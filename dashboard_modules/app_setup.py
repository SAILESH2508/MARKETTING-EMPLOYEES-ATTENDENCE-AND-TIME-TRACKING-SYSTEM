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
def setup_database_and_start_app():
    conn = sqlite3.connect("attendance_system.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
                      id INTEGER PRIMARY KEY, name TEXT
                    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS attendance (
                      emp_id INTEGER, name TEXT, date TEXT, sign_in TEXT, sign_out TEXT
                    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS salary (
                      emp_id INTEGER, name TEXT, salary REAL, bonus REAL, deductions REAL
                    )""")
    conn.commit()

    # Check for existing employees
    cursor.execute("SELECT id, name FROM employees")
    rows = cursor.fetchall()

    root = tk.Tk()
    root.withdraw()

    if not rows:
        # No employees: prompt to create the first user (admin flow)
        def create_first_user():
            create_win = tk.Toplevel()
            create_win.title("Create First Employee")
            create_win.geometry("500x400")
            create_win.transient(root)
            tk.Label(create_win, text="No employees found. Create the first employee below:", font=("Arial", 12)).pack(pady=8)
            frm = tk.Frame(create_win)
            frm.pack(padx=12, pady=8, fill='x')
            tk.Label(frm, text="Name:").grid(row=0, column=0, sticky='w')
            name_ent = tk.Entry(frm)
            name_ent.grid(row=0, column=1, pady=6, sticky='ew')
            tk.Label(frm, text="Salary (base):").grid(row=1, column=0, sticky='w')
            sal_ent = tk.Entry(frm)
            sal_ent.grid(row=1, column=1, pady=6, sticky='ew')
            tk.Label(frm, text="Bonus:").grid(row=2, column=0, sticky='w')
            bon_ent = tk.Entry(frm)
            bon_ent.grid(row=2, column=1, pady=6, sticky='ew')
            tk.Label(frm, text="Deductions:").grid(row=3, column=0, sticky='w')
            ded_ent = tk.Entry(frm)
            ded_ent.grid(row=3, column=1, pady=6, sticky='ew')
            frm.columnconfigure(1, weight=1)
            def submit_first():
                n = name_ent.get().strip()
                try:
                    s = float(sal_ent.get().strip() or 0)
                except:
                    messagebox.showerror("Input Error", "Salary must be a number.")
                    return
                try:
                    b = float(bon_ent.get().strip() or 0)
                except:
                    messagebox.showerror("Input Error", "Bonus must be a number.")
                    return
                try:
                    d = float(ded_ent.get().strip() or 0)
                except:
                    messagebox.showerror("Input Error", "Deductions must be a number.")
                    return
                if not n:
                    messagebox.showerror("Input Error", "Name cannot be empty.")
                    return
                cursor.execute("INSERT INTO employees (name) VALUES (?)", (n,))
