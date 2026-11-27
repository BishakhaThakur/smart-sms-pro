import bcrypt
import pandas as pd
from database import SessionLocal, User


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def register_user(username: str, email: str, password: str, role: str = "student", student_roll_no: str = None):
    username = username.strip().lower()
    email = email.strip().lower()
    with SessionLocal() as db:
        if db.query(User).filter((User.username == username) | (User.email == email)).first():
            return False, "Ye username ya email pehle se registered hai."
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            student_roll_no=student_roll_no,
        )
        db.add(user)
        db.commit()
        return True, "Account successfully create ho gaya."


def authenticate_user(username: str, password: str):
    username = username.strip().lower()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "student_roll_no": user.student_roll_no,
            }
        return None


def get_all_users_df():
    with SessionLocal() as db:
        users = db.query(User).order_by(User.id).all()
        return pd.DataFrame([{
            "ID": u.id,
            "Username": u.username,
            "Email": u.email,
            "Role": u.role.title(),
            "Linked Roll No": u.student_roll_no or "-"
        } for u in users])