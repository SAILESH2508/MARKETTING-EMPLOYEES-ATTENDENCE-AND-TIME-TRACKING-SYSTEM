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
# This avoids circular import issues

# ------------------
def employee_dashboard(root, emp_id, name, cursor, conn):
    # Import required functions from other modules
    from dashboard_modules.ui_helpers import fade_in, update_theme
    from dashboard_modules.summary_functions import show_default_summary, refresh_summary
    from dashboard_modules.chart_functions import show_heatmap, show_face_log, show_leaderboard, show_salary_pie, show_attendance_bar
    from dashboard_modules.analytics_functions import show_performance_trends, show_work_patterns, show_productivity_score, auto_train_ml_models
    from dashboard_modules.ml_functions import run_anomaly_scan
    from dashboard_modules.action_functions import sign_in, sign_out, auto_reminder
    
    global content 
    dashboard = tk.Toplevel(root)
    dashboard.title(f"Employee Dashboard - {name}")
    dashboard.geometry("1400x800")
    
    # Proper cleanup function to prevent Tkinter errors
    def on_closing():
        try:
            # Unbind all events first to prevent callback errors
            dashboard.protocol("WM_DELETE_WINDOW", lambda: None)
        except:
            pass
        try:
            # Close database connection if needed
            if conn:
                conn.close()
        except:
            pass
        try:
            # Quit the mainloop before destroying
            dashboard.quit()
        except:
            pass
        try:
            # Destroy dashboard first
            dashboard.destroy()
        except:
            pass
        try:
            # Then destroy root
            root.destroy()
        except:
            pass
    
    dashboard.protocol("WM_DELETE_WINDOW", on_closing)
    dashboard.configure(bg=theme["bg"])
    dashboard.attributes("-alpha", 0.0)
    fade_in(dashboard)

    def toggle_theme_update():
        global theme
        theme = LIGHT_MODE if theme == DARK_MODE else DARK_MODE
        update_theme(dashboard)

    top_bar = tk.Frame(dashboard, bg=theme["bg"]) 
    top_bar.pack(fill='x', pady=(5, 0))
    
    # Left side - Employee name with welcome message
    name_frame = tk.Frame(top_bar, bg=theme["bg"])
    name_frame.pack(side='left', padx=15, pady=8)
    tk.Label(name_frame, text=f"Welcome, {name}!", font=("Arial", 24, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(anchor='w')
    tk.Label(name_frame, text=f"ID: {emp_id}", font=("Arial", 11), bg=theme["bg"], fg=theme["fg"]).pack(anchor='w')
    
    # Right side - Action buttons
    tk.Button(top_bar, text="🌗 Toggle Mode", command=toggle_theme_update, bg=theme["button"], fg=theme["fg"], font=BUTTON_FONT).pack(side='right', padx=5)
    tk.Button(top_bar, text="🔄 Refresh", command=lambda: refresh_summary(content, emp_id, cursor), bg=theme["button"], fg=theme["fg"], font=BUTTON_FONT).pack(side='right', padx=5)
    tk.Button(top_bar, text="🚪 Logout", command=on_closing, bg=theme["button"], fg=theme["fg"], font=BUTTON_FONT).pack(side='right', padx=5)

    # Quick action buttons
    action_bar = tk.Frame(dashboard, bg=theme["bg"])
    action_bar.pack(fill='x', padx=10, pady=5)
    tk.Button(action_bar, text="✅ Sign In", command=lambda: sign_in(emp_id, name, cursor, conn), 
             bg=theme["button"], fg=theme["fg"], font=("Arial", 11), width=12).pack(side='left', padx=5)
    tk.Button(action_bar, text="❌ Sign Out", command=lambda: sign_out(emp_id, cursor, conn), 
             bg=theme["button"], fg=theme["fg"], font=("Arial", 11), width=12).pack(side='left', padx=5)
    
    # Create tabbed interface
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TNotebook', background=theme['bg'], borderwidth=0)
    style.configure('TNotebook.Tab', background=theme['card'], foreground=theme['fg'], 
                   padding=[20, 10], font=('Arial', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', theme['button'])], 
             foreground=[('selected', theme['fg'])])
    
    notebook = ttk.Notebook(dashboard)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)
    
    # Create tabs
    tab_dashboard = tk.Frame(notebook, bg=theme["bg"])
    tab_attendance = tk.Frame(notebook, bg=theme["bg"])
    tab_analytics = tk.Frame(notebook, bg=theme["bg"])
    tab_ml = tk.Frame(notebook, bg=theme["bg"])
    
    notebook.add(tab_dashboard, text='📊 Dashboard')
    notebook.add(tab_attendance, text='📅 Attendance')
    notebook.add(tab_analytics, text='📈 Analytics')
    notebook.add(tab_ml, text='🤖 ML Insights')
    
    # Dashboard tab content
    content = tab_dashboard
    show_default_summary(content, emp_id, cursor)
    
    # Attendance tab - create sub-notebook
    attendance_notebook = ttk.Notebook(tab_attendance)
    attendance_notebook.pack(fill='both', expand=True, padx=5, pady=5)
    
    heatmap_frame = tk.Frame(attendance_notebook, bg=theme["bg"])
    history_frame = tk.Frame(attendance_notebook, bg=theme["bg"])
    leaderboard_frame = tk.Frame(attendance_notebook, bg=theme["bg"])
    
    attendance_notebook.add(heatmap_frame, text='Heatmap')
    attendance_notebook.add(history_frame, text='Login History')
    attendance_notebook.add(leaderboard_frame, text='Leaderboard')
    
    show_heatmap(heatmap_frame, emp_id, cursor)
    show_face_log(history_frame, emp_id, cursor)
    show_leaderboard(leaderboard_frame, cursor)
    
    # Analytics tab - create sub-notebook
    analytics_notebook = ttk.Notebook(tab_analytics)
    analytics_notebook.pack(fill='both', expand=True, padx=5, pady=5)
    
    productivity_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
    performance_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
    patterns_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
    salary_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
    ontime_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
    
    analytics_notebook.add(productivity_frame, text='Productivity Score')
    analytics_notebook.add(performance_frame, text='Performance Trends')
    analytics_notebook.add(patterns_frame, text='Work Patterns')
    analytics_notebook.add(salary_frame, text='Salary Breakdown')
    analytics_notebook.add(ontime_frame, text='On-Time vs Late')
    
    show_productivity_score(productivity_frame, emp_id, cursor)
    show_performance_trends(performance_frame, emp_id, cursor)
    show_work_patterns(patterns_frame, emp_id, cursor)
    show_salary_pie(salary_frame, emp_id, cursor)
    show_attendance_bar(ontime_frame, emp_id, cursor)
    
    # ML tab
    ml_content = tab_ml
    anomaly_frame = tk.Frame(ml_content, bg=theme["bg"])
    anomaly_frame.pack(fill='both', expand=True)
    run_anomaly_scan(cursor, anomaly_frame)
    dashboard.after(2000, lambda: auto_reminder(emp_id, cursor))
    # Auto-train ML models in background on startup
    dashboard.after(1000, lambda: auto_train_ml_models(cursor, emp_id))

# ------------------
# Sign-in/out, reminders and remaining helpers
