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
def get_predicted_salary_value(emp_id, cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely
    path = os.path.join(MODEL_DIR, "salary_reg.pkl")
    if os.path.exists(path) and SKLEARN_AVAILABLE:
        try:
            with open(path, "rb") as f:
                model = pickle.load(f)
            row, err = get_db_data_safely("SELECT bonus, deductions FROM salary WHERE emp_id=?", (emp_id,), fetch_all=False)
            if err:
                return None, f"DB access error: {err}"
            if not row:
                return None, "No salary row to compute prediction."
            bonus, deductions = row
            bonus = bonus or 0
            deductions = deductions or 0
            import pandas as pd
            X_predict = pd.DataFrame([[bonus, deductions]], columns=['bonus', 'deductions'])
            pred = model.predict(X_predict)[0]
            return pred, None
        except Exception as e:
            return None, f"Error using salary model: {e}"
    else:
        r, err = get_db_data_safely("SELECT salary FROM salary WHERE emp_id=?", (emp_id,), fetch_all=False)
        if err:
             return None, f"DB access error: {err}"
        if r and r[0]:
            return r[0], "No model, showing actual salary"
        if not SKLEARN_AVAILABLE:
            return None, "Install scikit-learn/pandas to enable model predictions."
        return None, "Train salary model (use ML controls) to get predictions."

def get_punctuality_probability(emp_id, cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely
    from dashboard_modules.ml_functions import load_attendance_df
    path = os.path.join(MODEL_DIR, "punctuality.pkl")
    if os.path.exists(path) and SKLEARN_AVAILABLE:
        try:
            with open(path, "rb") as f:
                clf = pickle.load(f)
            conn = sqlite3.connect("attendance_system.db")
            temp_cursor = conn.cursor()
            df, err = load_attendance_df(temp_cursor)
            conn.close()
            if err or df is None:
                return None, err or "No attendance data"
            import pandas as pd
            emp_mean = df[df['emp_id'] == emp_id]['sign_in_seconds'].mean()
            if pd.isna(emp_mean):
                emp_mean = df['sign_in_seconds'].mean()
            dayofweek = datetime.now().weekday()
            X = pd.DataFrame([[dayofweek, emp_mean]], columns=['dayofweek', 'mean_sign_in'])
            prob_on_time = clf.predict_proba(X)[0][1] if hasattr(clf, "predict_proba") else float(clf.predict(X)[0])
            return float(prob_on_time), None
        except Exception as e:
            return None, f"Error using punctuality model: {e}"
    else:
        query = """SELECT COUNT(*),
                            SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END)
                      FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
                    """
        row, err = get_db_data_safely(query, (emp_id,), fetch_all=False)
        if err:
            return None, f"DB access error: {err}"
        if not row:
            return None, "No attendance data"
        total, on_time = row
        if total == 0:
            return None, "No sign-in data"
        return (on_time / total), "Heuristic (Past Performance)"

def compute_perfection_score(emp_id, cursor):
    from dashboard_modules.ui_helpers import get_db_data_safely
    query = """SELECT COUNT(*),
                        SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END)
                  FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
                """
    row, err = get_db_data_safely(query, (emp_id,), fetch_all=False)
    if err:
        return 0.0
    if not row:
        return 0.0
    total, on_time = row
    if not total:
        return 0.0
    return (on_time / total) if total else 0.0

def refresh_summary(frame, emp_id, cursor):
    show_default_summary(frame, emp_id, cursor)

def show_default_summary(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, create_scrollable_frame, rounded_card, ToolTip, get_db_data_safely
    global ml_training_in_progress, ml_trained_this_session
    
    clear_content(frame)
    
    # Create scrollable frame
    scrollable_frame, canvas = create_scrollable_frame(frame)
    
    # Main container inside scrollable frame
    container = tk.Frame(scrollable_frame, bg=theme['bg'])
    container.pack(fill='both', expand=True, padx=12, pady=12)
    top = tk.Frame(container, bg=theme['bg'])
    top.pack(fill='x')

    def place_card(parent, title, build_body_fn, hint, width=320, height=140):
        c = rounded_card(parent, width=width, height=height, radius=14, bg=theme['card'])
        c.pack(side='left', padx=10)
        c.create_text(30, 24, anchor='w', text=title, fill=theme['fg'], font=("Arial", 12, 'bold'))
        inner = tk.Frame(c, bg=theme['card'])
        inner.pack(fill='both', expand=True, padx=10, pady=(4, 10))
        c.create_window(10, 48, anchor='nw', window=inner, width=width-30, height=height-60)
        try:
            build_body_fn(inner)
        except Exception as e:
            tk.Label(inner, text=f"Error building card: {e}", bg=theme['card'], fg=theme['fg']).pack()
        ToolTip(c, hint)
        return c

    def build_salary(inner):
        row, err = get_db_data_safely("SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,), fetch_all=False)
        if err:
            txt = f"DB Error: {err}"
        elif row:
            salary, bonus, deductions = row
            salary = salary if salary is not None else 0.0
            bonus = bonus if bonus is not None else 0.0
            deductions = deductions if deductions is not None else 0.0
            txt = f"💼 Base: {salary:.2f}\n➕ Bonus: {bonus:.2f}\n➖ Deductions: {deductions:.2f}"
        else:
            txt = "No salary data"
        tk.Label(inner, text=txt, bg=theme['card'], fg=theme['fg'], justify='left', font=("Arial", 11)).pack(anchor='w')

    place_card(top, "💼 Current Salary", build_salary, "Stored salary information from the database.")

    def build_pred(inner):
        pred_val, pred_msg = get_predicted_salary_value(emp_id, cursor)
        if pred_val is not None and not isinstance(pred_msg, str):
            tk.Label(inner, text=f"🔮 Predicted base: {pred_val:.2f}", bg=theme['card'], fg=theme['fg'], font=("Arial", 12)).pack(anchor='w')
        else:
            tk.Label(inner, text=pred_msg, bg=theme['card'], fg=theme['fg'], font=("Arial", 10), wraplength=280, justify='left').pack(anchor='w')

    place_card(top, "🔮 Predicted Salary", build_pred, "Model-based prediction (train model in ML panel).")

    def build_prob(inner):
        prob, pmsg = get_punctuality_probability(emp_id, cursor)
        if prob is not None:
            tk.Label(inner, text=f"{prob*100:.1f}% chance on-time tomorrow", bg=theme['card'], fg=theme['fg'], font=("Arial", 11)).pack(anchor='w')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Red.Horizontal.TProgressbar", foreground=theme['hover'], background=theme['button'])
            pb = ttk.Progressbar(inner, orient='horizontal', length=220, mode='determinate', style="Red.Horizontal.TProgressbar")
            pb['value'] = prob*100
            pb.pack(pady=8, anchor='w')
        else:
            tk.Label(inner, text=pmsg, bg=theme['card'], fg=theme['fg'], font=("Arial", 10), wraplength=280, justify='left').pack(anchor='w')

    place_card(top, "⏱️ On-time Probability", build_prob, "Probability estimate from model or heuristic.")

    def build_perf(inner):
        perf_pct = compute_perfection_score(emp_id, cursor)
        tk.Label(inner, text=f"{perf_pct*100:.1f}% on-time (overall)", bg=theme['card'], fg=theme['fg'], font=("Arial", 11)).pack(anchor='w')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Blue.Horizontal.TProgressbar", foreground=theme['button'], background=theme['hover'])
        pb2 = ttk.Progressbar(inner, orient='horizontal', length=220, mode='determinate', style="Blue.Horizontal.TProgressbar")
        pb2['value'] = perf_pct*100
        pb2.pack(pady=8, anchor='w')

    place_card(top, "🏅 Perfection Score", build_perf, "Ratio of on-time sign-ins to total sign-ins.")

    # Second row for productivity score
    top2 = tk.Frame(container, bg=theme['bg'])
    top2.pack(fill='x', pady=(10, 0))

    def build_productivity(inner):
        query = """SELECT COUNT(*),
                          SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                          SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END),
                          AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                              THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                              ELSE NULL END),
                          MIN(sign_in),
                          MAX(sign_in)
                   FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL"""
        
        row, err = get_db_data_safely(query, (emp_id,), fetch_all=False)
        if err or not row or row[0] == 0:
            tk.Label(inner, text="No data available", bg=theme['card'], fg=theme['fg'], font=("Arial", 14)).pack(anchor='w')
            return
        
        total_days, on_time_days, late_days, avg_hours, earliest_time, latest_time = row
        
        # Calculate scores
        punctuality_score = (on_time_days / total_days) * 100 if total_days > 0 else 0
        attendance_score = min(100, (total_days / 20) * 100)
        work_hours_score = min(100, (avg_hours / 8) * 100) if avg_hours else 0
        
        # Overall productivity score (weighted average)
        productivity_score = (punctuality_score * 0.4 + attendance_score * 0.3 + work_hours_score * 0.3)
        
        # Grade and color
        if productivity_score >= 95:
            grade, grade_color = "A+", "#4CAF50"
        elif productivity_score >= 90:
            grade, grade_color = "A", "#66BB6A"
        elif productivity_score >= 85:
            grade, grade_color = "B+", "#FFA726"
        elif productivity_score >= 80:
            grade, grade_color = "B", "#FF9800"
        elif productivity_score >= 70:
            grade, grade_color = "C", "#FF7043"
        else:
            grade, grade_color = "D", "#F44336"
        
        # Main score display
        score_label = tk.Label(inner, text=f"{productivity_score:.1f}", bg=theme['card'], fg=theme['button'], font=("Arial", 38, "bold"))
        score_label.pack(anchor='center', pady=(5, 0))
        
        out_of_label = tk.Label(inner, text="/100", bg=theme['card'], fg=theme['fg'], font=("Arial", 14))
        out_of_label.pack(anchor='center')
        
        grade_label = tk.Label(inner, text=f"Grade: {grade}", bg=theme['card'], fg=grade_color, font=("Arial", 15, "bold"))
        grade_label.pack(anchor='center', pady=(5, 8))
        
        # Detailed breakdown with progress bars
        details_frame = tk.Frame(inner, bg=theme['card'])
        details_frame.pack(fill='x', padx=15, pady=(5, 0))
        
        # Punctuality detail
        punct_frame = tk.Frame(details_frame, bg=theme['card'])
        punct_frame.pack(fill='x', pady=2)
        tk.Label(punct_frame, text=f"⏰ Punctuality: {punctuality_score:.0f}%", bg=theme['card'], fg=theme['fg'], font=("Arial", 9, "bold")).pack(anchor='w')
        tk.Label(punct_frame, text=f"   {on_time_days} on-time / {late_days} late", bg=theme['card'], fg=theme['fg'], font=("Arial", 8)).pack(anchor='w')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Punct.Horizontal.TProgressbar", foreground=theme['button'], background=theme['button'], troughcolor=theme['bg'])
        pb1 = ttk.Progressbar(punct_frame, orient='horizontal', length=380, mode='determinate', style="Punct.Horizontal.TProgressbar")
        pb1['value'] = punctuality_score
        pb1.pack(fill='x', pady=2)
        
        # Attendance detail
        attend_frame = tk.Frame(details_frame, bg=theme['card'])
        attend_frame.pack(fill='x', pady=2)
        tk.Label(attend_frame, text=f"📅 Attendance: {attendance_score:.0f}%", bg=theme['card'], fg=theme['fg'], font=("Arial", 9, "bold")).pack(anchor='w')
        tk.Label(attend_frame, text=f"   {total_days} days recorded", bg=theme['card'], fg=theme['fg'], font=("Arial", 8)).pack(anchor='w')
        style.configure("Attend.Horizontal.TProgressbar", foreground="#66BB6A", background="#66BB6A", troughcolor=theme['bg'])
        pb2 = ttk.Progressbar(attend_frame, orient='horizontal', length=380, mode='determinate', style="Attend.Horizontal.TProgressbar")
        pb2['value'] = attendance_score
        pb2.pack(fill='x', pady=2)
        
        # Work hours detail
        hours_frame = tk.Frame(details_frame, bg=theme['card'])
        hours_frame.pack(fill='x', pady=2)
        tk.Label(hours_frame, text=f"⏱️ Work Hours: {work_hours_score:.0f}%", bg=theme['card'], fg=theme['fg'], font=("Arial", 9, "bold")).pack(anchor='w')
        avg_hrs_text = f"{avg_hours:.1f} hrs/day avg" if avg_hours else "N/A"
        tk.Label(hours_frame, text=f"   {avg_hrs_text}", bg=theme['card'], fg=theme['fg'], font=("Arial", 8)).pack(anchor='w')
        style.configure("Hours.Horizontal.TProgressbar", foreground="#FFA726", background="#FFA726", troughcolor=theme['bg'])
        pb3 = ttk.Progressbar(hours_frame, orient='horizontal', length=380, mode='determinate', style="Hours.Horizontal.TProgressbar")
        pb3['value'] = work_hours_score
        pb3.pack(fill='x', pady=2)

    place_card(top2, "🎯 Productivity Score", build_productivity, "Comprehensive score based on punctuality, attendance, and work hours.", width=580, height=290)
    
    # Add Quick Stats next to Productivity Score
    def build_quick_stats_card(inner):
        tk.Label(inner, text="📊 Quick Stats", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 8))
        
        # Get today's status
        today = datetime.now().strftime("%Y-%m-%d")
        today_query = """SELECT sign_in, sign_out FROM attendance WHERE emp_id=? AND date=?"""
        today_data, _ = get_db_data_safely(today_query, (emp_id, today), fetch_all=False)
        
        # Today's status
        if today_data and today_data[0]:
            sign_in_time = today_data[0]
            sign_out_time = today_data[1] if today_data[1] else "Not yet"
            status_color = "#4CAF50" if sign_in_time <= "09:00:00" else "#F44336"
            
            tk.Label(inner, text="Today:", bg=theme['card'], fg=theme['fg'], 
                    font=("Arial", 9, "bold")).pack(anchor='w')
            tk.Label(inner, text=f"✅ In: {sign_in_time}", bg=theme['card'], 
                    fg=status_color, font=("Arial", 9)).pack(anchor='w', pady=2)
            tk.Label(inner, text=f"🚪 Out: {sign_out_time}", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
        else:
            tk.Label(inner, text="⚠️ Not signed in today", bg=theme['card'], 
                    fg="#F44336", font=("Arial", 9, "bold")).pack(anchor='w', pady=10)
        
        # Week summary
        week_query = """SELECT COUNT(*), 
                              SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END)
                       FROM attendance 
                       WHERE emp_id=? AND date >= date('now', '-7 days') AND sign_in IS NOT NULL"""
        week_data, _ = get_db_data_safely(week_query, (emp_id,), fetch_all=False)
        
        if week_data and week_data[0] > 0:
            total, on_time = week_data
            rate = (on_time / total) * 100 if total > 0 else 0
            rate_color = "#4CAF50" if rate >= 80 else "#FFA726" if rate >= 60 else "#F44336"
            
            tk.Label(inner, text="\nThis Week:", bg=theme['card'], fg=theme['fg'], 
                    font=("Arial", 9, "bold")).pack(anchor='w', pady=(8, 2))
            tk.Label(inner, text=f"📊 {total} days worked", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
            tk.Label(inner, text=f"⏰ {rate:.0f}% on-time", bg=theme['card'], 
                    fg=rate_color, font=("Arial", 9, "bold")).pack(anchor='w', pady=2)
    
    place_card(top2, "📊 Quick Stats", build_quick_stats_card, "Today's status and weekly summary", width=380, height=290)
    
    # Add Performance next to Quick Stats
    def build_performance_card(inner):
        tk.Label(inner, text="📈 Performance", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 8))
        
        # Overall stats
        overall_query = """SELECT COUNT(*),
                                 SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                                 COUNT(DISTINCT date),
                                 MIN(sign_in),
                                 MAX(sign_in)
                          FROM attendance 
                          WHERE emp_id=? AND sign_in IS NOT NULL"""
        overall_data, _ = get_db_data_safely(overall_query, (emp_id,), fetch_all=False)
        
        if overall_data and overall_data[0] > 0:
            total_records, on_time_total, unique_days, earliest, latest = overall_data
            on_time_rate = (on_time_total / total_records * 100) if total_records > 0 else 0
            
            rate_color = "#4CAF50" if on_time_rate >= 80 else "#FFA726" if on_time_rate >= 60 else "#F44336"
            
            tk.Label(inner, text="Overall:", bg=theme['card'], fg=theme['fg'], 
                    font=("Arial", 9, "bold")).pack(anchor='w')
            tk.Label(inner, text=f"⭐ {on_time_rate:.1f}% on-time", bg=theme['card'], 
                    fg=rate_color, font=("Arial", 9, "bold")).pack(anchor='w', pady=2)
            tk.Label(inner, text=f"📊 {unique_days} unique days", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
            tk.Label(inner, text=f"📝 {total_records} records", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
            
            # Additional stats
            tk.Label(inner, text="\nTimes:", bg=theme['card'], fg=theme['fg'], 
                    font=("Arial", 9, "bold")).pack(anchor='w', pady=(8, 2))
            tk.Label(inner, text=f"🌅 Earliest: {earliest if earliest else 'N/A'}", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 8)).pack(anchor='w', pady=1)
            tk.Label(inner, text=f"🌆 Latest: {latest if latest else 'N/A'}", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 8)).pack(anchor='w', pady=1)
            
            # Streak
            streak_query = """SELECT COUNT(*)
                             FROM attendance 
                             WHERE emp_id=? 
                             AND date >= date('now', '-5 days')
                             AND TIME(sign_in) <= '09:00:00'
                             AND sign_in IS NOT NULL"""
            streak_data, _ = get_db_data_safely(streak_query, (emp_id,), fetch_all=False)
            
            if streak_data:
                streak = streak_data[0]
                streak_color = "#4CAF50" if streak >= 4 else "#FFA726" if streak >= 2 else "#F44336"
                tk.Label(inner, text=f"\n🔥 Streak: {streak}/5 days", bg=theme['card'], 
                        fg=streak_color, font=("Arial", 9, "bold")).pack(anchor='w', pady=(8, 2))
        else:
            tk.Label(inner, text="No data available", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=10)
    
    place_card(top2, "📈 Performance", build_performance_card, "Overall performance metrics", width=380, height=290)

    # Third row - ML Insights Cards (moved here to appear before Recent Activity)
    top3 = tk.Frame(container, bg=theme['bg'])
    top3.pack(fill='x', pady=(10, 0))
    
    def build_ml_status(inner):
        tk.Label(inner, text="🤖 ML Models", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        
        models = [
            ("Punctuality", "punctuality.pkl"),
            ("Salary", "salary_reg.pkl"),
            ("Anomaly", "anomaly.pkl")
        ]
        
        for model_name, file_name in models:
            exists = os.path.exists(os.path.join(MODEL_DIR, file_name))
            status_icon = "✅" if exists else "⏳"
            color = "#4CAF50" if exists else "#FFA726"
            
            tk.Label(inner, text=f"{status_icon} {model_name}", bg=theme['card'], 
                    fg=color, font=("Arial", 9)).pack(anchor='w', pady=2)
    
    place_card(top3, "🤖 ML Status", build_ml_status, "Machine Learning models status", width=320, height=140)
    
    def build_predictions(inner):
        tk.Label(inner, text="🔮 Predictions", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Punctuality prediction
        prob, _ = get_punctuality_probability(emp_id, cursor)
        if prob is not None:
            pred_color = "#4CAF50" if prob >= 0.7 else "#FFA726" if prob >= 0.5 else "#F44336"
            tk.Label(inner, text=f"⏰ On-time: {prob*100:.0f}%", bg=theme['card'], 
                    fg=pred_color, font=("Arial", 9, "bold")).pack(anchor='w', pady=2)
        
        # Salary prediction
        pred_val, _ = get_predicted_salary_value(emp_id, cursor)
        if pred_val is not None and not isinstance(pred_val, str):
            tk.Label(inner, text=f"💰 Salary: ₹{pred_val:.0f}", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
        
        # Performance score
        perf = compute_perfection_score(emp_id, cursor)
        perf_color = "#4CAF50" if perf >= 0.8 else "#FFA726" if perf >= 0.6 else "#F44336"
        tk.Label(inner, text=f"📊 Score: {perf*100:.0f}%", bg=theme['card'], 
                fg=perf_color, font=("Arial", 9)).pack(anchor='w', pady=2)
    
    place_card(top3, "🔮 Predictions", build_predictions, "ML-powered predictions", width=320, height=140)
    
    def build_insights(inner):
        tk.Label(inner, text="💡 Insights", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Get recent performance
        query = """SELECT COUNT(*), 
                          SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END)
                   FROM attendance 
                   WHERE emp_id=? AND date >= date('now', '-7 days') AND sign_in IS NOT NULL"""
        week_data, _ = get_db_data_safely(query, (emp_id,), fetch_all=False)
        
        if week_data and week_data[0] > 0:
            total, on_time = week_data
            rate = (on_time / total) * 100 if total > 0 else 0
            
            if rate >= 80:
                insight = "🌟 Excellent!"
                color = "#4CAF50"
            elif rate >= 60:
                insight = "👍 Good"
                color = "#FFA726"
            else:
                insight = "⚠️ Improve"
                color = "#F44336"
            
            tk.Label(inner, text=insight, bg=theme['card'], fg=color, 
                    font=("Arial", 9, "bold")).pack(anchor='w', pady=2)
            tk.Label(inner, text=f"7 days: {rate:.0f}%", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 8)).pack(anchor='w', pady=2)
        
        # Training status
        if ml_trained_this_session:
            tk.Label(inner, text="✅ Models ready", bg=theme['card'], 
                    fg="#4CAF50", font=("Arial", 8)).pack(anchor='w', pady=2)
        elif ml_training_in_progress:
            tk.Label(inner, text="⏳ Training...", bg=theme['card'], 
                    fg="#FFA726", font=("Arial", 8)).pack(anchor='w', pady=2)
    
    place_card(top3, "💡 Insights", build_insights, "AI-powered insights", width=320, height=140)
    
    def build_monthly_summary(inner):
        tk.Label(inner, text="📅 This Month", bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Get this month's data
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        month_query = """SELECT COUNT(*), 
                               SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                               AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                                   THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                                   ELSE NULL END)
                        FROM attendance 
                        WHERE emp_id=? AND date >= ? AND sign_in IS NOT NULL"""
        month_data, _ = get_db_data_safely(month_query, (emp_id, month_start), fetch_all=False)
        
        if month_data and month_data[0] > 0:
            days, on_time, avg_hrs = month_data
            on_time_pct = (on_time / days * 100) if days > 0 else 0
            
            tk.Label(inner, text=f"📊 {days} days worked", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
            
            color = "#4CAF50" if on_time_pct >= 80 else "#FFA726" if on_time_pct >= 60 else "#F44336"
            tk.Label(inner, text=f"⏰ {on_time_pct:.0f}% on-time", bg=theme['card'], 
                    fg=color, font=("Arial", 9, "bold")).pack(anchor='w', pady=2)
            
            if avg_hrs:
                tk.Label(inner, text=f"⏱️ {avg_hrs:.1f} hrs/day", bg=theme['card'], 
                        fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=2)
        else:
            tk.Label(inner, text="No data this month", bg=theme['card'], 
                    fg=theme['fg'], font=("Arial", 9)).pack(anchor='w', pady=10)
    
    place_card(top3, "📅 Monthly", build_monthly_summary, "This month's summary", width=320, height=140)

    # Recent Activity Section (Full Width)
    activity_container = tk.Frame(container, bg=theme['bg'])
    activity_container.pack(fill='x', pady=(20, 0))
    
    tk.Label(activity_container, text="📋 Recent Activity", bg=theme['bg'], fg=theme['fg'], font=("Arial", 14, 'bold')).pack(anchor='w', pady=(0, 10))
    
    activity_frame = tk.Frame(activity_container, bg=theme['card'])
    activity_frame.pack(fill='x')
    
    # Get recent attendance records
    recent_query = """SELECT date, sign_in, sign_out 
                      FROM attendance 
                      WHERE emp_id=? 
                      ORDER BY date DESC 
                      LIMIT 5"""
    recent_data, err = get_db_data_safely(recent_query, (emp_id,), fetch_all=True)
    
    if recent_data and not err:
        # Header
        header_frame = tk.Frame(activity_frame, bg=theme['card'])
        header_frame.pack(fill='x', padx=15, pady=5)
        tk.Label(header_frame, text="Date", width=15, anchor='w', bg=theme['card'], fg=theme['fg'], font=("Arial", 10, 'bold')).pack(side='left')
        tk.Label(header_frame, text="Sign In", width=20, anchor='w', bg=theme['card'], fg=theme['fg'], font=("Arial", 10, 'bold')).pack(side='left')
        tk.Label(header_frame, text="Sign Out", width=20, anchor='w', bg=theme['card'], fg=theme['fg'], font=("Arial", 10, 'bold')).pack(side='left')
        
        tk.Frame(activity_frame, bg=theme['fg'], height=1).pack(fill='x', padx=10)

        for date, sign_in, sign_out in recent_data:
            record_frame = tk.Frame(activity_frame, bg=theme['card'])
            record_frame.pack(fill='x', padx=15, pady=8)
            
            # Date
            tk.Label(record_frame, text=date, width=15, anchor='w', bg=theme['card'], fg=theme['fg'], 
                    font=("Arial", 10)).pack(side='left')
            
            # Sign in time with status
            if sign_in:
                h, m, s = sign_in.split(':')
                hour = int(h)
                status_icon = "✅" if hour < 9 or (hour == 9 and int(m) == 0) else "⚠️"
                tk.Label(record_frame, text=f"{status_icon} {sign_in}", width=20, anchor='w', bg=theme['card'], 
                        fg=theme['fg'], font=("Arial", 10)).pack(side='left')
            else:
                tk.Label(record_frame, text="--:--:--", width=20, anchor='w', bg=theme['card'], 
                        fg=theme['fg'], font=("Arial", 10)).pack(side='left')
            
            # Sign out time
            if sign_out:
                tk.Label(record_frame, text=f"🚪 {sign_out}", width=20, anchor='w', bg=theme['card'], 
                        fg=theme['fg'], font=("Arial", 10)).pack(side='left')
            else:
                tk.Label(record_frame, text="Not signed out", width=20, anchor='w', bg=theme['card'], 
                        fg="#FFA726", font=("Arial", 10, "italic")).pack(side='left')
    else:
        tk.Label(activity_frame, text="No recent activity found.", bg=theme['card'], 
                fg=theme['fg'], font=("Arial", 10)).pack(pady=20)



# ------------------
# NEW ML FEATURES
