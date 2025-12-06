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
DARK_MODE = {"bg": "#1A1A2E", "fg": "white", "button": "#E94560", "hover": "#FF6F61", "card": "#2E2E2E"}
LIGHT_MODE = {"bg": "#F0F0F0", "fg": "#1A1A2E", "button": "#007BFF", "hover": "#0056b3", "card": "#FFFFFF"}
theme = DARK_MODE.copy()
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
def sign_in(emp_id, name, cursor, conn):
    from dashboard_modules.ui_helpers import get_db_data_safely
    from dashboard_modules.summary_functions import refresh_summary
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
    try:
        cursor.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    except sqlite3.OperationalError:
        messagebox.showerror("DB Error", "Database table 'attendance' not found. Please relaunch.")
        return
    if cursor.fetchone():
        messagebox.showinfo("INFO", "Already signed in today!")
    else:
        try:
            cursor.execute("INSERT INTO attendance (emp_id, name, date, sign_in) VALUES (?, ?, ?, ?)", (emp_id, name, date, time))
            conn.commit()
            messagebox.showinfo("SUCCESS", f"Signed in at {time}")
            global content
            if content:
                 refresh_summary(content, emp_id, cursor)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

def sign_out(emp_id, cursor, conn):
    from dashboard_modules.ui_helpers import get_db_data_safely
    from dashboard_modules.summary_functions import refresh_summary
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
    try:
        cursor.execute("SELECT sign_in FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    except sqlite3.OperationalError:
        messagebox.showerror("DB Error", "Database table 'attendance' not found. Please relaunch.")
        return
    record = cursor.fetchone()
    if record and record[0] is not None:
        try:
            cursor.execute("UPDATE attendance SET sign_out=? WHERE emp_id=? AND date=?", (time, emp_id, date))
            conn.commit()
            messagebox.showinfo("SUCCESS", f"Signed out at {time}")
            global content
            if content:
                 refresh_summary(content, emp_id, cursor)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
    else:
        messagebox.showwarning("ALERT", "You haven't signed in today!")

def auto_reminder(emp_id, cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely
    now = datetime.now()
    hour = now.hour
    today = now.strftime("%Y-%m-%d")
    query = "SELECT sign_in, sign_out FROM attendance WHERE emp_id=? AND date=?"
    record, err = get_db_data_safely(query, (emp_id, today), fetch_all=False)
    if err:
        return
    if hour >= 9 and (not record or not record[0]):
        messagebox.showinfo("Reminder", "You forgot to sign in today!")
    if hour >= 17 and (not record or not record[1]):
        messagebox.showinfo("Reminder", "You might have forgotten to sign out!")

def export_attendance_csv(cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely
    rows, err = get_db_data_safely("SELECT emp_id, name, date, sign_in, sign_out FROM attendance", fetch_all=True)
    if err:
        messagebox.showerror("Export Error", f"Database error: {err}")
        return
    if not rows:
        messagebox.showinfo("Export", "No attendance rows to export.")
        return
    try:
        import csv
        fname = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(['emp_id', 'name', 'date', 'sign_in', 'sign_out'])
            w.writerows(rows)
        messagebox.showinfo("Export", f"Attendance exported to {fname}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))

# ------------------
# Main and DB setup (NO dummy data; create-first-user modal)
