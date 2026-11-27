import pandas as pd
from database import init_db, bulk_import_csv, DATABASE_URL
from auth import register_user

if __name__ == "__main__":
    print("Connecting to:", "Supabase Cloud PostgreSQL" if "supabase" in DATABASE_URL else DATABASE_URL)
    init_db()

    df = pd.read_csv("students_master.csv")
    inserted, skipped, msg = bulk_import_csv(df)
    print(f"Students Upload -> Inserted: {inserted}, Skipped: {skipped} ({msg})")

    demo_users = [
        ("admin", "admin@college-demo.edu", "admin123", "admin", None),
        ("teacher", "teacher@college-demo.edu", "teacher123", "teacher", None),
        ("student", "diya.kaur1@college-demo.edu", "student123", "student", "2304501"),
    ]
    for uname, email, pwd, role, roll in demo_users:
        ok, status = register_user(uname, email, pwd, role, roll)
        print(f"User '{uname}' ({role}): {status}")

    print("\nSetup complete! Demo Logins:")
    print("  Admin   -> admin / admin123")
    print("  Teacher -> teacher / teacher123")
    print("  Student -> student / student123")