"""Early-warning ML using historical completed students and pre-final assessment marks.

Predictions are decision-support scores, not calibrated probabilities or guarantees.
"""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "assessment_count", "subject_count", "overall_pct", "latest_pct",
    "recent_avg_pct", "trend_pct", "score_std", "below_50_count",
    "weak_subject_rate",
]
OUTCOMES = {"Pass", "Distinction", "Fail", "Withdrawn"}
MIN_LABELLED_STUDENTS = 30
MIN_PER_CLASS = 5


def _is_final_assessment(kind: str) -> bool:
    return "final" in (kind or "").strip().lower().replace("_", " ")


def extract_student_features(student: Any) -> dict[str, float] | None:
    """Build features from recorded non-final marks; final exam marks are excluded."""
    scores, subject_means = [], []
    weighted_obtained = weighted_maximum = 0.0
    for subject in (getattr(student, "subjects", []) or []):
        marks = [
            mark for mark in (getattr(subject, "assessments", []) or [])
            if not _is_final_assessment(getattr(mark, "assessment_type", ""))
            and float(getattr(mark, "maximum", 0) or 0) > 0
        ]
        marks.sort(key=lambda m: (getattr(m, "assessment_date", None), getattr(m, "id", 0) or 0))
        current = []
        for mark in marks:
            maximum, obtained = float(mark.maximum), float(mark.obtained)
            if maximum <= 0 or not np.isfinite(obtained / maximum):
                continue
            current.append(float(np.clip(obtained / maximum * 100, 0, 100)))
            weighted_obtained += obtained
            weighted_maximum += maximum
        scores.extend(current)
        if current:
            subject_means.append(float(np.mean(current)))
    if len(scores) < 2 or weighted_maximum <= 0:
        return None
    recent = scores[-3:]
    slope = float(np.polyfit(np.arange(len(scores), dtype=float), np.asarray(scores), 1)[0])
    return {
        "assessment_count": float(len(scores)),
        "subject_count": float(len(subject_means)),
        "overall_pct": float(weighted_obtained / weighted_maximum * 100),
        "latest_pct": float(scores[-1]),
        "recent_avg_pct": float(np.mean(recent)),
        "trend_pct": slope,
        "score_std": float(np.std(scores)),
        "below_50_count": float(sum(value < 50 for value in scores)),
        "weak_subject_rate": float(sum(value < 50 for value in subject_means) / len(subject_means)),
    }


def outcome_to_risk(outcome: str) -> int:
    value = (outcome or "").strip().title()
    if value not in OUTCOMES:
        raise ValueError(f"Outcome must be one of: {', '.join(sorted(OUTCOMES))}.")
    return int(value in {"Fail", "Withdrawn"})


def _pipeline(model: Any) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", model),
    ])


def train_early_warning_model(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compare classifiers on a stratified holdout, then refit the winner."""
    clean = []
    for row in rows:
        features, outcome = row.get("features") or {}, str(row.get("outcome", "")).title()
        if outcome not in OUTCOMES or not all(key in features for key in FEATURES):
            continue
        values = [float(features[key]) for key in FEATURES]
        if not np.isfinite(values).all():
            continue
        clean.append({**dict(zip(FEATURES, values)), "target": outcome_to_risk(outcome)})
    counts = pd.Series([row["target"] for row in clean]).value_counts().to_dict()
    class_counts = {"not_at_risk": int(counts.get(0, 0)), "at_risk": int(counts.get(1, 0))}
    if len(clean) < MIN_LABELLED_STUDENTS or any(counts.get(label, 0) < MIN_PER_CLASS for label in (0, 1)):
        return {
            "ready": False, "labelled_students": len(clean), "class_counts": class_counts,
            "minimum_required": MIN_LABELLED_STUDENTS,
            "message": (
                f"Need at least {MIN_LABELLED_STUDENTS} completed students with usable pre-final marks "
                f"and at least {MIN_PER_CLASS} examples in each outcome group. "
                "No ML prediction is produced until this evidence exists."
            ),
        }
    frame = pd.DataFrame(clean)
    X, y = frame[FEATURES], frame["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    candidates = {
        "Logistic Regression": _pipeline(
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
        ),
        "Random Forest": _pipeline(RandomForestClassifier(
            n_estimators=250, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )),
    }
    evaluations = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
        metrics = {
            "accuracy": float(accuracy_score(y_test, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, predicted)),
            "precision": float(precision_score(y_test, predicted, zero_division=0)),
            "recall": float(recall_score(y_test, predicted, zero_division=0)),
            "f1": float(f1_score(y_test, predicted, zero_division=0)),
        }
        if len(set(y_test)) == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities))
        evaluations[name] = metrics
    best_name = max(evaluations, key=lambda name: (
        evaluations[name]["f1"], evaluations[name]["balanced_accuracy"]
    ))
    best_model = candidates[best_name].fit(X, y)
    return {
        "ready": True, "model_name": best_name, "model": best_model,
        "metrics": evaluations, "selected_metrics": evaluations[best_name],
        "labelled_students": len(clean), "class_counts": class_counts, "features": FEATURES,
    }


def predict_student(model: Any, features: dict[str, float]) -> dict[str, Any]:
    """Return a model score plus descriptive (not causal) performance signals."""
    row = pd.DataFrame([{key: float(features[key]) for key in FEATURES}], columns=FEATURES)
    score = float(model.predict_proba(row)[0, list(model.classes_).index(1)])
    band = "High" if score >= 0.65 else "Moderate" if score >= 0.35 else "Low"
    signals = []
    if features["overall_pct"] < 60:
        signals.append("Pre-final weighted average is below 60%.")
    if features["trend_pct"] < -2:
        signals.append("Assessment scores show a declining trend.")
    if features["weak_subject_rate"] >= 0.5:
        signals.append("At least half of assessed subjects are currently below 50%.")
    if features["below_50_count"] >= 2:
        signals.append("Two or more recorded assessments are below 50%.")
    if not signals:
        signals.append("No strong low-mark or declining-trend signal is present in recorded marks.")
    action = {
        "High": "Arrange an individual teacher check-in and a targeted support plan this week.",
        "Moderate": "Monitor the next assessment and provide focused practice in weaker topics.",
        "Low": "Continue monitoring progress and maintain the current learning support.",
    }[band]
    return {"risk_score": score, "risk_band": band, "signals": signals, "recommended_action": action}
