from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from assessment.prediction import FEATURES, extract_student_features, outcome_to_risk, predict_student, train_early_warning_model


def make_student(scores, include_final=True):
    marks = [
        SimpleNamespace(id=i + 1, assessment_type="Quiz", obtained=score, maximum=100,
                        assessment_date=date(2026, 1, 1) + timedelta(days=i * 7))
        for i, score in enumerate(scores)
    ]
    if include_final:
        marks.append(SimpleNamespace(id=99, assessment_type="Final exam", obtained=0,
                                     maximum=100, assessment_date=date(2026, 6, 1)))
    return SimpleNamespace(subjects=[SimpleNamespace(name="Math", assessments=marks)])


def test_features_exclude_final_exam_marks():
    features = extract_student_features(make_student([70, 60, 50]))
    assert features["assessment_count"] == 3
    assert features["latest_pct"] == 50
    assert features["overall_pct"] == pytest.approx(60)
    assert set(features) == set(FEATURES)


def test_features_require_two_non_final_assessments():
    assert extract_student_features(make_student([80])) is None


def test_outcome_mapping():
    assert outcome_to_risk("Fail") == 1
    assert outcome_to_risk("Withdrawn") == 1
    assert outcome_to_risk("Pass") == 0
    assert outcome_to_risk("Distinction") == 0
    with pytest.raises(ValueError):
        outcome_to_risk("Unknown")


def test_model_refuses_insufficient_or_single_class_data():
    rows = [{"features": {key: 50.0 for key in FEATURES}, "outcome": "Pass"} for _ in range(40)]
    result = train_early_warning_model(rows)
    assert result["ready"] is False
    assert "No ML prediction" in result["message"]


def test_model_compares_models_and_predicts():
    rows = []
    for i in range(60):
        at_risk = i % 2 == 0
        base = 35 if at_risk else 78
        features = {
            "assessment_count": 4, "subject_count": 2,
            "overall_pct": base + (i % 5),
            "latest_pct": base + (i % 5) - (8 if at_risk else -2),
            "recent_avg_pct": base + (i % 5),
            "trend_pct": -4 if at_risk else 2, "score_std": 8,
            "below_50_count": 3 if at_risk else 0,
            "weak_subject_rate": 1.0 if at_risk else 0.0,
        }
        rows.append({"features": features, "outcome": "Fail" if at_risk else "Pass"})
    result = train_early_warning_model(rows)
    assert result["ready"] is True
    assert set(result["metrics"]) == {"Logistic Regression", "Random Forest"}
    assert "f1" in result["selected_metrics"]
    prediction = predict_student(result["model"], rows[0]["features"])
    assert 0 <= prediction["risk_score"] <= 1
    assert prediction["risk_band"] in {"High", "Moderate", "Low"}
    assert prediction["signals"]
