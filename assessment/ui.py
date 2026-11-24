"""Streamlit UI for student records, marks, feedback, analysis and goals."""
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import init_db, SessionLocal, Student, Subject, Assessment, Feedback, Goal, IS_PERSISTENT, validate_marks
from .analytics import analyze_student, suggested_actions, suggested_target
from .reports import build_student_pdf


def render_assessment():
    init_db()
    st.markdown("## Individual Student Assessment")
    st.caption("Manage student records and marks-based support. This module is separate from the OULAD research prediction model.")
    if not IS_PERSISTENT:
        st.warning("Local SQLite storage is active. On Streamlit Community Cloud, local files may be reset when the app restarts. Configure DATABASE_URL with a managed PostgreSQL database for durable hosted records.")
    with SessionLocal() as db:
        students = db.scalars(select(Student).order_by(Student.name)).all()
        tabs = st.tabs(["Students", "Subjects & marks", "Teachers & feedback", "Performance & goals", "Student report"])
        with tabs[0]:
            st.subheader("Register a student")
            with st.form("new_student", clear_on_submit=True):
                c1,c2 = st.columns(2)
                name = c1.text_input("Student name")
                sid = c2.text_input("Student ID")
                course = c1.text_input("Course")
                semester = c2.text_input("Semester")
                details = st.text_area("Academic details / notes")
                submitted = st.form_submit_button("Add student", type="primary")
                if submitted:
                    if not name.strip() or not sid.strip(): st.error("Student name and ID are required.")
                    else:
                        try:
                            db.add(Student(name=name.strip(),student_id=sid.strip(),course=course.strip(),semester=semester.strip(),academic_details=details.strip())); db.commit(); st.success("Student registered."); st.rerun()
                        except IntegrityError: db.rollback(); st.error("That student ID already exists.")
            if students:
                st.subheader("Search and manage students")
                query = st.text_input("Search by name, ID or course", key="student_search").lower()
                visible = [s for s in students if query in f"{s.name} {s.student_id} {s.course}".lower()]
                st.dataframe(pd.DataFrame([{"Name":s.name,"Student ID":s.student_id,"Course":s.course,"Semester":s.semester} for s in visible]),use_container_width=True,hide_index=True)
                selected = st.selectbox("Select student to edit or delete", students, format_func=lambda s:f"{s.name} · {s.student_id}", key="student_manage")
                with st.form("edit_student"):
                    n = st.text_input("Name",selected.name); c = st.text_input("Course",selected.course); sem = st.text_input("Semester",selected.semester); d = st.text_area("Academic details",selected.academic_details)
                    save = st.form_submit_button("Save student changes")
                    if save:
                        selected.name=n.strip(); selected.course=c.strip(); selected.semester=sem.strip(); selected.academic_details=d.strip(); db.commit(); st.success("Student updated."); st.rerun()
                if st.button("Delete student and all related assessment records", type="secondary"):
                    db.delete(selected); db.commit(); st.success("Student and related records deleted."); st.rerun()
            else: st.info("No students registered yet.")
        # Refresh after possible form submit/rerun.
        students = db.scalars(select(Student).order_by(Student.name)).all()
        if not students:
            for tab in tabs[1:]:
                with tab: st.info("Register a student to begin adding subjects, marks and feedback.")
            return
        with tabs[1]:
            student = st.selectbox("Student",students,format_func=lambda s:f"{s.name} · {s.student_id}",key="marks_student")
            st.subheader("Add a subject and assessment")
            with st.form("add_mark",clear_on_submit=True):
                subject_name=st.text_input("Subject name"); teacher=st.text_input("Assigned teacher"); kind=st.selectbox("Assessment type",["Quiz","Assignment","Midterm","Final exam","Project","Practical","Other"]); a,b=st.columns(2); obtained=a.number_input("Obtained marks",min_value=0.0,value=0.0,step=1.0); maximum=b.number_input("Maximum marks",min_value=0.01,value=100.0,step=1.0); dt=st.date_input("Assessment date",value=date.today()); add=st.form_submit_button("Save marks",type="primary")
                if add:
                    try:
                        obtained,maximum=validate_marks(obtained,maximum)
                        subject=db.scalar(select(Subject).where(Subject.student_id==student.id,Subject.name==subject_name.strip())) if subject_name.strip() else None
                        if not subject: 
                            if not subject_name.strip(): raise ValueError("Subject name is required.")
                            subject=Subject(student_id=student.id,name=subject_name.strip(),teacher_name=teacher.strip()); db.add(subject); db.flush()
                        elif teacher.strip(): subject.teacher_name=teacher.strip()
                        db.add(Assessment(subject_id=subject.id,assessment_type=kind,obtained=obtained,maximum=maximum,assessment_date=dt)); db.commit(); st.success(f"Marks saved ({obtained/maximum*100:.1f}%)."); st.rerun()
                    except ValueError as e: db.rollback(); st.error(str(e))
            subjects=db.scalars(select(Subject).where(Subject.student_id==student.id).order_by(Subject.name)).all()
            for sub in subjects:
                with st.expander(f"{sub.name} · {sub.teacher_name or 'Teacher not assigned'}"):
                    for mark in sorted(sub.assessments,key=lambda x:x.assessment_date,reverse=True):
                        c1,c2,c3=st.columns([2,2,1]); c1.write(f"{mark.assessment_type} · {mark.assessment_date}"); c2.write(f"{mark.obtained:g}/{mark.maximum:g} ({mark.obtained/mark.maximum*100:.1f}%)")
                        with st.form(f"edit_mark_{mark.id}"):
                            new_type=st.text_input("Assessment type",mark.assessment_type,key=f"type_{mark.id}")
                            x,y,z=st.columns(3)
                            new_obtained=x.number_input("Obtained",min_value=0.0,value=float(mark.obtained),key=f"obt_{mark.id}")
                            new_maximum=y.number_input("Maximum",min_value=0.01,value=float(mark.maximum),key=f"max_{mark.id}")
                            new_date=z.date_input("Date",value=mark.assessment_date,key=f"date_{mark.id}")
                            update_mark=st.form_submit_button("Update marks")
                            if update_mark:
                                try:
                                    mark.obtained,mark.maximum=validate_marks(new_obtained,new_maximum); mark.assessment_type=new_type.strip() or "Assessment"; mark.assessment_date=new_date; db.commit(); st.success("Marks updated."); st.rerun()
                                except ValueError as e: db.rollback(); st.error(str(e))
                        if c3.button("Delete",key=f"del_mark_{mark.id}"): db.delete(mark); db.commit(); st.rerun()
                    with st.form(f"edit_subject_{sub.id}"):
                        new_teacher=st.text_input("Assigned teacher",sub.teacher_name); rename=st.text_input("Subject name",sub.name); save=st.form_submit_button("Update subject")
                        if save: sub.teacher_name=new_teacher.strip(); sub.name=rename.strip(); db.commit(); st.success("Subject updated."); st.rerun()
                    if st.button("Delete subject and its marks",key=f"del_sub_{sub.id}"): db.delete(sub); db.commit(); st.rerun()
        with tabs[2]:
            student=st.selectbox("Student",students,format_func=lambda s:f"{s.name} · {s.student_id}",key="feedback_student")
            subjects=db.scalars(select(Subject).where(Subject.student_id==student.id).order_by(Subject.name)).all()
            if subjects:
                sub=st.selectbox("Subject",subjects,format_func=lambda s:s.name,key="feedback_subject")
                with st.form("teacher_feedback"):
                    teacher=st.text_input("Teacher name",sub.teacher_name); when=st.date_input("Feedback date",date.today()); comment=st.text_area("Feedback / comments"); save=st.form_submit_button("Save teacher feedback")
                    if save:
                        if not teacher.strip() or not comment.strip(): st.error("Teacher name and feedback are required.")
                        else: sub.teacher_name=teacher.strip(); db.add(Feedback(subject_id=sub.id,teacher_name=teacher.strip(),feedback_date=when,comment=comment.strip())); db.commit(); st.success("Feedback saved."); st.rerun()
                for f in sorted(sub.feedback,key=lambda x:x.feedback_date,reverse=True):
                    left,right=st.columns([5,1]); left.info(f"{f.feedback_date} · {f.teacher_name}: {f.comment}")
                    if right.button("Delete",key=f"delete_feedback_{f.id}"):
                        db.delete(f); db.commit(); st.rerun()
            else: st.info("Add a subject before recording teacher feedback.")
        with tabs[3]:
            student=st.selectbox("Student",students,format_func=lambda s:f"{s.name} · {s.student_id}",key="analysis_student")
            result=analyze_student(student)
            a,b,c=st.columns(3); a.metric("Overall weighted result",f"{result['overall']:.1f}%" if result["overall"] is not None else "N/A"); b.metric("Overall grade",result["grade"]); c.metric("Subjects monitored",len(result["subjects"]))
            if result["subjects"]:
                df=pd.DataFrame([{k:r[k] for k in ["subject","percentage","grade","risk","teacher"]} for r in result["subjects"]]); st.dataframe(df,use_container_width=True,hide_index=True)
                st.plotly_chart(px.bar(df,x="subject",y="percentage",color="risk",range_y=[0,100],title="Subject-wise performance (%)"),use_container_width=True)
                for r in result["subjects"]:
                    if r["risk"]!="Low":
                        st.warning(f"{r['subject']} · {r['risk']} monitoring: {r['reason']}")
                        st.write(f"Suggested next-assessment target: **{suggested_target(r):.1f}%**")
                        st.write("Suggested actions: " + " · ".join(suggested_actions(r)))
                if result["strengths"]: st.success("Current strengths: " + ", ".join(result["strengths"]))
                if result["weaknesses"]: st.info("Priority subjects: " + ", ".join(result["weaknesses"]))
                trend_rows=[{"Subject":r["subject"],"Date":m.assessment_date,"Percentage":m.obtained/m.maximum*100} for r in result["subjects"] for m in r["marks"]]
                if trend_rows: st.plotly_chart(px.line(pd.DataFrame(trend_rows),x="Date",y="Percentage",color="Subject",markers=True,title="Assessment progress over time"),use_container_width=True)
            st.subheader("Improvement goals")
            with st.form("new_goal"):
                subject_options=[s.name for s in student.subjects] or ["General"]
                goal_subject=st.selectbox("Subject",subject_options); title=st.text_input("Goal / target"); recommendation=st.text_area("Teacher recommendation or action plan"); due=st.date_input("Target date",date.today()+timedelta(days=30)); create=st.form_submit_button("Add improvement goal")
                if create:
                    if not title.strip(): st.error("Goal title is required.")
                    else: db.add(Goal(student_id=student.id,subject_name=goal_subject,title=title.strip(),recommendation=recommendation.strip(),target_date=due)); db.commit(); st.success("Goal added."); st.rerun()
            for goal in student.goals:
                with st.container(border=True):
                    st.write(f"**{goal.subject_name}:** {goal.title} · target {goal.target_date}")
                    progress=st.slider("Progress (%)",0,100,goal.progress,key=f"goal_progress_{goal.id}")
                    if st.button("Update goal progress",key=f"save_goal_{goal.id}"): goal.progress=progress; goal.status="Completed" if progress==100 else "In progress"; db.commit(); st.rerun()
                    if goal.recommendation: st.caption(goal.recommendation)
        with tabs[4]:
            student=st.selectbox("Student",students,format_func=lambda s:f"{s.name} · {s.student_id}",key="report_student")
            result=analyze_student(student)
            st.subheader(student.name)
            st.write(f"**Student ID:** {student.student_id} · **Course:** {student.course or '—'} · **Semester:** {student.semester or '—'}")
            st.metric("Overall weighted performance",f"{result['overall']:.1f}%" if result["overall"] is not None else "Not enough marks")
            st.dataframe(pd.DataFrame([{ "Subject":r["subject"],"Marks":f"{r['obtained']:.1f}/{r['maximum']:.1f}","Percentage":r["percentage"],"Grade":r["grade"],"Risk":r["risk"]} for r in result["subjects"]]),use_container_width=True,hide_index=True)
            st.download_button("Download individual student PDF",data=build_student_pdf(student),file_name=f"StudentIQ_{student.student_id}_report.pdf",mime="application/pdf",type="primary")
            st.caption("PDF includes recorded marks, grades, strengths, weaknesses, monitoring alerts, teacher feedback and improvement goals.")
