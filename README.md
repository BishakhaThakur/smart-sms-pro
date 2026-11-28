# 🎓 Smart Student Management System (Smart SMS Pro)

A cloud-hosted **Academic Intelligence & Performance Prediction Platform** built with Python, Streamlit, Supabase PostgreSQL, and Scikit-Learn. Designed to manage student records, forecast academic performance using Machine Learning, generate official PDF report cards, and trigger automated low-attendance alerts.

🔗 **Live Web App:** *[Add your Streamlit Cloud URL here after deployment]*

---

## ✨ Key Features

* **🔐 Role-Based Access Control (RBAC):** Secure `bcrypt`-hashed authentication with dedicated dashboards for **Admin**, **Teacher**, and **Student** roles.
* **☁️ Cloud PostgreSQL Backend:** Normalized relational schema (`users`, `students`, `alert_logs`) hosted on **Supabase** via SQLAlchemy ORM, pre-loaded with 300 student records.
* **🗂️ Full CRUD & CSV Bulk Sync:** Live search, multi-filter directory, add/update/delete operations, one-click CSV export, and duplicate-safe bulk CSV import.
* **🤖 Machine Learning & Explainable AI (XAI):**
  * Benchmarks **Random Forest Regressor** against **Linear Regression** ($R^2$, RMSE, MAE).
  * **At-Risk Student Classifier** (Accuracy & F1-Score) with feature importance visualization.
  * Interactive **"What-If" Performance Simulator** to test how attendance and internal marks impact predicted CGPA.
* **📊 Interactive Analytics:** Dynamic Plotly charts for course distribution, age distribution, semester GPA trends, and attendance vs. CGPA scatter plots with a 75% threshold marker.
* **📄 Automated PDF Report Cards:** One-click official college report card generation using `fpdf2`, including AI performance forecasts and risk recommendations.
* **📣 Automated Email & SMS Alerts:** Instant Gmail SMTP low-attendance warnings (auto-triggered when attendance drops below 75%) and Twilio SMS support with a cloud-stored audit log.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend & UI** | Python, Streamlit, `streamlit-option-menu`, Plotly |
| **Database & ORM** | PostgreSQL (Supabase), SQLAlchemy, `psycopg` |
| **Machine Learning** | Scikit-Learn (Random Forest, Linear Regression), Pandas, NumPy |
| **Security** | `bcrypt` Password Hashing, Environment Secrets (`.env` / TOML) |
| **Reporting & Alerts** | `fpdf2` (PDF), Gmail `smtplib` (Email), Twilio (SMS) |
| **Deployment** | Streamlit Community Cloud, Android APK Wrapper |

---

## 📂 Project Structure

```text
smart-sms-pro/
├── .streamlit/
│   └── config.toml          # Custom UI theme configuration
├── app.py                   # Main Streamlit application & RBAC routing
├── auth.py                  # User registration, login & bcrypt hashing
├── database.py              # SQLAlchemy models & Supabase CRUD/bulk operations
├── ml_engine.py             # ML training, benchmarking, XAI & What-If predictor
├── pdf_report.py            # Official styled PDF report card generator
├── notifier.py              # Gmail SMTP & Twilio SMS notification engine
├── seed_db.py               # Initial cloud database seeding script
├── students_master.csv      # 300-record master dataset
├── new_batch_import.csv     # Sample CSV for testing bulk import
└── requirements.txt         # Python dependencies
```

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full CRUD, Delete records, User Accounts, ML, PDF & Alerts |
| **Teacher** | `teacher` | `teacher123` | Add/Update records, Bulk CSV, Analytics, ML, PDF & Alerts |
| **Student** | `student` | `student123` | Personal Portal, AI What-If Simulator & Own PDF Report Card |

---

## 🚀 Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/BishakhaThakur/smart-sms-pro.git](https://github.com/BishakhaThakur/smart-sms-pro.git)
   cd smart-sms-pro
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Seed the database & launch the app:**
   ```bash
   python seed_db.py
   python -m streamlit run app.py
   ```

---

## 👩‍💻 Author

**Bishakha Thakur**  
B.Tech in Computer Science & Engineering  
Ludhiana College of Engineering & Technology (LCET)
