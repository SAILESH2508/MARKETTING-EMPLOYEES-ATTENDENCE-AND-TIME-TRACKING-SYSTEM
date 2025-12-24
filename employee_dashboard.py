import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Default Theme
DARK_MODE = {
    "bg": "#1A1A2E", "fg": "white", "button": "#E94560", "hover": "#FF6F61", "card": "#2E2E2E"
}
LIGHT_MODE = {
    "bg": "#F0F0F0", "fg": "#1A1A2E", "button": "#007BFF", "hover": "#0056b3", "card": "#FFFFFF"
}
theme = DARK_MODE.copy()

BUTTON_FONT = ("Arial", 12)

class CustomButton:
    def __init__(self, parent, text, command):
        self.button = tk.Button(parent, text=text, font=BUTTON_FONT,
                                bg=theme["button"], fg=theme["fg"],
                                activebackground=theme["hover"], relief="flat", bd=0)
        self.button.bind("<Enter>", lambda e: self.button.config(bg=theme["hover"]))
        self.button.bind("<Leave>", lambda e: self.button.config(bg=theme["button"]))
        self.button.config(command=command)
        self.button.pack(fill='x', pady=5, padx=10)

def employee_dashboard(root, emp_id, name, cursor, conn):
    dashboard = tk.Toplevel(root)
    dashboard.title(f"Dashboard - {name}")
    dashboard.geometry("1000x600")
    dashboard.configure(bg=theme["bg"])
    dashboard.attributes("-alpha", 0.0)
    fade_in(dashboard)

    # Top bar
    top_bar = tk.Frame(dashboard, bg=theme["bg"])
    top_bar.pack(fill='x')

    tk.Label(top_bar, text=f"Welcome, {name}!", font=("Arial", 18, "bold"),
             bg=theme["bg"], fg=theme["fg"]).pack(side='left', padx=10, pady=10)

    tk.Button(top_bar, text="🌗 Toggle Mode", command=lambda: toggle_theme(dashboard, root, emp_id, name, cursor, conn),
              bg=theme["button"], fg=theme["fg"], font=BUTTON_FONT).pack(side='right', padx=10)
    tk.Button(top_bar, text="🚪 Logout", command=dashboard.destroy,
              bg=theme["button"], fg=theme["fg"], font=BUTTON_FONT).pack(side='right')

    # Main body
    main_body = tk.Frame(dashboard, bg=theme["bg"])
    main_body.pack(fill='both', expand=True)

    nav = tk.Frame(main_body, bg=theme["card"], width=200)
    nav.pack(side='left', fill='y')

    content = tk.Frame(main_body, bg=theme["bg"])
    content.pack(side='right', expand=True, fill='both')

    # Sign In/Out Buttons
    CustomButton(nav, "Sign In", lambda: sign_in(emp_id, name, cursor, conn))
    CustomButton(nav, "Sign Out", lambda: sign_out(emp_id, cursor, conn))

    # Navigation Buttons
    CustomButton(nav, "📅 Attendance Heatmap", lambda: show_heatmap(content, emp_id, cursor))
    CustomButton(nav, "🏆 Leaderboard", lambda: show_leaderboard(content, cursor))
    CustomButton(nav, "💰 Salary Breakdown", lambda: show_salary_pie(content, emp_id, cursor))
    CustomButton(nav, "📸 Face Login History", lambda: show_face_log(content, emp_id, cursor))
    CustomButton(nav, "📊 On-Time vs Late", lambda: show_attendance_bar(content, emp_id, cursor))

    auto_reminder(emp_id, cursor)

def fade_in(win, alpha=0.0):
    alpha += 0.05
    if alpha <= 1.0:
        win.attributes("-alpha", alpha)
        win.after(30, lambda: fade_in(win, alpha))

def toggle_theme(dashboard, root, emp_id, name, cursor, conn):
    global theme
    theme = LIGHT_MODE if theme == DARK_MODE else DARK_MODE
    dashboard.destroy()  # Restart the dashboard
    employee_dashboard(root, emp_id, name, cursor, conn)  # Use the existing 'root' window

def sign_in(emp_id, name, cursor, conn):
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
    cursor.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    if cursor.fetchone():
        messagebox.showinfo("INFO", "Already signed in today!")
    else:
        cursor.execute("INSERT INTO attendance (emp_id, name, date, sign_in) VALUES (?, ?, ?, ?)",
                       (emp_id, name, date, time))
        conn.commit()
        messagebox.showinfo("SUCCESS", f"Signed in at {time}")

