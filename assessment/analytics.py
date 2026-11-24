"""Transparent marks-based assessment analysis; not an ML prediction model."""
from collections import defaultdict

def grade_for(percent):
    if percent >= 85: return "A"
    if percent >= 75: return "B"
    if percent >= 65: return "C"
    if percent >= 50: return "D"
    return "F"

def analyze_student(student):
    rows, total_obtained, total_maximum = [], 0.0, 0.0
    for subject in student.subjects:
        marks = sorted(subject.assessments, key=lambda x: (x.assessment_date, x.id))
        topics = sorted({topic.strip() for mark in marks for topic in getattr(mark, "topics", "").split(",") if topic.strip()})
        obtained = sum(m.obtained for m in marks)
        maximum = sum(m.maximum for m in marks)
        if maximum <= 0: continue
        pct = obtained / maximum * 100
        total_obtained += obtained; total_maximum += maximum
        trend = None
        if len(marks) >= 2:
            first = marks[0].obtained / marks[0].maximum * 100
            last = marks[-1].obtained / marks[-1].maximum * 100
            trend = round(last - first, 1)
        if pct < 50: level, reason = "High", f"Current average is {pct:.1f}%, below the 50% support threshold."
        elif pct < 65: level, reason = "Moderate", f"Current average is {pct:.1f}%, below the 65% monitoring threshold."
        else: level, reason = "Low", f"Current average is {pct:.1f}%, at or above the monitoring threshold."
        rows.append({"subject": subject.name, "teacher": subject.teacher_name, "assessments": len(marks), "obtained": obtained, "maximum": maximum, "percentage": round(pct, 1), "grade": grade_for(pct), "risk": level, "reason": reason, "trend": trend, "topics": topics, "marks": marks})
    overall = (total_obtained / total_maximum * 100) if total_maximum else None
    ranked = sorted(rows, key=lambda r: r["percentage"])
    return {"subjects": rows, "overall": round(overall, 1) if overall is not None else None,
            "grade": grade_for(overall) if overall is not None else "N/A",
            "strengths": [r["subject"] for r in ranked[-2:] if r["percentage"] >= 65][::-1],
            "weaknesses": [r["subject"] for r in ranked[:2] if r["percentage"] < 65],
            "alerts": [r for r in rows if r["risk"] != "Low"]}

def suggested_target(subject_row):
    """A transparent next-assessment target: at least 65%, or +5 points."""
    return round(min(100.0, max(65.0, subject_row["percentage"] + 5.0)), 1)

def suggested_actions(subject_row):
    p = subject_row["percentage"]
    if p < 50:
        return ["Arrange a teacher check-in this week and identify the two most difficult topics.", "Complete three focused 30-minute practice sessions each week.", "Review mistakes after each exercise and request feedback before the next assessment."]
    if p < 65:
        return ["Schedule two 30-minute revision sessions each week.", "Complete one timed practice task and review errors weekly.", "Ask the teacher to clarify topics where marks were lost."]
    return ["Maintain the current study routine and complete one extension task each week.", "Review feedback and target a 5 percentage-point improvement in the next assessment."]
