from datetime import datetime
from fpdf import FPDF


def generate_student_pdf(student: dict, prediction: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header Banner
    pdf.set_fill_color(26, 54, 93)
    pdf.rect(0, 0, 210, 36, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_y(9)
    pdf.cell(0, 8, "LUDHIANA COLLEGE OF ENGINEERING & TECHNOLOGY", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Department of Computer Science & Engineering | Smart Academic Report Card", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(14)
    pdf.set_text_color(30, 30, 30)

    # Meta Line
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Section 1: Student Profile
    pdf.set_fill_color(235, 241, 248)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, "  1. STUDENT PROFILE", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    profile_rows = [
        ("Roll Number", str(student["roll_no"]), "Full Name", str(student["name"])),
        ("Course / Branch", str(student["course"]), "Semester", f"Semester {student['semester']}"),
        ("Age", f"{student['age']} Years", "Phone", str(student["phone"])),
        ("Email ID", str(student["email"]), "Attendance Status", "Below 75% Warning" if student["attendance"] < 75 else "Satisfactory"),
    ]

    pdf.set_font("Helvetica", "", 10)
    for k1, v1, k2, v2 in profile_rows:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(35, 8, k1, border=1)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(60, 8, v1[:28], border=1)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(35, 8, k2, border=1)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(60, 8, v2[:28], border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # Section 2: Academic Metrics
    pdf.set_fill_color(235, 241, 248)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, "  2. ACADEMIC PERFORMANCE SUMMARY", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    metrics = [
        ("Previous Semester GPA", f"{student['prev_gpa']:.2f} / 10.00"),
        ("Internal Assessment Marks", f"{student['internal_marks']:.1f} / 40.0"),
        ("Current Attendance", f"{student['attendance']:.1f}%"),
        ("Current CGPA / Grade", f"{student['grade']:.2f} / 10.00"),
    ]
    for label, val in metrics:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(95, 8, f"  {label}", border=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(95, 8, f"  {val}", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # Section 3: AI Prediction & Risk Assessment
    pdf.set_fill_color(235, 241, 248)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, "  3. AI PERFORMANCE FORECAST & RISK ASSESSMENT", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    ai_rows = [
        ("ML Model Used", "Random Forest Regressor & Risk Classifier"),
        ("AI Predicted Next CGPA", f"{prediction['predicted_grade']:.2f} / 10.00"),
        ("Academic Risk Category", f"{prediction['risk_level']} (Risk Score: {prediction['risk_probability']}%)"),
    ]
    for label, val in ai_rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(75, 8, f"  {label}", border=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(115, 8, f"  {val}", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Advisor / AI Recommendation:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, prediction["advice"], border=1)

    pdf.ln(18)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(95, 6, "_____________________________", align="L")
    pdf.cell(95, 6, "_____________________________", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(95, 6, "Class Coordinator Signature", align="L")
    pdf.cell(95, 6, "Head of Department (CSE)", align="R", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())