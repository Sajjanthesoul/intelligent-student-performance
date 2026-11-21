import json
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.functions import vector_to_array
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, Imputer, VectorAssembler
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier, RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from config import ARTIFACTS_DIR, RANDOM_SEED, TEST_FRACTION

NUMERIC = [
    "num_of_prev_attempts", "studied_credits", "date_registration",
    "early_total_clicks", "early_active_days", "early_unique_resources",
    "early_vle_records", "early_assessment_avg", "early_assessment_min",
    "early_assessment_max", "early_assessment_count"
]
CATEGORICAL = [
    "code_module", "code_presentation", "gender", "region",
    "highest_education", "imd_band", "age_band", "disability"
]

def main():
    spark = (SparkSession.builder.appName("OULAD-Model-Comparison")
             .master("local[*]").config("spark.sql.shuffle.partitions", "8")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    path = ARTIFACTS_DIR / "student_features.parquet"
    if not path.exists():
        raise FileNotFoundError("Run python -m src.build_features first.")

    df = spark.read.parquet(str(path)).filter("final_result IS NOT NULL")

    # Convert numeric features to double for Spark ML
    for c in NUMERIC:
        if c in df.columns:
            df = df.withColumn(c, F.col(c).cast("double"))

    nums = [c for c in NUMERIC if c in df.columns]
    cats = [c for c in CATEGORICAL if c in df.columns]
    label = StringIndexer(inputCol="final_result", outputCol="label",
                          handleInvalid="keep")
    stages = [label]
    for c in cats:
        stages.append(StringIndexer(inputCol=c, outputCol=c+"_idx",
                                    handleInvalid="keep"))
    if cats:
        stages.append(OneHotEncoder(
            inputCols=[c+"_idx" for c in cats],
            outputCols=[c+"_ohe" for c in cats], handleInvalid="keep"))
    if nums:
        stages.append(Imputer(inputCols=nums,
            outputCols=[c+"_imp" for c in nums], strategy="median"))
    inputs = [c+"_imp" for c in nums] + [c+"_ohe" for c in cats]
    stages.append(VectorAssembler(inputCols=inputs, outputCol="features",
                                  handleInvalid="keep"))

    train, test = df.randomSplit([1-TEST_FRACTION, TEST_FRACTION],
                                 seed=RANDOM_SEED)
    models = {
        "LogisticRegression": LogisticRegression(
            labelCol="label", featuresCol="features", maxIter=80, regParam=0.05),
        "DecisionTree": DecisionTreeClassifier(
            labelCol="label", featuresCol="features", maxDepth=8, seed=RANDOM_SEED),
        "RandomForest": RandomForestClassifier(
            labelCol="label", featuresCol="features", numTrees=120,
            maxDepth=10, seed=RANDOM_SEED)
    }
    f1_eval = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="f1")
    acc_eval = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy")

    results, best_name, best_f1, best_pipeline = {}, None, -1, None
    for name, model in models.items():
        fitted = Pipeline(stages=stages + [model]).fit(train)
        pred = fitted.transform(test).cache()
        f1, acc = float(f1_eval.evaluate(pred)), float(acc_eval.evaluate(pred))
        results[name] = {"weighted_f1": f1, "accuracy": acc}
        print(f"{name}: weighted F1={f1:.4f}; accuracy={acc:.4f}")
        if f1 > best_f1:
            best_name, best_f1, best_pipeline = name, f1, fitted
        pred.unpersist()

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    with open(ARTIFACTS_DIR / "model_metrics.json", "w") as f:
        json.dump({"task": "four-class classification",
                   "target": "final_result", "best_model": best_name,
                   "models": results}, f, indent=2)
    best_pipeline.write().overwrite().save(str(ARTIFACTS_DIR / "best_model"))
    (best_pipeline.transform(test)
    .select(
        "final_result",
        "prediction",
        F.to_json(vector_to_array("probability")).alias("probability")
    )
    .write.mode("overwrite").option("header", True)
    .csv(str(ARTIFACTS_DIR / "test_predictions_csv")))
    print("Saved model, metrics, and test predictions in artifacts/.")
    spark.stop()

if __name__ == "__main__":
    main()
