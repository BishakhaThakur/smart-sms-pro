import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUM_FEATURES = ["prev_gpa", "internal_marks", "attendance", "semester"]
CAT_FEATURES = ["course"]
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES


def train_and_evaluate_models(df: pd.DataFrame):
    if len(df) < 20:
        return None

    X = df[ALL_FEATURES].copy()
    y_reg = df["grade"].astype(float)
    y_clf = ((df["grade"] < 7.0) | (df["attendance"] < 75.0)).astype(int)

    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_FEATURES),
        ]
    )

    # 1. Baseline Model (Old 6th-Sem Approach: Linear Regression)
    lr_pipe = Pipeline([
        ("prep", preprocessor),
        ("model", LinearRegression()),
    ])
    lr_pipe.fit(X_train, y_reg_train)
    lr_preds = lr_pipe.predict(X_test)

    # 2. Upgraded Regression Model (Random Forest Regressor)
    rf_reg_pipe = Pipeline([
        ("prep", preprocessor),
        ("model", RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42)),
    ])
    rf_reg_pipe.fit(X_train, y_reg_train)
    rf_preds = rf_reg_pipe.predict(X_test)

    # 3. At-Risk Classification Model (Random Forest Classifier)
    rf_clf_pipe = Pipeline([
        ("prep", preprocessor),
        ("model", RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)),
    ])
    rf_clf_pipe.fit(X_train, y_clf_train)
    clf_preds = rf_clf_pipe.predict(X_test)

    comparison_df = pd.DataFrame([
        {
            "Model": "Linear Regression (Old Baseline)",
            "R2 Score": round(float(r2_score(y_reg_test, lr_preds)), 4),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_reg_test, lr_preds))), 4),
            "MAE": round(float(mean_absolute_error(y_reg_test, lr_preds)), 4),
        },
        {
            "Model": "Random Forest Regressor (Upgraded)",
            "R2 Score": round(float(r2_score(y_reg_test, rf_preds)), 4),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_reg_test, rf_preds))), 4),
            "MAE": round(float(mean_absolute_error(y_reg_test, rf_preds)), 4),
        },
    ])

    # Feature Importances for Explainable AI
    feature_names = NUM_FEATURES + list(
        rf_reg_pipe.named_steps["prep"].named_transformers_["cat"].get_feature_names_out(CAT_FEATURES)
    )
    importances = rf_reg_pipe.named_steps["model"].feature_importances_
    importance_df = (
        pd.DataFrame({"Feature": feature_names, "Importance": importances})
        .sort_values("Importance", ascending=True)
    )

    clf_metrics = {
        "accuracy": round(float(accuracy_score(y_clf_test, clf_preds)) * 100, 2),
        "f1_score": round(float(f1_score(y_clf_test, clf_preds, zero_division=0)), 4),
    }

    return {
        "rf_reg": rf_reg_pipe,
        "rf_clf": rf_clf_pipe,
        "comparison_df": comparison_df,
        "importance_df": importance_df,
        "clf_metrics": clf_metrics,
    }


def predict_student(bundle, prev_gpa: float, internal_marks: float, attendance: float, semester: int, course: str):
    sample = pd.DataFrame([{
        "prev_gpa": float(prev_gpa),
        "internal_marks": float(internal_marks),
        "attendance": float(attendance),
        "semester": int(semester),
        "course": str(course),
    }])

    pred_grade = float(np.clip(bundle["rf_reg"].predict(sample)[0], 4.0, 10.0))
    risk_prob = float(bundle["rf_clf"].predict_proba(sample)[0][1]) if len(bundle["rf_clf"].classes_) > 1 else 0.0

    if attendance < 75.0 or pred_grade < 6.5 or risk_prob >= 0.6:
        risk_level = "High Risk"
        advice = "Immediate intervention needed: improve attendance above 75% and schedule faculty mentoring."
    elif attendance < 82.0 or pred_grade < 7.5 or risk_prob >= 0.3:
        risk_level = "Moderate Risk"
        advice = "Borderline performance: focus on internal assessments and consistent class attendance."
    else:
        risk_level = "Safe / On-Track"
        advice = "Strong academic standing: maintain current attendance and assessment consistency."

    return {
        "predicted_grade": round(pred_grade, 2),
        "risk_probability": round(risk_prob * 100, 1),
        "risk_level": risk_level,
        "advice": advice,
    }