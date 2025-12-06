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
def show_heatmap(frame, emp_id, cursor):
    # Import at function level to avoid circular imports
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    clear_content(frame)
    rows, err = get_db_data_safely("SELECT date FROM attendance WHERE emp_id=?", (emp_id,), fetch_all=True)
    if err:
        tk.Label(frame, text=f"Database error: {err}", bg=theme['bg'], fg=theme['fg']).pack()
        return
    dates = [row[0] for row in rows]
    date_counts = {d: dates.count(d) for d in set(dates)}
    fig, ax = plt.subplots(figsize=(6, 3), facecolor=theme['bg'])
    ax.set_facecolor(theme['card'])
    ax.tick_params(colors=theme['fg'])
    ax.xaxis.label.set_color(theme['fg'])
    ax.yaxis.label.set_color(theme['fg'])
    ax.title.set_color(theme['fg'])
    year, month = datetime.now().year, datetime.now().month
    days = list(calendar.Calendar().itermonthdays(year, month))
    labels, values = [], []
    for day in days:
        if day == 0:
            labels.append("")
            values.append(0)
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"
            labels.append(str(day))
            values.append(date_counts.get(date_str, 0))
    ax.bar(labels, values, color=theme['button'])
    ax.set_title(f"Attendance Heatmap ({calendar.month_name[month]} {year})")
    ax.set_ylabel('Sign-ins')
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    plt.close(fig)

