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
    from typing import Any
    pd: Any = None
    LogisticRegression: Any = None
    LinearRegression: Any = None
    IsolationForest: Any = None
    train_test_split: Any = None
    accuracy_score: Any = None
    CalibratedClassifierCV: Any = None
    pickle: Any = None

# Updated Import from ui_helpers
try:
    from dashboard_modules.ui_helpers import (
        theme,
        RoundedFrame,
        ToolTip,
        create_scrollable_frame,
        clear_content,
        get_db_data_safely,
        BUTTON_FONT,
        MODEL_DIR,
        HEADER_FONT,
        SUBHEADER_FONT,
        TITLE_FONT,
        BODY_FONT,
        SMALL_FONT,
    )
except ImportError:
    # Fallback theme
    theme = {
        "bg": "#0A192F",
        "fg": "white",
        "button": "#E94560",
        "card": "#172A45",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
    }
    MODEL_DIR = "models"
    HEADER_FONT = ("Segoe UI", 26, "bold")
    SUBHEADER_FONT = ("Segoe UI", 16, "bold")
    TITLE_FONT = ("Segoe UI", 14, "bold")
    BODY_FONT = ("Segoe UI", 11)
    SMALL_FONT = ("Segoe UI", 9)

    class FallbackRoundedFrame(tk.Frame):
        def __init__(self, parent, **kwargs):
            bg_color = kwargs.pop("bg_color", theme["card"])
            super().__init__(parent, bg=bg_color, **kwargs)
            self.inner_frame = self
    RoundedFrame = FallbackRoundedFrame


