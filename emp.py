import cv2
import face_recognition
import numpy as np
import sqlite3
import tkinter as tk
import subprocess
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime

# Local Modules - importing functions directly to maintain integration
from employee_dashboard import employee_dashboard
from admin_dashboard import launch_admin_dashboard

# ORIGINAL DARK THEME CONSTANTS
BG_COLOR = "#1A1A2E"
FG_COLOR = "white"
BUTTON_COLOR = "#E94560"
BUTTON_HOVER = "#FF6F61"
CARD_COLOR = "#2E2E2E"

# Fonts
HEADER_FONT = ("Arial", 25, "bold")
BODY_FONT = ("Arial", 12)
BUTTON_FONT = ("Arial", 11, "bold")

# SQLite Connection
def get_db_connection():
    return sqlite3.connect("attendance_system.db")

# Ensure lockout table (run once)
try:
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS lockout_status (
        id TEXT PRIMARY KEY,
        locked_until TEXT
    )
    ''')
    conn.commit()
    conn.close()
except Exception as e:
    print(f"DB Init Error: {e}")

# Main Window
root = tk.Tk()
root.title("Employee Attendance System")
root.geometry("800x600")
root.configure(bg=BG_COLOR)

# Center function
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

center_window(root, 800, 600)

# =========================
# FACE LOGIN LOGIC
# =========================
def face_first_login(root_win):
    face_window = tk.Toplevel(root_win)
    face_window.title("Face Login")
    face_window.configure(bg=BG_COLOR)
    center_window(face_window, 700, 600)
    face_window.grab_set()

    tk.Label(face_window, text="Looking for Face...", font=HEADER_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(pady=20)

    # Camera Frame
    camera_frame = tk.Frame(face_window, bg="black", width=500, height=350, highlightbackground=FG_COLOR, highlightthickness=2)
    camera_frame.pack(pady=10)
    camera_frame.pack_propagate(False)

    camera_label = tk.Label(camera_frame, bg="black")
    camera_label.pack(fill='both', expand=True)

    status_label = tk.Label(face_window, text="Initializing...", font=("Arial", 14), bg=BG_COLOR, fg="#FFD700")
    status_label.pack(pady=10)

    # Variables
    retry_count = 0
    max_retries = 80
    running = True
    
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        messagebox.showerror("Camera Error", "Cannot access webcam.")
        face_window.destroy()
        return

    def cleanup():
        nonlocal running
        running = False
        if video_capture.isOpened():
            video_capture.release()
        face_window.destroy()

    face_window.protocol("WM_DELETE_WINDOW", cleanup)

    def process_login(emp_id, name):
        status_label.config(text=f"Welcome, {name}!", fg="#00FF00")
        face_window.after(1000, lambda: [cleanup(), launch_dashboard(emp_id, name)])

    def launch_dashboard(emp_id, name):
        conn = get_db_connection()
        cursor = conn.cursor()
        employee_dashboard(root_win, emp_id, name, cursor, conn)

    def update_loop():
        nonlocal retry_count
        if not running: return

        ret, frame = video_capture.read()
        if not ret:
            status_label.config(text="Camera Error")
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

        # Detection
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        matched = False
        if face_encodings:
            status_label.config(text="Scanning...", fg="cyan")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, face_encoding FROM employees")
            employees = cursor.fetchall()
            conn.close()

            for emp_id, name, encoding in employees:
                if encoding:
                    try:
                        known = np.frombuffer(encoding, dtype=np.float64)
                        match = face_recognition.compare_faces([known], face_encodings[0], tolerance=0.5)
                        if match[0]:
                            process_login(emp_id, name)
                            return
                    except:
                        pass
            
            status_label.config(text="Face Not Recognized", fg="red")
        
        retry_count += 1
        if retry_count > max_retries:
            status_label.config(text="Timeout. Try again.", fg="red")
            face_window.after(2000, cleanup)
        else:
            face_window.after(50, update_loop)

    update_loop()

# =========================
# UI LAYOUT
# =========================

tk.Label(root, text="EMPLOYEE ATTENDANCE SYSTEM", font=("Impact", 30), bg=BG_COLOR, fg=FG_COLOR).pack(pady=(60, 20))
tk.Label(root, text="Select Login Mode", font=("Arial", 14), bg=BG_COLOR, fg="gray").pack(pady=10)

# Card-like Container
menu_frame = tk.Frame(root, bg=CARD_COLOR, padx=40, pady=40)
menu_frame.pack(pady=20)

def btn_config(btn):
    btn.config(font=BUTTON_FONT, bg=BUTTON_COLOR, fg="white", activebackground=BUTTON_HOVER, activeforeground="white", width=25, height=2, bd=0, cursor="hand2")

def open_reg():
    root.iconify()
    subprocess.Popen(["python", "register_face.py"])

b1 = tk.Button(menu_frame, text="👤  Employee Face Login", command=lambda: face_first_login(root))
btn_config(b1)
b1.pack(pady=10)

b2 = tk.Button(menu_frame, text="🔑  Admin Dashboard", command=launch_admin_dashboard)
btn_config(b2)
b2.pack(pady=10)

b3 = tk.Button(menu_frame, text="📝  Register New Employee", command=open_reg)
btn_config(b3)
b3.config(bg="#4CAF50", activebackground="#45a049") # Green for register
b3.pack(pady=10)

# Footer
tk.Label(root, text="Developed for Marketing Team • v2.0", font=("Arial", 9), bg=BG_COLOR, fg="gray").pack(side='bottom', pady=20)

if __name__ == "__main__":
    root.mainloop()
