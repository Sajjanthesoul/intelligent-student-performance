from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
EARLY_CUTOFF_DAY = 60
RANDOM_SEED = 42
TEST_FRACTION = 0.20
REQUIRED_FILES = [
    "studentInfo.csv", "studentRegistration.csv", "studentAssessment.csv",
    "assessments.csv", "studentVle.csv", "vle.csv", "courses.csv"
]
