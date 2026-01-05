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

# Theme and constants from ui_helpers (or define local fallback)
try:
    from dashboard_modules.ui_helpers import theme, DARK_MODE, LIGHT_MODE, RoundedFrame
except ImportError:
    DARK_MODE = {
        "bg": "#0A192F",
        "fg": "white",
        "button": "#E94560",
        "hover": "#FF6F61",
        "card": "#172A45",
    }
    LIGHT_MODE = {
        "bg": "#F0F0F0",
        "fg": "#1A1A2E",
        "button": "#007BFF",
        "hover": "#0056b3",
        "card": "#FFFFFF",
    }
    theme = DARK_MODE.copy()

    class RoundedFrame(tk.Frame):
        # Fallback simple frame
        def __init__(self, parent, **kwargs):
            bg_color = kwargs.pop("bg_color", theme["card"])
            super().__init__(parent, bg=bg_color, **kwargs)
            self.inner_frame = self


MODEL_DIR = "models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Global references
content = None
ml_training_in_progress = False
ml_trained_this_session = False


# ------------------
def setup_database_and_start_app():
    conn = sqlite3.connect("attendance_system.db")
    cursor = conn.cursor()

    # Use standard sqlite schemas to prevent OperationalErrors down the line
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS employees (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'Employee',
              password TEXT,
              face_encoding BLOB,
              lockout_until TEXT
            )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS attendance (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              emp_id INTEGER,
              name TEXT,
              date TEXT,
              sign_in TEXT,
              sign_out TEXT,
              FOREIGN KEY (emp_id) REFERENCES employees(id)
            )"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS salary (
              emp_id INTEGER PRIMARY KEY,
              name TEXT,
              salary REAL,
              bonus REAL,
              deductions REAL,
              net_salary REAL,
              FOREIGN KEY (emp_id) REFERENCES employees(id)
            )"""
    )
    conn.commit()

    # Check for existing employees
    cursor.execute("SELECT id, name FROM employees")
    rows = cursor.fetchall()

    root = tk.Tk()
    root.withdraw()

    if not rows:
        # No employees: prompt to create the first user (admin flow)
        def create_first_user():
            create_win = tk.Toplevel(root)
            create_win.title("Setup - Create First Employee")
            create_win.geometry("520x450")
            create_win.configure(bg=theme["bg"])
            create_win.transient(root)

            # Center window
            sw = create_win.winfo_screenwidth()
            sh = create_win.winfo_screenheight()
            x = (sw // 2) - 260
            y = (sh // 2) - 225
            create_win.geometry(f"520x450+{x}+{y}")

            tk.Label(
                create_win,
                text="Welcome! Create First Employee Record",
                font=("Segoe UI", 16, "bold"),
                bg=theme["bg"],
                fg=theme["fg"],
            ).pack(pady=(20, 5))

            tk.Label(
                create_win,
                text="The database is empty. Please set up the first account.",
                font=("Segoe UI", 10),
                bg=theme["bg"],
                fg=theme.get("text_secondary", "gray"),
            ).pack(pady=(0, 15))

            # Form using RoundedFrame
            form_container = RoundedFrame(
                create_win, width=460, height=280, bg_color=theme["card"]
            )
            form_container.pack(pady=10, padx=20, fill="both", expand=True)
            frm = form_container.inner_frame

            tk.Label(
                frm,
                text="Full Name",
                font=("Segoe UI", 10, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).grid(row=0, column=0, sticky="w", pady=8, padx=10)
            name_ent = tk.Entry(
                frm,
                font=("Segoe UI", 11),
                bg=theme["bg"],
                fg=theme["fg"],
                relief="flat",
                insertbackground=theme["fg"],
            )
            name_ent.grid(row=0, column=1, pady=8, padx=10, sticky="ew")

            tk.Label(
                frm,
                text="Base Salary (₹)",
                font=("Segoe UI", 10, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).grid(row=1, column=0, sticky="w", pady=8, padx=10)
            sal_ent = tk.Entry(
                frm,
                font=("Segoe UI", 11),
                bg=theme["bg"],
                fg=theme["fg"],
                relief="flat",
                insertbackground=theme["fg"],
            )
            sal_ent.grid(row=1, column=1, pady=8, padx=10, sticky="ew")

            tk.Label(
                frm,
                text="Bonus (₹)",
                font=("Segoe UI", 10, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).grid(row=2, column=0, sticky="w", pady=8, padx=10)
            bon_ent = tk.Entry(
                frm,
                font=("Segoe UI", 11),
                bg=theme["bg"],
                fg=theme["fg"],
                relief="flat",
                insertbackground=theme["fg"],
            )
            bon_ent.grid(row=2, column=1, pady=8, padx=10, sticky="ew")

            tk.Label(
                frm,
                text="Deductions (₹)",
                font=("Segoe UI", 10, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).grid(row=3, column=0, sticky="w", pady=8, padx=10)
            ded_ent = tk.Entry(
                frm,
                font=("Segoe UI", 11),
                bg=theme["bg"],
                fg=theme["fg"],
                relief="flat",
                insertbackground=theme["fg"],
            )
            ded_ent.grid(row=3, column=1, pady=8, padx=10, sticky="ew")

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

                try:
                    from hashlib import sha256

                    pwd = sha256("password".encode()).hexdigest()

                    cursor.execute(
                        "INSERT INTO employees (name, role, password) VALUES (?, 'Employee', ?)",
                        (n, pwd),
                    )
                    emp_id = cursor.lastrowid

                    cursor.execute(
                        "INSERT INTO salary (emp_id, name, salary, bonus, deductions, net_salary) VALUES (?, ?, ?, ?, ?, ?)",
                        (emp_id, n, s, b, d, s + b - d),
                    )
                    conn.commit()
                    messagebox.showinfo(
                        "Success",
                        f"First employee record created!\n\nID: {emp_id}\nName: {n}\nDefault Password: 'password'\n\nYou will be redirected to the login screen.",
                    )
                    create_win.destroy()
                    root.destroy()
                    conn.close()

                    # Launch Login System
                    import subprocess
                    import sys

                    subprocess.Popen([sys.executable, "emp.py"])
                except Exception as ex:
                    messagebox.showerror(
                        "Database Error", f"Could not create first employee: {ex}"
                    )

            # Styled create button
            submit_btn = tk.Button(
                create_win,
                text="Create Account & Start",
                font=("Segoe UI", 11, "bold"),
                bg=theme["button"],
                fg=theme.get("button_fg", "white"),
                activebackground=theme["hover"],
                activeforeground=theme.get("button_fg", "white"),
                relief="flat",
                bd=0,
                cursor="hand2",
                command=submit_first,
            )
            submit_btn.pack(pady=15)
            submit_btn.bind("<Enter>", lambda e: submit_btn.config(bg=theme["hover"]))
            submit_btn.bind("<Leave>", lambda e: submit_btn.config(bg=theme["button"]))

            create_win.grab_set()
            create_win.wait_window()

        create_first_user()
        try:
            root.mainloop()
        except:
            pass
    else:
        conn.close()
        root.destroy()
        # Launch login screen
        import subprocess
        import sys

        subprocess.Popen([sys.executable, "emp.py"])
