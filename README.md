# Intelligent Student Performance Prediction and Early Warning System
## Using Big Data Analytics and Explainable Machine Learning

A runnable starter project using OULAD, Apache Spark/PySpark, machine learning, and Streamlit. It contains code scaffolding, not precomputed experimental results.

### Dataset
Download OULAD from:
- https://analyse.kmi.open.ac.uk/open_dataset/
- https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset

Extract these seven CSVs into `data/raw/`: `studentInfo.csv`, `studentRegistration.csv`, `studentAssessment.csv`, `assessments.csv`, `studentVle.csv`, `vle.csv`, and `courses.csv`.

### Research target and leakage prevention
OULAD's `final_result` is categorical. This starter therefore treats the primary task as four-class classification (Distinction, Pass, Fail, Withdrawn), not regression. The early-warning mapping is High risk = Fail/Withdrawn, Medium risk = Pass, Low risk = Distinction; this is a configurable research definition, not a universal standard.

Features use only VLE activity and assessment submissions available by day 60 (configurable in `config.py`). `final_result` is never used as an input feature. For stronger conference evidence, evaluate several early cutoffs and hold out entire course presentations to test generalization.

### Setup
Python 3.10/3.11 and Java are recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Place OULAD CSV files in `data/raw/`, then run:

```bash
python -m src.build_features
python -m src.train
streamlit run app.py
```

### Project structure
- `src/build_features.py`: Spark ingestion and early-course feature engineering.
- `src/train.py`: preprocessing and model comparison.
- `src/explain.py`: explainability implementation roadmap.
- `app.py`: Streamlit experiment dashboard.
- `artifacts/`: generated outputs.

### Conference experiments to complete
1. Compare Logistic Regression, Decision Tree, and Random Forest using accuracy, macro-F1, weighted-F1, and per-class precision/recall.
2. Repeat prediction at days 30, 60, and 90.
3. Add global feature importance and sampled SHAP explanations.
4. Benchmark Spark processing time across dataset sizes and configurations; report hardware, partitions, caching, and repetitions.
5. Use a course-presentation holdout split as a generalization experiment.
6. Examine class imbalance and responsible-use/fairness considerations.

### Data ethics
OULAD is de-identified, but educational data remains sensitive. Use data minimization and aggregate reporting. Predictions are decision-support signals, not definitive judgments or automatic grounds for punitive action.

### Dataset citation
Kuzilek, J., Hlosta, M., & Zdrahal, Z. (2017). Open University Learning Analytics Dataset. *Scientific Data*, 4, 170171. https://doi.org/10.1038/sdata.2017.171