def show_leaderboard(frame, cursor):
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    clear_content(frame)
    tk.Label(frame, text="🏆 Punctuality Leaderboard 🏆", font=("Arial", 16), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
    leaderboard = tk.Frame(frame, bg=theme["card"])
    leaderboard.pack(padx=10, pady=10)
    query = """ 
        SELECT e.name, COUNT(a.date),
                SUM(CASE WHEN TIME(a.sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                SUM(CASE WHEN TIME(a.sign_in) > '09:00:00' THEN 1 ELSE 0 END)
        FROM attendance a
        JOIN employees e ON a.emp_id = e.id
        WHERE a.sign_in IS NOT NULL
        GROUP BY a.emp_id
        ORDER BY COUNT(a.date) DESC
        LIMIT 5
    """
    rows, err = get_db_data_safely(query, fetch_all=True)
    if err:
        tk.Label(frame, text=f"Database error: {err}", bg=theme['bg'], fg=theme['fg']).pack()
        return
    header = tk.Frame(leaderboard, bg=theme['card'])
    header.pack(fill='x', padx=5, pady=2)
    tk.Label(header, text="Rank", font=("Arial", 12, 'bold'), bg=theme['card'], fg=theme['fg']).pack(side='left', padx=5, ipadx=5)
    tk.Label(header, text="Name", font=("Arial", 12, 'bold'), bg=theme['card'], fg=theme['fg']).pack(side='left', padx=20, ipadx=5)
    tk.Label(header, text="On-Time/Total", font=("Arial", 12, 'bold'), bg=theme['card'], fg=theme['fg']).pack(side='left', padx=20, ipadx=5)
    tk.Label(header, text="Badge", font=("Arial", 12, 'bold'), bg=theme['card'], fg=theme['fg']).pack(side='left', padx=20, ipadx=5)
    for i, (name, days, on_time, late) in enumerate(rows or [], 1):
        if days == 0:
            pct = 0
        else:
            pct = on_time / days
        badge = "🥇 Gold" if days and pct >= 0.9 else "🥈 Silver" if days and pct >= 0.75 else "🥉 Bronze" if days else "No Data"
        row_frame = tk.Frame(leaderboard, bg=theme['card'])
        row_frame.pack(fill='x', padx=5, pady=2)
        tk.Label(row_frame, text=f"{i}.", bg=theme['card'], fg=theme['fg'], font=("Arial", 12)).pack(side='left', padx=5, ipadx=5)
        tk.Label(row_frame, text=name, bg=theme['card'], fg=theme['fg'], font=("Arial", 12)).pack(side='left', padx=20, ipadx=5)
        tk.Label(row_frame, text=f"{on_time}/{days}", bg=theme['card'], fg=theme['fg'], font=("Arial", 12)).pack(side='left', padx=20, ipadx=5)
        tk.Label(row_frame, text=badge, bg=theme['card'], fg=theme['fg'], font=("Arial", 12)).pack(side='left', padx=20, ipadx=5)

def show_salary_pie(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    clear_content(frame)
    result, err = get_db_data_safely("SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,), fetch_all=False)
    if err:
        messagebox.showinfo("Data", f"Database error: {err}")
        return
    if not result:
        messagebox.showinfo("Data", "No salary data found.")
        return
    salary, bonus, deductions = result
    salary = salary if salary is not None else 0.0
    bonus = bonus if bonus is not None else 0.0
    deductions = deductions if deductions is not None else 0.0
    
    # Main container with padding
    main_container = tk.Frame(frame, bg=theme['bg'])
    main_container.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Title
    title_frame = tk.Frame(main_container, bg=theme['bg'])
    title_frame.pack(fill='x', pady=(0, 20))
    tk.Label(title_frame, text="💰 Salary Breakdown", font=("Arial", 20, "bold"), 
             bg=theme["bg"], fg=theme["fg"]).pack(anchor='w')
    
    # Content container - split into left and right
    content_container = tk.Frame(main_container, bg=theme['bg'])
    content_container.pack(fill='both', expand=True)
    
    # Left side - Pie chart
    left_frame = tk.Frame(content_container, bg=theme['bg'])
    left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20))
    
    labels = []
    values = []
    if salary and salary > 0:
        labels.append('Base Salary')
        values.append(salary)
    if bonus and bonus > 0:
        labels.append('Bonus')
        values.append(bonus)
    if deductions and deductions > 0:
        labels.append('Deductions')
        values.append(deductions)
    
    if not values:
        tk.Label(left_frame, text="All salary components are zero.", 
                bg=theme['bg'], fg=theme['fg'], font=("Arial", 12)).pack(pady=50)
    else:
        fig, ax = plt.subplots(figsize=(6, 6), facecolor=theme['bg'])
        colors = [theme['button'], '#4CAF50', '#F44336']
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, 
               colors=colors, textprops={'color': theme['fg'], 'fontsize': 11})
        ax.set_title("Salary Component Breakdown", color=theme['fg'], fontsize=14, pad=20)
        canvas = FigureCanvasTkAgg(fig, master=left_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)
    
    # Right side - Detailed breakdown
    right_frame = tk.Frame(content_container, bg=theme['card'], relief='flat', bd=0)
    right_frame.pack(side='right', fill='both', expand=True)
    
    # Add padding inside right frame
    details_container = tk.Frame(right_frame, bg=theme['card'])
    details_container.pack(fill='both', expand=True, padx=30, pady=30)
    
    # Title for details
    tk.Label(details_container, text="📊 Detailed Breakdown", font=("Arial", 16, "bold"), 
             bg=theme['card'], fg=theme['fg']).pack(anchor='w', pady=(0, 20))
    
    # Base Salary
    salary_row = tk.Frame(details_container, bg=theme['card'])
    salary_row.pack(fill='x', pady=10)
    tk.Label(salary_row, text="💼 Base Salary:", font=("Arial", 13, "bold"), 
             bg=theme['card'], fg=theme['fg'], width=18, anchor='w').pack(side='left')
    tk.Label(salary_row, text=f"₹{salary:,.2f}", font=("Arial", 13), 
             bg=theme['card'], fg=theme['button'], anchor='e').pack(side='right', fill='x', expand=True)
    
    # Separator
    tk.Frame(details_container, bg=theme['fg'], height=1).pack(fill='x', pady=5)
    
    # Bonus
    bonus_row = tk.Frame(details_container, bg=theme['card'])
    bonus_row.pack(fill='x', pady=10)
    tk.Label(bonus_row, text="➕ Bonus:", font=("Arial", 13, "bold"), 
             bg=theme['card'], fg=theme['fg'], width=18, anchor='w').pack(side='left')
    bonus_color = '#4CAF50' if bonus > 0 else theme['fg']
    tk.Label(bonus_row, text=f"₹{bonus:,.2f}", font=("Arial", 13), 
             bg=theme['card'], fg=bonus_color, anchor='e').pack(side='right', fill='x', expand=True)
    
    # Separator
    tk.Frame(details_container, bg=theme['fg'], height=1).pack(fill='x', pady=5)
    
    # Deductions
    deductions_row = tk.Frame(details_container, bg=theme['card'])
    deductions_row.pack(fill='x', pady=10)
    tk.Label(deductions_row, text="➖ Deductions:", font=("Arial", 13, "bold"), 
             bg=theme['card'], fg=theme['fg'], width=18, anchor='w').pack(side='left')
    deductions_color = '#F44336' if deductions > 0 else theme['fg']
    tk.Label(deductions_row, text=f"₹{deductions:,.2f}", font=("Arial", 13), 
             bg=theme['card'], fg=deductions_color, anchor='e').pack(side='right', fill='x', expand=True)
    
    # Separator (thicker)
    tk.Frame(details_container, bg=theme['fg'], height=2).pack(fill='x', pady=15)
    
    # Net Salary (Total)
    net_salary = salary + bonus - deductions
    total_row = tk.Frame(details_container, bg=theme['card'])
    total_row.pack(fill='x', pady=15)
    tk.Label(total_row, text="💰 Net Salary:", font=("Arial", 15, "bold"), 
             bg=theme['card'], fg=theme['fg'], width=18, anchor='w').pack(side='left')
    net_color = '#4CAF50' if net_salary > 0 else '#F44336'
    tk.Label(total_row, text=f"₹{net_salary:,.2f}", font=("Arial", 15, "bold"), 
             bg=theme['card'], fg=net_color, anchor='e').pack(side='right', fill='x', expand=True)
    
    # Additional info
    info_frame = tk.Frame(details_container, bg=theme['card'])
    info_frame.pack(fill='x', pady=(30, 0))
    
    # Calculate percentages
    if salary > 0:
        bonus_pct = (bonus / salary) * 100
        deductions_pct = (deductions / salary) * 100
        
        tk.Label(info_frame, text="📈 Bonus Rate:", font=("Arial", 11), 
                bg=theme['card'], fg=theme['fg'], anchor='w').pack(fill='x', pady=3)
        tk.Label(info_frame, text=f"{bonus_pct:.1f}% of base salary", font=("Arial", 10), 
                bg=theme['card'], fg='#4CAF50', anchor='w', padx=20).pack(fill='x')
        
        tk.Label(info_frame, text="📉 Deduction Rate:", font=("Arial", 11), 
                bg=theme['card'], fg=theme['fg'], anchor='w').pack(fill='x', pady=3)
        tk.Label(info_frame, text=f"{deductions_pct:.1f}% of base salary", font=("Arial", 10), 
                bg=theme['card'], fg='#F44336', anchor='w', padx=20).pack(fill='x')

