from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from assessment.db import Base, Student, Subject, Assessment, validate_marks
from assessment.analytics import analyze_student, grade_for, suggested_actions, suggested_target


def test_validate_marks_accepts_valid_values():
    assert validate_marks(72, 100) == (72.0, 100.0)


@pytest.mark.parametrize("obtained,maximum", [(-1, 100), (101, 100), (10, 0), ("x", 100)])
def test_validate_marks_rejects_invalid_values(obtained, maximum):
    with pytest.raises(ValueError):
        validate_marks(obtained, maximum)


def test_grade_boundaries():
    assert [grade_for(x) for x in (90, 80, 70, 55, 49)] == ["A", "B", "C", "D", "F"]


def test_analysis_is_weighted_and_risk_explained():
    subject_a = SimpleNamespace(name="Mathematics", teacher_name="Teacher A", assessments=[
        SimpleNamespace(id=1, assessment_date=date(2026, 1, 1), obtained=20, maximum=40),
        SimpleNamespace(id=2, assessment_date=date(2026, 2, 1), obtained=30, maximum=60),
    ])
    subject_b = SimpleNamespace(name="Science", teacher_name="Teacher B", assessments=[
        SimpleNamespace(id=3, assessment_date=date(2026, 2, 1), obtained=40, maximum=100),
    ])
    result = analyze_student(SimpleNamespace(subjects=[subject_a, subject_b]))
    assert result["overall"] == 45.0
    assert result["subjects"][1]["risk"] == "High"
    assert "40.0%" in result["subjects"][1]["reason"]
    assert result["subjects"][0]["trend"] == 0.0
    assert result["weaknesses"] == ["Science", "Mathematics"] or set(result["weaknesses"]) == {"Science", "Mathematics"}
    assert suggested_actions(result["subjects"][0])
    assert suggested_target(result["subjects"][0]) == 65.0


def test_database_persistence_and_cascade_delete(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'assessment-test.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        student = Student(student_id="TEST-001", name="Sample Student", course="Computing", semester="1")
        session.add(student); session.flush()
        subject = Subject(student_id=student.id, name="Programming", teacher_name="Teacher")
        session.add(subject); session.flush()
        session.add(Assessment(subject_id=subject.id, assessment_type="Quiz", obtained=8, maximum=10, assessment_date=date(2026, 1, 1)))
        session.commit()
        student_id = student.id
    with Session() as session:
        stored = session.scalar(select(Student).where(Student.student_id == "TEST-001"))
        assert stored is not None and stored.name == "Sample Student"
        assert stored.subjects[0].assessments[0].obtained == 8
        session.delete(stored); session.commit()
        assert session.scalar(select(Student).where(Student.id == student_id)) is None
    engine.dispose()


def test_pdf_report_is_generated():
    from assessment.reports import build_student_pdf
    subject = SimpleNamespace(name="Mathematics", teacher_name="Teacher", assessments=[
        SimpleNamespace(id=1, assessment_date=date(2026, 3, 1), obtained=72, maximum=100, assessment_type="Midterm")
    ], feedback=[],)
    student = SimpleNamespace(name="Sample Learner", student_id="SAMPLE-02", course="Computing", semester="2", academic_details="Anonymized fixture", subjects=[subject], goals=[])
    payload = build_student_pdf(student)
    assert payload.startswith(b"%PDF")
    assert len(payload) > 500
