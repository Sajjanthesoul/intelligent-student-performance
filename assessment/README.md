# Individual assessment storage and operations

The Individual assessment workspace is integrated into the root Streamlit application. Existing OULAD research pages and model artifacts remain separate.

## Database configuration

For local development, install requirements and run the app. Without a database URL the module creates a SQLite database at `.studentiq/studentiq.db`. This directory is ignored by Git.

For hosted use, configure a managed PostgreSQL database and set `DATABASE_URL` as a Streamlit secret or environment variable. Also set `ASSESSMENT_ACCESS_PASSWORD` to a strong, unique password before the module can be opened. The module is locked if this secret is absent. Example secrets (never commit credentials):

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
ASSESSMENT_ACCESS_PASSWORD = "replace-with-a-long-random-password"
```

The application normalizes PostgreSQL URLs for psycopg 3. Table initialization uses SQLAlchemy `create_all`, which creates missing tables but does not perform destructive schema migrations. For future schema changes, introduce versioned Alembic migrations before changing existing columns or constraints.

**Access-control limitation:** The built-in gate is a single shared password, not per-user authentication or role-based authorization. For real student records, restrict the Streamlit app to trusted users and add institutional identity/role controls before broad deployment.

**Persistence warning:** SQLite is suitable for local development only. Files on Streamlit Community Cloud are not a durable database. A managed PostgreSQL URL must be configured before using this feature for real student records in production.

## Assessment rules

- Percentages are calculated from total obtained marks divided by total maximum marks for each subject and overall.
- Grade bands: A ≥ 85, B ≥ 75, C ≥ 65, D ≥ 50, F < 50.
- Marks-based monitoring: High < 50%, Moderate 50–64.9%, Low ≥ 65%.
- These are configurable educational heuristics, not official institutional grading rules or machine-learning predictions.
- Individual marks are never passed into the OULAD prediction model.

## Tests

Run `pytest -q` to exercise mark validation, grade boundaries, weighted analysis, risk explanations and database persistence/cascade deletion. Use anonymized test fixtures only.


## Machine-learning early-warning module

The **Early-warning ML** tab is separate from the OULAD research dashboard and from the marks-based grade calculator.

- It automatically derives features from recorded assessments: weighted pre-final average, latest and recent scores, trend, score variability, low-mark count, subject count, and share of weak subjects.
- Final-exam assessment rows are excluded from both training features and current-student predictions.
- Teachers record the verified final result (Pass, Distinction, Fail, Withdrawn) for completed historical students. Fail/Withdrawn form the at-risk class; Pass/Distinction form the other class.
- The model compares Logistic Regression and Random Forest using a stratified holdout and reports accuracy, balanced accuracy, precision, recall, F1 and ROC-AUC where calculable.
- It requires at least 30 labelled students and at least five examples in each class. Until then, it explicitly reports insufficient evidence and does not produce an ML prediction. Never substitute synthetic data or the OULAD model's outputs for institution-specific labels.
- Current students with at least two non-final assessments receive a risk band, a non-calibrated model score, descriptive mark signals and a suggested teacher action.
- Risk scores are not calibrated probabilities, guarantees, causal explanations or automatic decisions. Validate the model on local cohorts, monitor class imbalance and fairness, and use teacher judgment.