def show_attendance_bar(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    clear_content(frame)
    query = """ 
        SELECT COUNT(*),
                SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END)
        FROM attendance
        WHERE emp_id=? AND sign_in IS NOT NULL
    """
    row, err = get_db_data_safely(query, (emp_id,), fetch_all=False)
    if err:
        tk.Label(frame, text=f"Database error: {err}", bg=theme['bg'], fg=theme['fg']).pack()
        return
    if not row:
        tk.Label(frame, text="No attendance data found.", bg=theme['bg'], fg=theme['fg']).pack()
        return
    total, on_time, late = row
    if total == 0:
        tk.Label(frame, text="No attendance data found.", bg=theme['bg'], fg=theme['fg']).pack()
        return
    fig, ax = plt.subplots(facecolor=theme['bg'])
    ax.set_facecolor(theme['card'])
    ax.bar(['On-Time', 'Late'], [on_time, late], color=[theme['button'], theme['hover']])
    ax.set_title("On-Time vs Late Count", color=theme['fg'])
    ax.tick_params(colors=theme['fg'])
    ax.xaxis.label.set_color(theme['fg'])
    ax.yaxis.label.set_color(theme['fg'])
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    plt.close(fig)

def show_face_log(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content, get_db_data_safely
    clear_content(frame)
    tk.Label(frame, text="Recent Face Login History", font=("Arial", 14), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
    log_frame = tk.Frame(frame, bg=theme["card"])
    log_frame.pack(fill='both', expand=True, padx=10, pady=5)
    tree = ttk.Treeview(log_frame, columns=('Date', 'Sign In'), show='headings')
    tree.heading('Date', text='Date')
    tree.heading('Sign In', text='Sign In Time')
    rows, err = get_db_data_safely("SELECT date, sign_in FROM attendance WHERE emp_id=? ORDER BY date DESC LIMIT 10", (emp_id,), fetch_all=True)
    if err:
        tk.Label(log_frame, text=f"Database error: {err}", bg=theme['card'], fg=theme['fg']).pack(pady=10)
        return
    if not rows:
        tk.Label(log_frame, text="No login data found.", bg=theme['card'], fg=theme['fg']).pack(pady=10)
    else:
        for date, sign_in in rows:
            tree.insert('', 'end', values=(date, sign_in or 'Not Recorded'))
        tree.pack(padx=10, pady=10, fill='both', expand=True)

# ------------------
# Summary cards + embedded ML controls
