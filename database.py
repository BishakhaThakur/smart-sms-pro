import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    if not url:
        return "sqlite:///local_sms.db"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    student_roll_no = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    course = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
    prev_gpa = Column(Float, nullable=False)
    internal_marks = Column(Float, nullable=False)
    attendance = Column(Float, nullable=False)
    grade = Column(Float, nullable=False)


class AlertLog(Base):
    __tablename__ = "alert_logs"
    id = Column(Integer, primary_key=True, index=True)
    student_roll_no = Column(String(30), nullable=False)
    student_name = Column(String(100), nullable=False)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(30), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_all_students_df():
    with SessionLocal() as db:
        rows = db.query(Student).order_by(Student.roll_no).all()
        if not rows:
            return pd.DataFrame(columns=[
                "id", "roll_no", "name", "age", "email", "phone",
                "course", "semester", "prev_gpa", "internal_marks", "attendance", "grade"
            ])
        data = [{
            "id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "age": s.age,
            "email": s.email,
            "phone": s.phone,
            "course": s.course,
            "semester": s.semester,
            "prev_gpa": s.prev_gpa,
            "internal_marks": s.internal_marks,
            "attendance": s.attendance,
            "grade": s.grade,
        } for s in rows]
        return pd.DataFrame(data)


def get_student_by_roll(roll_no: str):
    with SessionLocal() as db:
        s = db.query(Student).filter(Student.roll_no == str(roll_no)).first()
        if not s:
            return None
        return {
            "id": s.id, "roll_no": s.roll_no, "name": s.name, "age": s.age,
            "email": s.email, "phone": s.phone, "course": s.course,
            "semester": s.semester, "prev_gpa": s.prev_gpa,
            "internal_marks": s.internal_marks, "attendance": s.attendance, "grade": s.grade
        }


def add_student(data: dict):
    with SessionLocal() as db:
        exists = db.query(Student).filter(Student.roll_no == str(data["roll_no"])).first()
        if exists:
            return False, "Ye Roll Number pehle se exist karta hai."
        student = Student(
            roll_no=str(data["roll_no"]),
            name=data["name"],
            age=int(data["age"]),
            email=data["email"],
            phone=str(data["phone"]),
            course=data["course"],
            semester=int(data["semester"]),
            prev_gpa=float(data["prev_gpa"]),
            internal_marks=float(data["internal_marks"]),
            attendance=float(data["attendance"]),
            grade=float(data["grade"]),
        )
        db.add(student)
        db.commit()
        return True, "Student record successfully add ho gaya."


def update_student(roll_no: str, updates: dict):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.roll_no == str(roll_no)).first()
        if not student:
            return False, "Student nahi mila."
        for key, value in updates.items():
            if hasattr(student, key):
                setattr(student, key, value)
        db.commit()
        return True, "Student record update ho gaya."


def delete_student(roll_no: str):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.roll_no == str(roll_no)).first()
        if not student:
            return False, "Student nahi mila."
        db.delete(student)
        db.commit()
        return True, "Student record delete ho gaya."


def bulk_import_csv(df: pd.DataFrame):
    required = {
        "roll_no", "name", "age", "email", "phone",
        "course", "semester", "prev_gpa", "internal_marks", "attendance", "grade"
    }
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        return 0, 0, f"CSV me ye columns missing hain: {', '.join(missing)}"

    inserted = 0
    skipped = 0
    with SessionLocal() as db:
        existing_rolls = {r[0] for r in db.query(Student.roll_no).all()}
        new_records = []
        for _, row in df.iterrows():
            r_no = str(row["roll_no"]).strip()
            if r_no in existing_rolls:
                skipped += 1
                continue
            existing_rolls.add(r_no)
            new_records.append(Student(
                roll_no=r_no,
                name=str(row["name"]).strip(),
                age=int(row["age"]),
                email=str(row["email"]).strip(),
                phone=str(row["phone"]).strip(),
                course=str(row["course"]).strip(),
                semester=int(row["semester"]),
                prev_gpa=float(row["prev_gpa"]),
                internal_marks=float(row["internal_marks"]),
                attendance=float(row["attendance"]),
                grade=float(row["grade"]),
            ))
            inserted += 1
        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
    return inserted, skipped, "Import complete!"


def log_alert(roll_no, name, channel, recipient, message, status):
    with SessionLocal() as db:
        log = AlertLog(
            student_roll_no=str(roll_no),
            student_name=name,
            channel=channel,
            recipient=recipient,
            message=message,
            status=status,
        )
        db.add(log)
        db.commit()


def get_alert_logs_df():
    with SessionLocal() as db:
        rows = db.query(AlertLog).order_by(AlertLog.sent_at.desc()).limit(100).all()
        if not rows:
            return pd.DataFrame(columns=["Roll No", "Student", "Channel", "Recipient", "Status", "Time"])
        return pd.DataFrame([{
            "Roll No": r.student_roll_no,
            "Student": r.student_name,
            "Channel": r.channel,
            "Recipient": r.recipient,
            "Status": r.status,
            "Time": r.sent_at.strftime("%Y-%m-%d %H:%M"),
        } for r in rows])