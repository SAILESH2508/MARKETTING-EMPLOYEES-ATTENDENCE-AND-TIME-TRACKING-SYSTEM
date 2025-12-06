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
def show_performance_trends(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, create_scrollable_frame, get_db_data_safely
    from dashboard_modules.ml_functions import load_attendance_df
    """Show performance trends over time with ML predictions"""
    clear_content(frame)
    scrollable_frame, canvas = create_scrollable_frame(frame)
    frame = scrollable_frame  # Use scrollable frame as the parent
    tk.Label(frame, text="📈 Performance Trends Analysis", font=("Arial", 16, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
    
    if not SKLEARN_AVAILABLE:
        tk.Label(frame, text="Install scikit-learn and pandas for ML features", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    df, err = load_attendance_df(cursor)
    if err or df is None:
        tk.Label(frame, text=f"Error: {err}", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    emp_df = df[df['emp_id'] == emp_id].copy()
    if len(emp_df) < 2:
        tk.Label(frame, text="Not enough data for trend analysis", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    import pandas as pd
    emp_df['date_dt'] = pd.to_datetime(emp_df['date'])
    emp_df = emp_df.sort_values('date_dt')
    emp_df['day_num'] = (emp_df['date_dt'] - emp_df['date_dt'].min()).dt.days
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), facecolor=theme['bg'])
    
    # Sign-in time trend
    ax1.set_facecolor(theme['card'])
    ax1.plot(emp_df['day_num'], emp_df['sign_in_seconds']/3600, marker='o', color=theme['button'], linewidth=2)
    ax1.axhline(y=9, color='red', linestyle='--', label='9 AM threshold')
    ax1.set_title('Sign-In Time Trend', color=theme['fg'])
    ax1.set_ylabel('Hour of Day', color=theme['fg'])
    ax1.tick_params(colors=theme['fg'])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Rolling average punctuality
    ax2.set_facecolor(theme['card'])
    window = min(7, len(emp_df))
    emp_df['rolling_ontime'] = emp_df['on_time'].rolling(window=window, min_periods=1).mean() * 100
    ax2.plot(emp_df['day_num'], emp_df['rolling_ontime'], marker='s', color=theme['hover'], linewidth=2)
    ax2.set_title(f'{window}-Day Rolling On-Time %', color=theme['fg'])
    ax2.set_xlabel('Days Since First Record', color=theme['fg'])
    ax2.set_ylabel('On-Time %', color=theme['fg'])
    ax2.tick_params(colors=theme['fg'])
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
    plt.close(fig)

def show_work_patterns(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, create_scrollable_frame, get_db_data_safely
    from dashboard_modules.ml_functions import load_attendance_df
    """Analyze work patterns using clustering and statistics"""
    clear_content(frame)
    scrollable_frame, canvas = create_scrollable_frame(frame)
    frame = scrollable_frame  # Use scrollable frame as the parent
    tk.Label(frame, text="🧠 Work Pattern Analysis", font=("Arial", 16, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
    
    if not SKLEARN_AVAILABLE:
        tk.Label(frame, text="Install scikit-learn and pandas for ML features", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    df, err = load_attendance_df(cursor)
    if err or df is None:
        tk.Label(frame, text=f"Error: {err}", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    emp_df = df[df['emp_id'] == emp_id].copy()
    if len(emp_df) < 5:
        tk.Label(frame, text="Not enough data for pattern analysis (need 5+ records)", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    import pandas as pd
    emp_df['date_dt'] = pd.to_datetime(emp_df['date'])
    emp_df['day_name'] = emp_df['date_dt'].dt.day_name()
    
    # Create analysis frame
    analysis_frame = tk.Frame(frame, bg=theme['card'])
    analysis_frame.pack(fill='both', expand=True, padx=20, pady=10)
    
    # Day of week analysis
    tk.Label(analysis_frame, text="📅 Best & Worst Days:", font=("Arial", 13, "bold"), bg=theme['card'], fg=theme['fg']).pack(anchor='w', pady=5)
    
    day_stats = emp_df.groupby('day_name').agg({
        'on_time': 'mean',
        'sign_in_seconds': 'mean'
    }).round(2)
    
    if len(day_stats) > 0:
        best_day = day_stats['on_time'].idxmax()
        worst_day = day_stats['on_time'].idxmin()
        tk.Label(analysis_frame, text=f"✅ Best Day: {best_day} ({day_stats.loc[best_day, 'on_time']*100:.0f}% on-time)", 
                bg=theme['card'], fg=theme['fg'], font=("Arial", 11)).pack(anchor='w', padx=20)
        tk.Label(analysis_frame, text=f"❌ Worst Day: {worst_day} ({day_stats.loc[worst_day, 'on_time']*100:.0f}% on-time)", 
                bg=theme['card'], fg=theme['fg'], font=("Arial", 11)).pack(anchor='w', padx=20)
    
    # Average arrival time
    avg_arrival = emp_df['sign_in_seconds'].mean() / 3600
    tk.Label(analysis_frame, text=f"\n⏰ Average Arrival: {int(avg_arrival)}:{int((avg_arrival % 1) * 60):02d}", 
            font=("Arial", 13, "bold"), bg=theme['card'], fg=theme['fg']).pack(anchor='w', pady=5)
    
    # Consistency score
    std_dev = emp_df['sign_in_seconds'].std() / 3600
    consistency = max(0, 100 - (std_dev * 20))
    tk.Label(analysis_frame, text=f"🎯 Consistency Score: {consistency:.1f}/100", 
            font=("Arial", 13, "bold"), bg=theme['card'], fg=theme['fg']).pack(anchor='w', pady=5)
    tk.Label(analysis_frame, text=f"   (Lower variation = higher consistency)", 
            font=("Arial", 9), bg=theme['card'], fg=theme['fg']).pack(anchor='w', padx=20)
    
    # Recent trend
    if len(emp_df) >= 10:
        recent = emp_df.tail(5)['on_time'].mean()
        older = emp_df.head(5)['on_time'].mean()
        trend = "📈 Improving" if recent > older else "📉 Declining" if recent < older else "➡️ Stable"
        tk.Label(analysis_frame, text=f"\n📊 Recent Trend: {trend}", 
                font=("Arial", 13, "bold"), bg=theme['card'], fg=theme['fg']).pack(anchor='w', pady=5)

def show_productivity_score(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    """Calculate and display comprehensive productivity score with detailed metrics"""
    clear_content(frame)
    tk.Label(frame, text="🎯 Detailed Productivity Analysis", font=("Arial", 18, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(pady=15)
    
    query = """SELECT COUNT(*),
                      SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                      SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END),
                      AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                          THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                          ELSE NULL END),
                      MIN(sign_in),
                      MAX(sign_in),
                      COUNT(DISTINCT date)
               FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL"""
    
    row, err = get_db_data_safely(query, (emp_id,), fetch_all=False)
    if err or not row:
        tk.Label(frame, text="No data available", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    total_days, on_time_days, late_days, avg_hours, earliest, latest, unique_days = row
    if total_days == 0:
        tk.Label(frame, text="No attendance records found", bg=theme["bg"], fg=theme["fg"]).pack(pady=20)
        return
    
    # Calculate scores
    punctuality_score = (on_time_days / total_days) * 100 if total_days > 0 else 0
    attendance_score = min(100, (total_days / 20) * 100)
    work_hours_score = min(100, (avg_hours / 8) * 100) if avg_hours else 0
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
    
    # Main container
    main_container = tk.Frame(frame, bg=theme['bg'])
    main_container.pack(fill='both', expand=True, padx=20, pady=10)
    
    # Left side - Score display
    left_frame = tk.Frame(main_container, bg=theme['card'], width=400)
    left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
    
    tk.Label(left_frame, text=f"{productivity_score:.1f}", font=("Arial", 60, "bold"), 
            bg=theme['card'], fg=theme['button']).pack(pady=(30, 5))
    tk.Label(left_frame, text="/100", font=("Arial", 20), 
            bg=theme['card'], fg=theme['fg']).pack()
    tk.Label(left_frame, text="Overall Productivity", font=("Arial", 14), 
            bg=theme['card'], fg=theme['fg']).pack(pady=5)
    tk.Label(left_frame, text=f"Grade: {grade}", font=("Arial", 24, "bold"), 
            bg=theme['card'], fg=grade_color).pack(pady=15)
    
    # Right side - Detailed breakdown
    right_frame = tk.Frame(main_container, bg=theme['card'])
    right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
    
    tk.Label(right_frame, text="📊 Detailed Metrics", font=("Arial", 14, "bold"), 
            bg=theme['card'], fg=theme['fg']).pack(anchor='w', padx=15, pady=(15, 10))
    
    # Detailed metrics with progress bars
    metrics = [
        ("⏰ Punctuality Score", punctuality_score, f"{on_time_days} on-time, {late_days} late", theme['button']),
        ("📅 Attendance Score", attendance_score, f"{total_days} total days recorded", "#66BB6A"),
        ("⏱️ Work Hours Score", work_hours_score, f"{avg_hours:.1f} hrs/day average" if avg_hours else "N/A", "#FFA726")
    ]
    
    for title, score, detail, color in metrics:
        metric_frame = tk.Frame(right_frame, bg=theme['card'])
        metric_frame.pack(fill='x', padx=15, pady=8)
        
        tk.Label(metric_frame, text=title, bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 11, "bold")).pack(anchor='w')
        tk.Label(metric_frame, text=f"{score:.1f}%", bg=theme['card'], fg=color, 
                font=("Arial", 16, "bold")).pack(anchor='w')
        tk.Label(metric_frame, text=detail, bg=theme['card'], fg=theme['fg'], 
                font=("Arial", 9)).pack(anchor='w', pady=(0, 3))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(f"{title}.Horizontal.TProgressbar", foreground=color, background=color, troughcolor=theme['bg'])
        pb = ttk.Progressbar(metric_frame, orient='horizontal', length=450, mode='determinate', 
                            style=f"{title}.Horizontal.TProgressbar")
        pb['value'] = score
        pb.pack(fill='x', pady=2)
    


def auto_train_ml_models(cursor, emp_id):
    from dashboard_modules.ml_functions import train_punctuality_model, train_salary_predictor, train_anomaly_detector
    """Automatically train all ML models in background on dashboard load"""
    if not SKLEARN_AVAILABLE:
        return
    
    def worker():
        try:
            db_conn = sqlite3.connect("attendance_system.db")
            db_cursor = db_conn.cursor()
            
            # Silently train all models
            train_punctuality_model(db_cursor, return_eval=False, silent=True)
            train_salary_predictor(db_cursor, silent=True)
            train_anomaly_detector(db_cursor, silent=True)
            
            db_conn.close()
        except Exception as e:
            print(f"Auto ML training error: {e}")
    
    # Run in background thread
    t = threading.Thread(target=worker, daemon=True)
    t.start()

# ------------------
# Dashboard
