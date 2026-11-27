import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

from auth import authenticate_user, get_all_users_df, register_user
from database import (
    add_student,
    bulk_import_csv,
    delete_student,
    get_alert_logs_df,
    get_all_students_df,
    get_student_by_roll,
    init_db,
    update_student,
)
from ml_engine import predict_student, train_and_evaluate_models
from notifier import send_email_alert, send_sms_alert
from pdf_report import generate_student_pdf

st.set_page_config(
    page_title="Smart SMS | Academic Intelligence Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# Custom Polished UI Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
        padding: 18px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .metric-title { font-size: 0.85rem; opacity: 0.85; margin-bottom: 4px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; }
    .risk-high { background-color: #fed7d7; color: #9b2c2c; padding: 6px 12px; border-radius: 8px; font-weight: 600; }
    .risk-mod { background-color: #fefcbf; color: #975a16; padding: 6px 12px; border-radius: 8px; font-weight: 600; }
    .risk-safe { background-color: #c6f6d5; color: #22543d; padding: 6px 12px; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

COURSES = ["CSE", "ECE", "IT", "ME", "CE"]


@st.cache_resource(ttl=300)
def get_ml_bundle(row_count: int):
    df = get_all_students_df()
    return train_and_evaluate_models(df)


def render_auth_page():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("## 🎓 Smart Student Management System")
        st.caption("Cloud-Hosted Academic Intelligence & Performance Prediction Platform")

        tab_login, tab_reg = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="e.g., admin, teacher, or student")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
                if submitted:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

            with st.expander("🔑 Demo Credentials (Role-Based Access)"):
                st.markdown("""
                - **Admin:** `admin` / `admin123` (Full Access + User Management)
                - **Teacher:** `teacher` / `teacher123` (Records, Analytics, PDF & Alerts)
                - **Student:** `student` / `student123` (Personal Profile, AI Simulator & Report Card)
                """)

        with tab_reg:
            with st.form("register_form"):
                r_user = st.text_input("Choose Username")
                r_email = st.text_input("Email Address")
                r_pass = st.text_input("Password", type="password")
                r_role = st.selectbox("Account Role", ["student", "teacher"])
                r_roll = st.text_input("Student Roll No (Required if Student)", placeholder="e.g., 2304501")
                reg_submit = st.form_submit_button("Register Account", use_container_width=True)
                if reg_submit:
                    if not r_user or not r_email or not r_pass:
                        st.warning("Please fill all required fields.")
                    else:
                        ok, msg = register_user(r_user, r_email, r_pass, r_role, r_roll or None)
                        if ok:
                            st.success(msg + " You can now Sign In.")
                        else:
                            st.error(msg)


def render_kpi_cards(df: pd.DataFrame):
    total = len(df)
    avg_gpa = df["grade"].mean() if total else 0.0
    avg_att = df["attendance"].mean() if total else 0.0
    at_risk = int(((df["attendance"] < 75.0) | (df["grade"] < 6.5)).sum()) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-title">Total Students</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-title">Average CGPA</div><div class="metric-value">{avg_gpa:.2f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-title">Avg Attendance</div><div class="metric-value">{avg_att:.1f}%</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-title">At-Risk Students</div><div class="metric-value">{at_risk}</div></div>', unsafe_allow_html=True)


def render_dashboard(df: pd.DataFrame):
    st.title("📊 Academic Overview Dashboard")
    render_kpi_cards(df)
    st.markdown("---")

    f1, f2, f3 = st.columns([2, 1, 1])
    search = f1.text_input("🔍 Live Search (Name, Roll No, or Email)", placeholder="Type to filter...")
    course_filter = f2.selectbox("Filter by Course", ["All"] + COURSES)
    sem_filter = f3.selectbox("Filter by Semester", ["All"] + sorted(df["semester"].unique().tolist()) if not df.empty else ["All"])

    filtered = df.copy()
    if search:
        mask = (
            filtered["name"].str.contains(search, case=False, na=False)
            | filtered["roll_no"].str.contains(search, case=False, na=False)
            | filtered["email"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if course_filter != "All":
        filtered = filtered[filtered["course"] == course_filter]
    if sem_filter != "All":
        filtered = filtered[filtered["semester"] == sem_filter]

    st.subheader(f"Student Directory ({len(filtered)} Records)")
    st.dataframe(filtered.drop(columns=["id"], errors="ignore"), use_container_width=True, hide_index=True)

    csv_bytes = filtered.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export Filtered Data as CSV", data=csv_bytes, file_name="students_export.csv", mime="text/csv")


def render_manage_students(df: pd.DataFrame, role: str):
    st.title("🗂️ Manage Student Records")
    tabs = ["➕ Add Student", "✏️ Update Student", "📤 CSV Bulk Import"]
    if role == "admin":
        tabs.append("🗑️ Delete Student")

    tab_objs = st.tabs(tabs)

    # Add Student
    with tab_objs[0]:
        with st.form("add_student_form"):
            c1, c2, c3 = st.columns(3)
            roll_no = c1.text_input("Roll Number*")
            name = c2.text_input("Full Name*")
            age = c3.number_input("Age", 17, 30, 20)

            c4, c5, c6 = st.columns(3)
            email = c4.text_input("Email*")
            phone = c5.text_input("Phone (+91...)*", value="+91")
            course = c6.selectbox("Course", COURSES)

            c7, c8, c9, c10 = st.columns(4)
            semester = c7.number_input("Semester", 1, 8, 6)
            prev_gpa = c8.number_input("Previous GPA", 0.0, 10.0, 7.8, step=0.1)
            internal_marks = c9.number_input("Internal Marks (/40)", 0.0, 40.0, 30.0, step=0.5)
            attendance = c10.number_input("Attendance (%)", 0.0, 100.0, 82.0, step=0.5)
            grade = st.number_input("Current CGPA / Grade", 0.0, 10.0, 8.0, step=0.1)

            if st.form_submit_button("Save Student Record", type="primary"):
                if not roll_no or not name or not email:
                    st.error("Roll Number, Name, and Email are required.")
                else:
                    ok, msg = add_student({
                        "roll_no": roll_no, "name": name, "age": age, "email": email, "phone": phone,
                        "course": course, "semester": semester, "prev_gpa": prev_gpa,
                        "internal_marks": internal_marks, "attendance": attendance, "grade": grade,
                    })
                    if ok:
                        st.success(msg)
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error(msg)

    # Update Student
    with tab_objs[1]:
        if df.empty:
            st.info("No students found.")
        else:
            options = [f"{r.roll_no} - {r.name}" for _, r in df.iterrows()]
            selected = st.selectbox("Select Student to Update", options)
            sel_roll = selected.split(" - ")[0]
            stu = get_student_by_roll(sel_roll)

            with st.form("update_student_form"):
                c1, c2, c3 = st.columns(3)
                u_name = c1.text_input("Name", value=stu["name"])
                u_email = c2.text_input("Email", value=stu["email"])
                u_phone = c3.text_input("Phone", value=stu["phone"])

                c4, c5, c6, c7 = st.columns(4)
                u_course = c4.selectbox("Course", COURSES, index=COURSES.index(stu["course"]) if stu["course"] in COURSES else 0)
                u_sem = c5.number_input("Semester", 1, 8, int(stu["semester"]))
                u_att = c6.number_input("Attendance (%)", 0.0, 100.0, float(stu["attendance"]), step=0.5)
                u_grade = c7.number_input("Current CGPA", 0.0, 10.0, float(stu["grade"]), step=0.1)

                u_internal = st.number_input("Internal Marks (/40)", 0.0, 40.0, float(stu["internal_marks"]), step=0.5)
                auto_notify = st.checkbox("🔔 Automatically send Email & SMS alert if Attendance < 75%", value=True)

                if st.form_submit_button("Update Record", type="primary"):
                    updates = {
                        "name": u_name, "email": u_email, "phone": u_phone,
                        "course": u_course, "semester": int(u_sem),
                        "attendance": float(u_att), "grade": float(u_grade), "internal_marks": float(u_internal),
                    }
                    ok, msg = update_student(sel_roll, updates)
                    if ok:
                        st.success(msg)
                        if auto_notify and u_att < 75.0:
                            updated_stu = {**stu, **updates}
                            alert_text = (
                                f"Alert for {u_name} (Roll No: {sel_roll}): Your attendance has dropped to {u_att:.1f}%, "
                                f"which is below the 75% mandatory requirement. Current CGPA: {u_grade:.2f}."
                            )
                            _, e_msg = send_email_alert(updated_stu, "Low Attendance Warning - Smart SMS", alert_text)
                            _, s_msg = send_sms_alert(updated_stu, alert_text)
                            st.warning(f"Low Attendance Triggered!\n- {e_msg}\n- {s_msg}")
                        st.cache_resource.clear()
                    else:
                        st.error(msg)

    # CSV Bulk Import
    with tab_objs[2]:
        st.info("Upload `new_batch_import.csv` (or any CSV with matching student columns) to bulk-import records directly into Supabase.")
        uploaded = st.file_uploader("Choose CSV File", type=["csv"])
        if uploaded is not None:
            preview_df = pd.read_csv(uploaded)
            st.dataframe(preview_df.head(10), use_container_width=True)
            if st.button("🚀 Import into Cloud Database", type="primary"):
                ins, skp, msg = bulk_import_csv(preview_df)
                st.success(f"{msg} Inserted: {ins} new students | Skipped duplicates: {skp}")
                st.cache_resource.clear()

    # Delete Student (Admin only)
    if role == "admin":
        with tab_objs[3]:
            st.warning("⚠️ Admin-Only Zone: Deleting a student removes their record permanently from Cloud PostgreSQL.")
            if not df.empty:
                del_opt = st.selectbox("Select Student to Delete", [f"{r.roll_no} - {r.name}" for _, r in df.iterrows()], key="del_box")
                del_roll = del_opt.split(" - ")[0]
                if st.button("Permanently Delete Student", type="primary"):
                    ok, msg = delete_student(del_roll)
                    if ok:
                        st.success(msg)
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error(msg)


def render_analytics_and_ml(df: pd.DataFrame, bundle):
    st.title("🤖 Interactive Analytics & Machine Learning Lab")

    tab_viz, tab_ml, tab_sim = st.tabs(["📈 Interactive Visuals", "🏆 Model Benchmarks (XAI)", "🎛️ Live What-If Simulator"])

    with tab_viz:
        col1, col2 = st.columns(2)
        with col1:
            course_counts = df["course"].value_counts().reset_index()
            course_counts.columns = ["Course", "Students"]
            fig1 = px.bar(course_counts, x="Course", y="Students", color="Course", title="Students per Course")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            age_counts = df["age"].value_counts().sort_index().reset_index()
            age_counts.columns = ["Age", "Frequency"]
            fig2 = px.bar(age_counts, x="Age", y="Frequency", title="Age Distribution (Fixed & Verified)", color_discrete_sequence=["#2b6cb0"])
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.scatter(
                df, x="attendance", y="grade", color="course", size="internal_marks",
                hover_data=["name", "roll_no", "semester"],
                title="Attendance vs. CGPA (With 75% Threshold)"
            )
            fig3.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="75% Min Attendance")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            sem_avg = df.groupby("semester", as_index=False)["grade"].mean()
            fig4 = px.line(sem_avg, x="semester", y="grade", markers=True, title="Average CGPA Across Semesters")
            st.plotly_chart(fig4, use_container_width=True)

    with tab_ml:
        if not bundle:
            st.warning("Need at least 20 student records to train ML models.")
            return

        st.subheader("1. Regression Benchmark: Old Linear Regression vs. Upgraded Random Forest")
        st.dataframe(bundle["comparison_df"], use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        c1.metric("At-Risk Classifier Accuracy", f"{bundle['clf_metrics']['accuracy']}%")
        c2.metric("At-Risk Classifier F1-Score", f"{bundle['clf_metrics']['f1_score']}")

        st.subheader("2. Explainable AI: What Drives Student Grades Most?")
        fig_imp = px.bar(
            bundle["importance_df"], x="Importance", y="Feature", orientation="h",
            title="Random Forest Feature Importances", color="Importance", color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    with tab_sim:
        if not bundle:
            st.warning("ML model unavailable.")
            return
        st.subheader("Live 'What-If' Student Performance Simulator")
        st.caption("Adjust the sliders below to simulate how changes in attendance or internal marks affect predicted CGPA and academic risk.")

        s1, s2 = st.columns(2)
        sim_att = s1.slider("Attendance (%)", 40.0, 100.0, 78.0, 0.5)
        sim_int = s1.slider("Internal Assessment Marks (out of 40)", 10.0, 40.0, 29.0, 0.5)
        sim_prev = s2.slider("Previous Semester GPA", 4.0, 10.0, 7.6, 0.1)
        sim_sem = s2.selectbox("Semester", [2, 3, 4, 5, 6, 7, 8], index=4)
        sim_course = st.selectbox("Branch / Course", COURSES)

        res = predict_student(bundle, sim_prev, sim_int, sim_att, sim_sem, sim_course)

        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        r1.metric("AI Predicted CGPA", f"{res['predicted_grade']} / 10.0")
        r2.metric("At-Risk Probability", f"{res['risk_probability']}%")
        badge_cls = "risk-high" if "High" in res["risk_level"] else ("risk-mod" if "Moderate" in res["risk_level"] else "risk-safe")
        r3.markdown(f"<br><span class='{badge_cls}'>{res['risk_level']}</span>", unsafe_allow_html=True)
        st.info(f"💡 **AI Recommendation:** {res['advice']}")


def render_reports_and_alerts(df: pd.DataFrame, bundle):
    st.title("📄 PDF Report Cards & Automated Alerts")
    if df.empty or not bundle:
        st.info("Add student records first.")
        return

    selected = st.selectbox("Select Student", [f"{r.roll_no} - {r.name} ({r.course}, Att: {r.attendance}%)" for _, r in df.iterrows()])
    roll_no = selected.split(" - ")[0]
    stu = get_student_by_roll(roll_no)
    pred = predict_student(bundle, stu["prev_gpa"], stu["internal_marks"], stu["attendance"], stu["semester"], stu["course"])

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📑 Generate Official PDF Report Card")
        st.write(f"**Name:** {stu['name']} | **Roll No:** {stu['roll_no']} | **Course:** {stu['course']}")
        st.write(f"**Current CGPA:** {stu['grade']} | **Attendance:** {stu['attendance']}%")
        st.write(f"**AI Forecast:** {pred['predicted_grade']} ({pred['risk_level']})")

        pdf_bytes = generate_student_pdf(stu, pred)
        st.download_button(
            label="📥 Download Styled PDF Report Card",
            data=pdf_bytes,
            file_name=f"ReportCard_{stu['roll_no']}_{stu['name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
        )

    with c2:
        st.subheader("📣 Send Email & SMS Notification")
        default_msg = (
            f"Dear {stu['name']} ({stu['roll_no']}), your current attendance is {stu['attendance']}% "
            f"and CGPA is {stu['grade']}. AI Status: {pred['risk_level']}. {pred['advice']}"
        )
        msg_body = st.text_area("Notification Message", value=default_msg, height=110)

        b1, b2 = st.columns(2)
        if b1.button("📧 Send Email Alert", use_container_width=True):
            ok, status = send_email_alert(stu, "Academic Performance Alert - Smart SMS", msg_body)
            st.success(status) if ok else st.error(status)
        if b2.button("📱 Send SMS Alert", use_container_width=True):
            ok, status = send_sms_alert(stu, msg_body)
            st.success(status) if ok else st.error(status)

    st.markdown("---")
    st.subheader("📜 Notification Audit History (Cloud Logged)")
    st.dataframe(get_alert_logs_df(), use_container_width=True, hide_index=True)


def render_student_portal(user: dict, bundle):
    st.title(f"🎓 Welcome, {user['username'].title()}")
    roll = user.get("student_roll_no") or "2304501"
    stu = get_student_by_roll(roll)
    if not stu:
        st.warning(f"No student record linked to Roll No `{roll}`. Please ask Admin to link your roll number.")
        return

    pred = predict_student(bundle, stu["prev_gpa"], stu["internal_marks"], stu["attendance"], stu["semester"], stu["course"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Roll Number", stu["roll_no"])
    c2.metric("Current CGPA", f"{stu['grade']:.2f}")
    c3.metric("Attendance", f"{stu['attendance']:.1f}%")
    c4.metric("AI Predicted CGPA", f"{pred['predicted_grade']:.2f}")

    st.info(f"**Academic Status:** {pred['risk_level']} — {pred['advice']}")

    pdf_bytes = generate_student_pdf(stu, pred)
    st.download_button(
        "📥 Download My Official PDF Report Card",
        data=pdf_bytes,
        file_name=f"My_ReportCard_{stu['roll_no']}.pdf",
        mime="application/pdf",
        type="primary",
    )


# ---------------- MAIN APP ROUTING ----------------
if "user" not in st.session_state:
    render_auth_page()
else:
    user = st.session_state["user"]
    role = user["role"]
    df = get_all_students_df()
    bundle = get_ml_bundle(len(df))

    with st.sidebar:
        st.markdown("### 🎓 Smart SMS Pro")
        st.caption(f"Logged in as **{user['username']}** (`{role.upper()}`)")

        if role == "admin":
            menu_items = ["Dashboard", "Manage Students", "Analytics & ML", "PDF & Alerts", "User Accounts"]
            icons = ["speedometer2", "people", "cpu", "file-earmark-pdf", "shield-lock"]
        elif role == "teacher":
            menu_items = ["Dashboard", "Manage Students", "Analytics & ML", "PDF & Alerts"]
            icons = ["speedometer2", "people", "cpu", "file-earmark-pdf"]
        else:
            menu_items = ["My Portal", "What-If Simulator"]
            icons = ["person-badge", "sliders"]

        choice = option_menu(None, menu_items, icons=icons, default_index=0)

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state["user"]
            st.rerun()

    if choice == "Dashboard":
        render_dashboard(df)
    elif choice == "Manage Students":
        render_manage_students(df, role)
    elif choice == "Analytics & ML":
        render_analytics_and_ml(df, bundle)
    elif choice == "PDF & Alerts":
        render_reports_and_alerts(df, bundle)
    elif choice == "User Accounts":
        st.title("🛡️ Registered Users & Roles (Admin Panel)")
        st.dataframe(get_all_users_df(), use_container_width=True, hide_index=True)
    elif choice == "My Portal":
        render_student_portal(user, bundle)
    elif choice == "What-If Simulator":
        render_analytics_and_ml(df, bundle)