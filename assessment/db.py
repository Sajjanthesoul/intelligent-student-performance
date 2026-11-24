"""Persistent assessment storage. PostgreSQL is recommended for hosted deployments."""
import os
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine, String, Integer, Float, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = "assessment_students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    course: Mapped[str] = mapped_column(String(160), default="")
    semester: Mapped[str] = mapped_column(String(80), default="")
    academic_details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[date] = mapped_column(Date, default=date.today)
    subjects: Mapped[list["Subject"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="student", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "assessment_subjects"
    __table_args__ = (UniqueConstraint("student_id", "name", name="uq_student_subject"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("assessment_students.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    teacher_name: Mapped[str] = mapped_column(String(160), default="")
    student: Mapped[Student] = relationship(back_populates="subjects")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="subject", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessment_marks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("assessment_subjects.id", ondelete="CASCADE"), index=True)
    assessment_type: Mapped[str] = mapped_column(String(80))
    obtained: Mapped[float] = mapped_column(Float)
    maximum: Mapped[float] = mapped_column(Float)
    assessment_date: Mapped[date] = mapped_column(Date)
    topics: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[Subject] = relationship(back_populates="assessments")

class Feedback(Base):
    __tablename__ = "assessment_feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("assessment_subjects.id", ondelete="CASCADE"), index=True)
    teacher_name: Mapped[str] = mapped_column(String(160))
    comment: Mapped[str] = mapped_column(Text)
    feedback_date: Mapped[date] = mapped_column(Date, default=date.today)
    subject: Mapped[Subject] = relationship(back_populates="feedback")

class Goal(Base):
    __tablename__ = "assessment_goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("assessment_students.id", ondelete="CASCADE"), index=True)
    subject_name: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(240))
    recommendation: Mapped[str] = mapped_column(Text, default="")
    target_date: Mapped[date] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="In progress")
    student: Mapped[Student] = relationship(back_populates="goals")


class PredictionOutcome(Base):
    """Historical completed-course outcome used only as an ML training label."""
    __tablename__ = "assessment_prediction_outcomes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_students.id", ondelete="CASCADE"),
        unique=True, index=True
    )
    final_result: Mapped[str] = mapped_column(String(40))
    recorded_at: Mapped[date] = mapped_column(Date, default=date.today)


def database_url():
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        try:
            import streamlit as st
            value = str(st.secrets.get("DATABASE_URL", "")).strip()
        except Exception:
            value = ""
    if value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql+psycopg://", 1)
    elif value.startswith("postgresql://") and "+psycopg" not in value:
        value = value.replace("postgresql://", "postgresql+psycopg://", 1)
    if value:
        return value, True
    local = Path(os.getenv("STUDENTIQ_DATA_DIR", ".studentiq"))
    local.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + str((local / "studentiq.db").resolve()).replace("\\", "/"), False

_URL, IS_PERSISTENT = database_url()
_engine_options = {"pool_pre_ping": True}
if _URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    """Create missing tables; additive schema changes should use versioned migrations."""
    Base.metadata.create_all(engine)

def validate_marks(obtained, maximum):
    try:
        obtained, maximum = float(obtained), float(maximum)
    except (TypeError, ValueError):
        raise ValueError("Marks must be numeric.")
    if maximum <= 0:
        raise ValueError("Maximum marks must be greater than zero.")
    if obtained < 0 or obtained > maximum:
        raise ValueError("Obtained marks must be between zero and maximum marks.")
    return obtained, maximum
