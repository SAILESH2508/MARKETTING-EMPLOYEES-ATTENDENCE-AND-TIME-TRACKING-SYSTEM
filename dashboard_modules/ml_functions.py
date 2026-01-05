import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading

# ML imports
try:
    import pandas as pd
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.ensemble import IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.calibration import CalibratedClassifierCV
    import pickle

    SKLEARN_AVAILABLE = True
except Exception as e:
    SKLEARN_AVAILABLE = False
    _SKL_ERR = str(e)

# Theme and constants
try:
    from dashboard_modules.ui_helpers import theme
except ImportError:
    theme = {
        "bg": "#F0F0F0",
        "fg": "#1A1A2E",
        "button": "#007BFF",
        "hover": "#0056b3",
        "card": "#FFFFFF",
    }

BUTTON_FONT = ("Arial", 12)
MODEL_DIR = "models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Global reference for the content frame (used for navigation)
content = None

# Global flag to prevent ML training loops
ml_training_in_progress = False
ml_trained_this_session = False


# Extracted from employee_dashboard.py

# Note: Functions from other modules are imported via employee_dashboard.py


# ------------------
def load_attendance_df(cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely

    if not SKLEARN_AVAILABLE:
        return None, "scikit-learn/pandas not installed."
    try:
        cursor.execute(
            "SELECT emp_id, name, date, sign_in, sign_out FROM attendance WHERE sign_in IS NOT NULL"
        )
    except sqlite3.OperationalError as e:
        return None, f"Database error: {e}"
    rows = cursor.fetchall()
    if not rows:
        return None, "No attendance data in DB."
    import pandas as pd

    df = pd.DataFrame(rows, columns=["emp_id", "name", "date", "sign_in", "sign_out"])

    def time_to_seconds(t):
        try:
            h, m, s = map(int, t.split(":"))
            return h * 3600 + m * 60 + s
        except:
            return None

    df["sign_in_seconds"] = df["sign_in"].apply(time_to_seconds)
    df["on_time"] = df["sign_in_seconds"].apply(
        lambda s: 1 if s is not None and s <= 9 * 3600 else 0
    )
    df["dayofweek"] = pd.to_datetime(df["date"]).dt.dayofweek
    return df, None


def get_ml_status(cursor):
    msgs = []
    if SKLEARN_AVAILABLE:
        msgs.append("scikit-learn & pandas: available")
    else:
        msgs.append(f"ML libs missing: {_SKL_ERR}")
    for m in ["punctuality.pkl", "salary_reg.pkl", "anomaly.pkl"]:
        path = os.path.join(MODEL_DIR, m)
        msgs.append(f"{m}: {'exists' if os.path.exists(path) else 'missing'}")
    return "\n".join(msgs)


# ------------------
# ML training + inference
# ------------------
def train_punctuality_model(cursor, return_eval=False, silent=True):
    if not SKLEARN_AVAILABLE:
        if not silent:
            messagebox.showerror(
                "ML Error",
                "scikit-learn and pandas required. Install with: pip install scikit-learn pandas",
            )
        return None
    df, err = load_attendance_df(cursor)
    if err:
        if not silent:
            messagebox.showinfo("ML", err)
        return None
    hist = df.groupby("emp_id")["sign_in_seconds"].mean().rename("mean_sign_in")
    df = df.join(hist, on="emp_id")
    X = df[["dayofweek", "mean_sign_in"]].fillna(df["mean_sign_in"].mean())
    y = df["on_time"]
    if len(df) < 10:
        if not silent:
            messagebox.showinfo(
                "ML", "Not enough data to train a decent model (need >=10 rows)."
            )
        return None
    if y.nunique() < 2:
        if not silent:
            messagebox.showinfo(
                "ML",
                "Target variable has no variation (everyone always on-time or always late). Cannot train model.",
            )
        return None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    clf = LogisticRegression(max_iter=400)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    try:
        # Use cv=5 instead of deprecated 'prefit'
        calib = CalibratedClassifierCV(
            LogisticRegression(max_iter=400), cv=5, method="sigmoid"
        )
        calib.fit(X_train, y_train)
        final_clf = calib
    except Exception:
        final_clf = clf
    with open(os.path.join(MODEL_DIR, "punctuality.pkl"), "wb") as f:
        pickle.dump(final_clf, f)
    if not silent:
        messagebox.showinfo(
            "ML", f"Punctuality model trained. Test accuracy: {acc:.2f}"
        )
    if return_eval:
        try:
            from sklearn.metrics import confusion_matrix, roc_curve, auc

            cm = confusion_matrix(y_test, preds)
            if hasattr(final_clf, "predict_proba"):
                probs = final_clf.predict_proba(X_test)[:, 1]
                fpr, tpr, _ = roc_curve(y_test, probs)
                roc_auc = auc(fpr, tpr)
                roc_art = (fpr, tpr, roc_auc)
            else:
                roc_art = None
            return {"accuracy": acc, "confusion_matrix": cm, "roc": roc_art}
        except Exception:
            return {"accuracy": acc}
    return None


def predict_punctuality_for_emp(emp_id, cursor):
    path = os.path.join(MODEL_DIR, "punctuality.pkl")
    if not os.path.exists(path):
        messagebox.showinfo("ML", "Punctuality model not found. Train it first.")
        return
    if not SKLEARN_AVAILABLE:
        messagebox.showerror("ML Error", "scikit-learn and pandas required.")
        return
    with open(path, "rb") as f:
        clf = pickle.load(f)
    df, err = load_attendance_df(cursor)
    if err:
        messagebox.showinfo("ML", err)
        return
    import pandas as pd

    emp_mean = df[df["emp_id"] == emp_id]["sign_in_seconds"].mean()
    if pd.isna(emp_mean):
        emp_mean = df["sign_in_seconds"].mean()
    dayofweek = datetime.now().weekday()
    X = pd.DataFrame([[dayofweek, emp_mean]], columns=["dayofweek", "mean_sign_in"])
    pred = clf.predict(X)[0]
    prob = clf.predict_proba(X)[0][1] if hasattr(clf, "predict_proba") else None
    label = "On-time" if pred == 1 else "Likely Late"
    if prob is not None:
        messagebox.showinfo("Prediction", f"{label} (prob on-time: {prob:.2f})")
    else:
        messagebox.showinfo("Prediction", f"{label}")


def train_anomaly_detector(cursor, silent=True):
    if not SKLEARN_AVAILABLE:
        if not silent:
            messagebox.showerror(
                "ML Error",
                "scikit-learn and pandas required. Install with: pip install scikit-learn pandas",
            )
        return
    df, err = load_attendance_df(cursor)
    if err:
        if not silent:
            messagebox.showinfo("ML", err)
        return
    X = df[["sign_in_seconds"]].fillna(df["sign_in_seconds"].median())
    if len(X) < 10:
        if not silent:
            messagebox.showinfo("ML", "Not enough data to train anomaly detector.")
        return
    iso = IsolationForest(contamination=0.05, random_state=42)
    iso.fit(X)
    with open(os.path.join(MODEL_DIR, "anomaly.pkl"), "wb") as f:
        pickle.dump(iso, f)
    if not silent:
        messagebox.showinfo("ML", "Anomaly detector trained and saved.")


def run_anomaly_scan(cursor, frame):
    from dashboard_modules.ui_helpers import (
        clear_content,
        get_db_data_safely,
        apply_treeview_style,
    )

    path = os.path.join(MODEL_DIR, "anomaly.pkl")
    if not os.path.exists(path):
        messagebox.showinfo("ML", "Anomaly model not found. Train it first.")
        return
    if not SKLEARN_AVAILABLE:
        messagebox.showerror("ML Error", "scikit-learn and pandas required.")
        return
    df, err = load_attendance_df(cursor)
    if err:
        messagebox.showinfo("ML", err)
        return
    with open(path, "rb") as f:
        iso = pickle.load(f)
    X = df[["sign_in_seconds"]].fillna(df["sign_in_seconds"].median())
    preds = iso.predict(X)
    anomalies = df[preds == -1]
    clear_content(frame)
    tk.Label(
        frame,
        text="Anomaly Scan Results",
        font=("Arial", 14),
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(pady=6)
    if anomalies.empty:
        tk.Label(
            frame, text="No anomalies detected.", bg=theme["bg"], fg=theme["fg"]
        ).pack(pady=10)
    else:
        # Define style locally if needed (though global might apply, we ensure headers are visible)
        try:
            s = ttk.Style()
            apply_treeview_style(s)
        except:
            pass

        tree_frame = tk.Frame(frame, bg=theme["bg"])
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame,
            columns=("Date", "Sign In", "Sign Out", "Employee"),
            show="headings",
            height=8,
            style="Dark.Treeview",
        )

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        tree.heading("Date", text="Date", anchor="center")
        tree.column("Date", anchor="center")
        tree.heading("Sign In", text="Sign In", anchor="center")
        tree.column("Sign In", anchor="center")
        tree.heading("Sign Out", text="Sign Out", anchor="center")
        tree.column("Sign Out", anchor="center")
        tree.heading("Employee", text="Emp ID", anchor="center")
        tree.column("Employee", anchor="center")
        for _, row in anomalies.iterrows():
            tree.insert(
                "",
                "end",
                values=(row["date"], row["sign_in"], row["sign_out"], row["emp_id"]),
            )


def train_salary_predictor(cursor, silent=True):
    if not SKLEARN_AVAILABLE:
        if not silent:
            messagebox.showerror(
                "ML Error",
                "scikit-learn and pandas required. Install with: pip install scikit-learn pandas",
            )
        return
    try:
        cursor.execute("SELECT emp_id, salary, bonus, deductions FROM salary")
    except sqlite3.OperationalError as e:
        if not silent:
            messagebox.showinfo("ML", f"Database error: {e}")
        return
    rows = cursor.fetchall()
    if not rows or len(rows) < 5:
        if not silent:
            messagebox.showinfo(
                "ML", "Not enough salary data to train (need >=5 rows)."
            )
        return
    import pandas as pd

    df = pd.DataFrame(rows, columns=["emp_id", "salary", "bonus", "deductions"])
    X = df[["bonus", "deductions"]].fillna(0)
    y = df["salary"]
    if y.nunique() < 2:
        if not silent:
            messagebox.showinfo(
                "ML",
                "Target salary has no variation (all salaries are the same). Cannot train model.",
            )
        return
    model = LinearRegression()
    model.fit(X, y)
    with open(os.path.join(MODEL_DIR, "salary_reg.pkl"), "wb") as f:
        pickle.dump(model, f)
    if not silent:
        messagebox.showinfo("ML", "Salary predictor trained and saved.")


def predict_salary(emp_id, cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely

    path = os.path.join(MODEL_DIR, "salary_reg.pkl")
    if not os.path.exists(path):
        messagebox.showinfo("ML", "Salary model not found. Train it first.")
        return
    if not SKLEARN_AVAILABLE:
        messagebox.showerror("ML Error", "scikit-learn and pandas required.")
        return
    row, err = get_db_data_safely(
        "SELECT bonus, deductions FROM salary WHERE emp_id=?",
        (emp_id,),
        fetch_all=False,
    )
    if err:
        messagebox.showerror("DB Error", err)
        return
    if not row:
        messagebox.showinfo("ML", "No salary row found for this employee.")
        return
    import pandas as pd

    bonus, deductions = row
    with open(path, "rb") as f:
        model = pickle.load(f)
    bonus = bonus or 0
    deductions = deductions or 0
    X_predict = pd.DataFrame([[bonus, deductions]], columns=["bonus", "deductions"])
    pred = model.predict(X_predict)[0]
    messagebox.showinfo("Salary Prediction", f"Predicted base salary: {pred:.2f}")