def get_predicted_salary_value(emp_id, cursor):
    """Get predicted salary value with better error handling"""
    path = os.path.join(MODEL_DIR, "salary_reg.pkl")

    if os.path.exists(path) and SKLEARN_AVAILABLE:
        try:
            with open(path, "rb") as f:
                model = pickle.load(f)

            cursor.execute(
                "SELECT bonus, deductions FROM salary WHERE emp_id=?", (emp_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None, "No salary data found"

            bonus, deductions = row
            bonus = bonus or 0
            deductions = deductions or 0

            import pandas as pd

            X_predict = pd.DataFrame(
                [[bonus, deductions]], columns=["bonus", "deductions"]
            )
            pred = model.predict(X_predict)[0]
            return pred, None

        except Exception as e:
            return None, f"Model prediction error: {e}"
    else:
        # Fallback to actual salary
        try:
            cursor.execute("SELECT salary FROM salary WHERE emp_id=?", (emp_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0], "Actual salary (no model)"
            return None, "No salary data available"
        except Exception as e:
            return None, f"Database error: {e}"


def get_punctuality_probability(emp_id, cursor):
    """Get punctuality probability with better error handling"""
    path = os.path.join(MODEL_DIR, "punctuality.pkl")

    if os.path.exists(path) and SKLEARN_AVAILABLE:
        try:
            with open(path, "rb") as f:
                clf = pickle.load(f)

            # Get employee's average sign-in time
            cursor.execute(
                "SELECT AVG(CASE WHEN sign_in IS NOT NULL THEN "
                "(CAST(substr(sign_in,1,2) AS INTEGER) * 3600 + "
                "CAST(substr(sign_in,4,2) AS INTEGER) * 60 + "
                "CAST(substr(sign_in,7,2) AS INTEGER)) END) "
                "FROM attendance WHERE emp_id=?",
                (emp_id,),
            )

            result = cursor.fetchone()
            emp_mean = (
                result[0] if result and result[0] else 8.5 * 3600
            )  # Default 8:30 AM

            dayofweek = datetime.now().weekday()

            import pandas as pd

            X = pd.DataFrame(
                [[dayofweek, emp_mean]], columns=["dayofweek", "mean_sign_in"]
            )

            if hasattr(clf, "predict_proba"):
                prob_on_time = clf.predict_proba(X)[0][1]
            else:
                prob_on_time = float(clf.predict(X)[0])

            return float(prob_on_time), None

        except Exception as e:
            return None, f"Model error: {e}"
    else:
        # Fallback to historical performance
        try:
            cursor.execute(
                """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time
                FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
            """,
                (emp_id,),
            )

            result = cursor.fetchone()
            if result and result[0] > 0:
                total, on_time = result
                return (on_time / total), "Historical average"
            return None, "No attendance data"

        except Exception as e:
            return None, f"Database error: {e}"


def compute_perfection_score(emp_id, cursor):
    """Compute perfection score with error handling"""
    try:
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time
            FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        result = cursor.fetchone()
        if result and result[0] > 0:
            total, on_time = result
            return (on_time / total) if total else 0.0
        return 0.0

    except Exception as e:
        print(f"Perfection score error: {e}")
        return 0.0


def refresh_summary(frame, emp_id, cursor):
    """Refresh summary with error handling"""
    try:
        show_default_summary(frame, emp_id, cursor)
    except Exception as e:
        print(f"Summary refresh error: {e}")


def show_default_summary(frame, emp_id, cursor):
    """Fixed main dashboard summary with better error handling and layout"""

    # Clear existing content
    for widget in frame.winfo_children():
        widget.destroy()

    # Create main container
    main_container = tk.Frame(frame, bg=theme["bg"])
    main_container.pack(fill="both", expand=True, padx=15, pady=15)

    # Title
    title_frame = tk.Frame(main_container, bg=theme["bg"])
    title_frame.pack(fill="x", pady=(0, 20))
    tk.Label(
        title_frame,
        text="📊 Dashboard Summary",
        font=HEADER_FONT,
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(anchor="w")

    # Create grid layout for cards
    grid_frame = tk.Frame(main_container, bg=theme["bg"])
    grid_frame.pack(fill="both", expand=True)

    # Configure grid
    grid_frame.grid_columnconfigure(0, weight=1)
    grid_frame.grid_columnconfigure(1, weight=1)
    grid_frame.grid_columnconfigure(2, weight=1)

    # Row 1: Basic Info Cards
    create_salary_card(grid_frame, 0, 0, emp_id, cursor)
    create_attendance_card(grid_frame, 0, 1, emp_id, cursor)
    create_status_card(grid_frame, 0, 2, emp_id, cursor)

    # Row 2: Performance Cards
    create_productivity_card(grid_frame, 1, 0, emp_id, cursor, colspan=2)
    create_predictions_card(grid_frame, 1, 2, emp_id, cursor)

    # Row 3: Recent Activity
    create_recent_activity_card(grid_frame, 2, 0, emp_id, cursor, colspan=3)


def create_salary_card(parent, row, col, emp_id, cursor):
    """Create salary overview card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="💰 Salary Overview",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        cursor.execute(
            "SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,)
        )
        result = cursor.fetchone()

        if result:
            salary, bonus, deductions = result
            salary = salary or 0
            bonus = bonus or 0
            deductions = deductions or 0
            net_salary = salary + bonus - deductions

            # Layout salary info
            info_frame = tk.Frame(content_frame, bg=theme["card"])
            info_frame.pack(fill="x")
            info_frame.grid_columnconfigure(1, weight=1)

            tk.Label(info_frame, text="Base:", bg=theme["card"], fg=theme["fg"]).grid(
                row=0, column=0, sticky="w"
            )
            tk.Label(
                info_frame, text=f"₹{salary:,.0f}", bg=theme["card"], fg=theme["button"]
            ).grid(row=0, column=1, sticky="e")

            tk.Label(info_frame, text="Bonus:", bg=theme["card"], fg=theme["fg"]).grid(
                row=1, column=0, sticky="w"
            )
            tk.Label(
                info_frame, text=f"₹{bonus:,.0f}", bg=theme["card"], fg=theme["success"]
            ).grid(row=1, column=1, sticky="e")

            tk.Label(
                info_frame, text="Deductions:", bg=theme["card"], fg=theme["fg"]
            ).grid(row=2, column=0, sticky="w")
            tk.Label(
                info_frame,
                text=f"₹{deductions:,.0f}",
                bg=theme["card"],
                fg=theme["error"],
            ).grid(row=2, column=1, sticky="e")

            # Separator
            tk.Frame(content_frame, bg=theme["fg"], height=1).pack(fill="x", pady=5)

            tk.Label(
                content_frame,
                text=f"Net: ₹{net_salary:,.0f}",
                font=("Arial", 12, "bold"),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(anchor="w")
        else:
            tk.Label(
                content_frame,
                text="No salary data available",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(content_frame, text=f"Error: {e}", bg=theme["card"], fg="red").pack()


def create_attendance_card(parent, row, col, emp_id, cursor):
    """Create attendance summary card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="📅 Attendance",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        # Get attendance stats
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time
            FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        result = cursor.fetchone()
        if result and result[0] > 0:
            total, on_time = result
            on_time_pct = (on_time / total * 100) if total > 0 else 0

            tk.Label(
                content_frame, text="Total Days:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                content_frame,
                text=f"{total}",
                font=("Arial", 16, "bold"),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(anchor="w", pady=(0, 5))

            tk.Label(
                content_frame, text="On-Time Rate:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            color = (
                theme["success"]
                if on_time_pct >= 90
                else theme["warning"] if on_time_pct >= 75 else theme["error"]
            )
            tk.Label(
                content_frame,
                text=f"{on_time_pct:.1f}%",
                font=("Arial", 16, "bold"),
                bg=theme["card"],
                fg=color,
            ).pack(anchor="w")
        else:
            tk.Label(
                content_frame,
                text="No attendance data yet",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(content_frame, text=f"Error: {e}", bg=theme["card"], fg="red").pack()


def create_status_card(parent, row, col, emp_id, cursor):
    """Create today's status card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="🕐 Today's Status",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT sign_in, sign_out FROM attendance WHERE emp_id=? AND date=?",
            (emp_id, today),
        )
        result = cursor.fetchone()

        if result and result[0]:
            sign_in_time = result[0]
            sign_out_time = result[1]

            tk.Label(
                content_frame, text="Sign In:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                content_frame,
                text=sign_in_time,
                font=("Arial", 12, "bold"),
                bg=theme["card"],
                fg=theme["success"],
            ).pack(anchor="w", pady=(0, 5))

            if sign_out_time:
                tk.Label(
                    content_frame, text="Sign Out:", bg=theme["card"], fg=theme["fg"]
                ).pack(anchor="w")
                tk.Label(
                    content_frame,
                    text=sign_out_time,
                    font=("Arial", 12, "bold"),
                    bg=theme["card"],
                    fg=theme["warning"],
                ).pack(anchor="w")
                tk.Label(
                    content_frame,
                    text="✅ Complete",
                    bg=theme["card"],
                    fg=theme["success"],
                ).pack(anchor="w", pady=(5, 0))
            else:
                tk.Label(
                    content_frame,
                    text="🔄 Working",
                    bg=theme["card"],
                    fg=theme["button"],
                ).pack(anchor="w", pady=(5, 0))
        else:
            tk.Label(
                content_frame,
                text="❌ Not signed in",
                bg=theme["card"],
                fg=theme["warning"],
            ).pack()

    except Exception as e:
        tk.Label(content_frame, text=f"Error: {e}", bg=theme["card"], fg="red").pack()


def create_productivity_card(parent, row, col, emp_id, cursor, colspan=1):
    """Create productivity overview card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(
        row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=10
    )

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="🎯 Productivity Overview",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        # Get comprehensive stats
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time,
                   AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                       THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                       ELSE NULL END) as avg_hours
            FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        result = cursor.fetchone()
        if result and result[0] > 0:
            total, on_time, avg_hours = result
            punctuality = (on_time / total * 100) if total > 0 else 0
            avg_hours = avg_hours or 0

            # Calculate overall score
            attendance_score = min(100, (total / 20) * 100)  # 20 days = 100%
            hours_score = min(100, (avg_hours / 8) * 100) if avg_hours > 0 else 0
            overall_score = (
                punctuality * 0.5 + attendance_score * 0.3 + hours_score * 0.2
            )

            # Layout metrics
            metrics_frame = tk.Frame(content_frame, bg=theme["card"])
            metrics_frame.pack(fill="x")
            metrics_frame.grid_columnconfigure(0, weight=1)
            metrics_frame.grid_columnconfigure(1, weight=1)
            metrics_frame.grid_columnconfigure(2, weight=1)

            # Overall score
            score_frame = tk.Frame(metrics_frame, bg=theme["card"])
            score_frame.grid(row=0, column=0, sticky="w")
            tk.Label(
                score_frame, text="Overall Score:", bg=theme["card"], fg=theme["fg"]
            ).pack()
            color = (
                theme["success"]
                if overall_score >= 80
                else theme["warning"] if overall_score >= 60 else theme["error"]
            )
            tk.Label(
                score_frame,
                text=f"{overall_score:.0f}%",
                font=("Arial", 16, "bold"),
                bg=theme["card"],
                fg=color,
            ).pack()

            # Punctuality
            punct_frame = tk.Frame(metrics_frame, bg=theme["card"])
            punct_frame.grid(row=0, column=1, sticky="w")
            tk.Label(
                punct_frame, text="Punctuality:", bg=theme["card"], fg=theme["fg"]
            ).pack()
            tk.Label(
                punct_frame,
                text=f"{punctuality:.0f}%",
                font=("Arial", 16, "bold"),
                bg=theme["card"],
                fg=theme["button"],
            ).pack()

            # Average hours
            hours_frame = tk.Frame(metrics_frame, bg=theme["card"])
            hours_frame.grid(row=0, column=2, sticky="w")
            tk.Label(
                hours_frame, text="Avg Hours:", bg=theme["card"], fg=theme["fg"]
            ).pack()
            tk.Label(
                hours_frame,
                text=f"{avg_hours:.1f}h",
                font=("Arial", 16, "bold"),
                bg=theme["card"],
                fg=theme["success"],
            ).pack()

        else:
            tk.Label(
                content_frame,
                text="No performance data available yet",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(content_frame, text=f"Error: {e}", bg=theme["card"], fg="red").pack()


def create_predictions_card(parent, row, col, emp_id, cursor):
    """Create ML predictions card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="🔮 Predictions",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    # Punctuality prediction
    prob, prob_msg = get_punctuality_probability(emp_id, cursor)
    if prob is not None:
        tk.Label(
            content_frame, text="On-Time Tomorrow:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            content_frame,
            text=f"{prob*100:.0f}%",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["success"] if prob > 0.8 else theme["warning"],
        ).pack(anchor="w", pady=(0, 5))
    else:
        tk.Label(
            content_frame, text="Punctuality:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            content_frame, text="No prediction", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w", pady=(0, 5))

    # Salary prediction
    salary_pred, salary_msg = get_predicted_salary_value(emp_id, cursor)
    if salary_pred is not None:
        tk.Label(
            content_frame, text="Predicted Salary:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            content_frame,
            text=f"₹{salary_pred:,.0f}",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["button"],
        ).pack(anchor="w")
    else:
        tk.Label(
            content_frame, text="Salary Forecast:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            content_frame, text="No prediction", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")


def create_recent_activity_card(parent, row, col, emp_id, cursor, colspan=1):
    """Create recent activity card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(
        row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=10
    )

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="📋 Recent Activity",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        cursor.execute(
            "SELECT date, sign_in, sign_out FROM attendance WHERE emp_id=? ORDER BY date DESC LIMIT 7",
            (emp_id,),
        )
        results = cursor.fetchall()

        if results:
            # Create header
            header_frame = tk.Frame(content_frame, bg=theme["card"])
            header_frame.pack(fill="x", pady=(0, 5))
            tk.Label(
                header_frame,
                text="Date",
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 9, "bold"),
                width=12,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                header_frame,
                text="Sign In",
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 9, "bold"),
                width=10,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                header_frame,
                text="Sign Out",
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 9, "bold"),
                width=10,
                anchor="w",
            ).pack(side="left")

            # Add separator
            tk.Frame(content_frame, bg=theme["fg"], height=1).pack(fill="x", pady=2)

            # Activity rows
            for date, sign_in, sign_out in results:
                activity_frame = tk.Frame(content_frame, bg=theme["card"])
                activity_frame.pack(fill="x", pady=1)

                tk.Label(
                    activity_frame,
                    text=date,
                    bg=theme["card"],
                    fg=theme["fg"],
                    font=("Arial", 9),
                    width=12,
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    activity_frame,
                    text=sign_in or "--",
                    bg=theme["card"],
                    fg=theme["fg"],
                    font=("Arial", 9),
                    width=10,
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    activity_frame,
                    text=sign_out or "--",
                    bg=theme["card"],
                    fg=theme["fg"],
                    font=("Arial", 9),
                    width=10,
                    anchor="w",
                ).pack(side="left")
        else:
            tk.Label(
                content_frame,
                text="No recent activity found",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(content_frame, text=f"Error: {e}", bg=theme["card"], fg="red").pack()
