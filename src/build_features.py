from pyspark.sql import SparkSession, functions as F
from config import RAW_DATA_DIR, ARTIFACTS_DIR, EARLY_CUTOFF_DAY, REQUIRED_FILES

def main():
    missing = [f for f in REQUIRED_FILES if not (RAW_DATA_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing OULAD CSVs in data/raw/: " + ", ".join(missing)
        )

    spark = (SparkSession.builder.appName("OULAD-Early-Warning")
             .master("local[*]")
             .config("spark.sql.shuffle.partitions", "8").getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    def read(name):
        return (spark.read.option("header", True).option("inferSchema", True)
                .csv(str(RAW_DATA_DIR / name)))

    info = read("studentInfo.csv")
    reg = read("studentRegistration.csv")
    svle = read("studentVle.csv")
    sa = read("studentAssessment.csv")
    assessments = read("assessments.csv")
    keys = ["code_module", "code_presentation", "id_student"]

    vle_early = (svle.filter(F.col("date") <= EARLY_CUTOFF_DAY)
        .groupBy(*keys).agg(
            F.sum("sum_click").alias("early_total_clicks"),
            F.countDistinct("date").alias("early_active_days"),
            F.countDistinct("id_site").alias("early_unique_resources"),
            F.count("*").alias("early_vle_records")))

    # Include only assessments whose scheduled date and submission date are
    # both within the early window, preventing later assessment scores leaking.
    assessment_early = (sa.join(
        assessments.select("id_assessment", "code_module", "code_presentation", "date"),
        "id_assessment", "inner")
        .filter((F.col("date_submitted") <= EARLY_CUTOFF_DAY) &
                (F.col("date") <= EARLY_CUTOFF_DAY))
        .groupBy("code_module", "code_presentation", "id_student")
        .agg(F.avg("score").alias("early_assessment_avg"),
             F.min("score").alias("early_assessment_min"),
             F.max("score").alias("early_assessment_max"),
             F.count("score").alias("early_assessment_count")))

    reg_keep = [c for c in keys + ["date_registration"] if c in reg.columns]
    df = (info.join(reg.select(*reg_keep), keys, "left")
        .join(vle_early, keys, "left")
        .join(assessment_early, keys, "left"))

    zero_cols = ["early_total_clicks", "early_active_days",
                 "early_unique_resources", "early_vle_records",
                 "early_assessment_count"]
    for c in zero_cols:
        df = df.withColumn(c, F.coalesce(F.col(c), F.lit(0)))
    df = df.filter(F.col("final_result").isNotNull()).drop("id_student")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / "student_features.parquet"
    df.write.mode("overwrite").parquet(str(out))
    print(f"Saved {df.count()} student-course rows to {out}")
    df.groupBy("final_result").count().orderBy("final_result").show()
    spark.stop()

if __name__ == "__main__":
    main()
