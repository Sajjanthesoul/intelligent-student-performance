"""PDF report generation for an individual student."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from .analytics import analyze_student, suggested_actions

def build_student_pdf(student):
    safe = lambda value: escape(str(value or ""))
    analysis = analyze_student(student)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Subtle", parent=styles["Normal"], textColor=colors.HexColor("#526174"), fontSize=8))
    story = [Paragraph("StudentIQ | Individual Student Assessment", styles["Title"]), Spacer(1, 5*mm),
             Paragraph(f"<b>Student:</b> {safe(student.name)} &nbsp;&nbsp; <b>ID:</b> {safe(student.student_id)}", styles["Normal"]),
             Paragraph(f"<b>Course:</b> {safe(student.course or '—')} &nbsp;&nbsp; <b>Semester:</b> {safe(student.semester or '—')}", styles["Normal"]),
             Paragraph(f"<b>Academic details:</b> {safe(student.academic_details or '—')}", styles["Normal"]), Spacer(1, 4*mm)]
    overall = f"{analysis['overall']:.1f}% ({analysis['grade']})" if analysis["overall"] is not None else "Not enough marks yet"
    story += [Paragraph(f"<b>Overall weighted performance:</b> {overall}", styles["Heading2"]), Spacer(1, 2*mm)]
    data = [["Subject", "Teacher", "Assessments", "Marks", "Percent", "Grade", "Risk"]]
    for r in analysis["subjects"]:
        data.append([r["subject"], r["teacher"] or "—", str(r["assessments"]), f"{r['obtained']:.1f}/{r['maximum']:.1f}", f"{r['percentage']:.1f}%", r["grade"], r["risk"]])
    table = Table(data, repeatRows=1, colWidths=[35*mm, 30*mm, 19*mm, 25*mm, 19*mm, 13*mm, 18*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#14243A")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#D5DCE5")),("FONTSIZE",(0,0),(-1,-1),7), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6FA")]),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story += [table, Spacer(1, 4*mm), Paragraph("Strengths and areas for attention", styles["Heading2"]), Paragraph("<b>Strengths:</b> " + (", ".join(safe(x) for x in analysis["strengths"]) or "Not yet established"), styles["Normal"]), Paragraph("<b>Needs attention:</b> " + (", ".join(safe(x) for x in analysis["weaknesses"]) or "No subject currently below the monitoring threshold"), styles["Normal"]), Spacer(1, 3*mm)]
    for r in analysis["subjects"]:
        if r["risk"] != "Low":
            story.append(Paragraph(f"<b>{safe(r['subject'])} — {r['risk']} risk:</b> {r['reason']}", styles["Normal"]))
            for action in suggested_actions(r): story.append(Paragraph("• " + action, styles["Subtle"]))
    story += [Spacer(1, 4*mm), Paragraph("Teacher feedback", styles["Heading2"])]
    for s in student.subjects:
        for f in sorted(s.feedback, key=lambda x:x.feedback_date, reverse=True):
            story.append(Paragraph(f"<b>{safe(s.name)} · {safe(f.teacher_name)} · {f.feedback_date}</b>: {safe(f.comment)}", styles["Normal"]))
    story += [Spacer(1, 3*mm), Paragraph("Improvement goals", styles["Heading2"])]
    for g in student.goals:
        story.append(Paragraph(f"<b>{safe(g.subject_name)}:</b> {safe(g.title)} — {g.progress}% complete; target {g.target_date}; {g.status}. {safe(g.recommendation)}", styles["Normal"]))
    story += [Spacer(1, 5*mm), Paragraph("This report summarizes recorded marks and teacher-entered information. Risk levels are transparent marks-based monitoring flags, not machine-learning predictions or guaranteed future outcomes.", styles["Subtle"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