def sign_out(emp_id, cursor, conn):
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
    cursor.execute("SELECT sign_in FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    record = cursor.fetchone()
    if record and record[0] is not None:
        cursor.execute("UPDATE attendance SET sign_out=? WHERE emp_id=? AND date=?", (time, emp_id, date))
        conn.commit()
        messagebox.showinfo("SUCCESS", f"Signed out at {time}")
    else:
        messagebox.showwarning("ALERT", "You haven't signed in today!")

def auto_reminder(emp_id, cursor):
    now = datetime.now()
    hour = now.hour
    today = now.strftime("%Y-%m-%d")
    cursor.execute("SELECT sign_in, sign_out FROM attendance WHERE emp_id=? AND date=?", (emp_id, today))
    record = cursor.fetchone()
    if hour >= 9 and (not record or not record[0]):
        messagebox.showinfo("Reminder", "You forgot to sign in today!")
    if hour >= 17 and (not record or not record[1]):
        messagebox.showinfo("Reminder", "You might have forgotten to sign out!")

def clear_content(frame):
    for widget in frame.winfo_children():
        widget.destroy()

# UI Embeds
def show_heatmap(frame, emp_id, cursor):
    clear_content(frame)
    cursor.execute("SELECT date FROM attendance WHERE emp_id=?", (emp_id,))
    dates = [row[0] for row in cursor.fetchall()]
    date_counts = {d: dates.count(d) for d in set(dates)}

    fig, ax = plt.subplots(figsize=(6, 3))
    year, month = datetime.now().year, datetime.now().month
    days = calendar.Calendar().itermonthdays(year, month)

    labels, values = [], []
    for day in days:
        if day == 0:
            labels.append("")
            values.append(0)
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"
            labels.append(str(day))
            values.append(date_counts.get(date_str, 0))

    ax.bar(labels, values, color='lightblue')
    ax.set_title("Attendance Heatmap", color=theme["fg"])
    ax.tick_params(axis='x', colors=theme["fg"])
    ax.tick_params(axis='y', colors=theme["fg"])
    fig.patch.set_facecolor(theme["bg"])

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def show_leaderboard(frame, cursor):
    clear_content(frame)
    tk.Label(frame, text="🏆 Punctuality Leaderboard 🏆", font=("Arial", 16), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
    leaderboard = tk.Frame(frame, bg=theme["card"])
    leaderboard.pack(padx=10, pady=10)

    cursor.execute(""" 
        SELECT e.name, COUNT(a.date),
               SUM(CASE WHEN TIME(a.sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
               SUM(CASE WHEN TIME(a.sign_in) > '09:00:00' THEN 1 ELSE 0 END)
        FROM attendance a
        JOIN employees e ON a.emp_id = e.id
        WHERE a.sign_in IS NOT NULL
        GROUP BY a.emp_id
        ORDER BY COUNT(a.date) DESC
        LIMIT 5
    """)
    for i, (name, days, on_time, late) in enumerate(cursor.fetchall(), 1):
        badge = "🥇 Gold" if on_time / days >= 0.9 else "🥈 Silver" if on_time / days >= 0.75 else "🥉 Bronze"
        msg = f"{i}. {name} - {on_time}/{days} On-time - {badge}"
        tk.Label(leaderboard, text=msg, bg=theme["card"], fg=theme["fg"], font=("Arial", 12)).pack(anchor="w", pady=2)

def show_salary_pie(frame, emp_id, cursor):
    clear_content(frame)
    cursor.execute("SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showinfo("Data", "No salary data found.")
        return

    salary, bonus, deductions = result
    labels = ['Salary', 'Bonus', 'Deductions']
    values = [salary, bonus, deductions]
    colors = ['#4CAF50', '#2196F3', '#FF5722']

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    fig.patch.set_facecolor(theme["bg"])
    ax.set_title("Salary Breakdown", color=theme["fg"])

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def show_attendance_bar(frame, emp_id, cursor):
    clear_content(frame)
    cursor.execute(""" 
        SELECT COUNT(*),
               SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
               SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END)
        FROM attendance
        WHERE emp_id=? AND sign_in IS NOT NULL
    """, (emp_id,))
    total, on_time, late = cursor.fetchone()
    if total == 0:
        tk.Label(frame, text="No attendance data found.", bg=theme["bg"], fg=theme["fg"]).pack()
        return

    fig, ax = plt.subplots()
    ax.bar(['On-Time', 'Late'], [on_time, late], color=['#4CAF50', '#FF5722'])
    ax.set_title("On-Time vs Late", color=theme["fg"])
    fig.patch.set_facecolor(theme["bg"])

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def show_face_log(frame, emp_id, cursor):
    clear_content(frame)
    tk.Label(frame, text="Recent Face Login History", font=("Arial", 14),
             bg=theme["bg"], fg=theme["fg"]).pack(pady=10)

    log_frame = tk.Frame(frame, bg=theme["card"])
    log_frame.pack(fill='both', expand=True, padx=10, pady=5)

    cursor.execute("SELECT date, sign_in FROM attendance WHERE emp_id=? ORDER BY date DESC LIMIT 10", (emp_id,))
    rows = cursor.fetchall()
    if not rows:
        tk.Label(log_frame, text="No login data found.", bg=theme["card"], fg=theme["fg"]).pack(pady=10)
    else:
        for date, sign_in in rows:
            tk.Label(log_frame, text=f"{date} - {sign_in or 'Not Recorded'}",
                     bg=theme["card"], fg=theme["fg"]).pack(anchor="w", padx=10, pady=2)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Employee Dashboard")
    root.geometry("1000x600")
    root.configure(bg=theme["bg"])

    # Placeholder values for employee ID, name, cursor, and conn
    emp_id = 1  # Replace with actual employee ID
    name = "John Doe"  # Replace with actual employee name
    conn = sqlite3.connect("employee.db")  # Example database connection
    cursor = conn.cursor()

    # Initialize the dashboard for the employee
    employee_dashboard(root, emp_id, name, cursor, conn)

    root.mainloop()  # Start the Tkinter event loop
