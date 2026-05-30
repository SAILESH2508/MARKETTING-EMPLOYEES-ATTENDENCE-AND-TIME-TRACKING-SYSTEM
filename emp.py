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
from dashboard_modules.ui_helpers import theme, RoundedFrame, CustomButton

# THEME COLORS (Mapped from global theme)
BG_COLOR = theme["bg"]
FG_COLOR = theme["fg"]
BUTTON_COLOR = theme["button"]
BUTTON_HOVER = theme["hover"]
CARD_COLOR = theme["card"]

# Fonts
HEADER_FONT = ("Segoe UI", 26, "bold")
BODY_FONT = ("Segoe UI", 11)
BUTTON_FONT = ("Segoe UI", 11, "bold")


# SQLite Connection
def get_db_connection():
    return sqlite3.connect("attendance_system.db")


# Ensure lockout table (run once)
try:
    conn = get_db_connection()
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS lockout_status (
        id TEXT PRIMARY KEY,
        locked_until TEXT
    )
    """
    )
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

    tk.Label(
        face_window,
        text="Looking for Face...",
        font=HEADER_FONT,
        bg=BG_COLOR,
        fg=FG_COLOR,
    ).pack(pady=20)

    # Camera Frame using RoundedFrame with button/indigo accent border
    camera_frame = RoundedFrame(
        face_window,
        width=520,
        height=370,
        corner_radius=15,
        bg_color="black",
        border_color=BUTTON_COLOR,
    )
    camera_frame.pack(pady=10)

    camera_label = tk.Label(camera_frame.inner_frame, bg="black")
    camera_label.pack(fill="both", expand=True)

    status_label = tk.Label(
        face_window,
        text="Initializing...",
        font=("Segoe UI Semibold", 14),
        bg=BG_COLOR,
        fg="#FFD700",
    )
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
        if not running:
            return

        ret, frame = video_capture.read()
        if not ret:
            status_label.config(text="Camera Error")
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk  # type: ignore
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
                        match = face_recognition.compare_faces(
                            [known], face_encodings[0], tolerance=0.5
                        )
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

tk.Label(
    root,
    text="EMPLOYEE TIME & ATTENDANCE SYSTEM",
    font=("Segoe UI", 24, "bold"),
    bg=BG_COLOR,
    fg=FG_COLOR,
).pack(pady=(60, 5))

tk.Label(
    root,
    text="MARKETING TEAM PORTAL",
    font=("Segoe UI Semibold", 11),
    bg=BG_COLOR,
    fg=BUTTON_COLOR,
).pack(pady=(0, 20))

tk.Label(
    root, text="Select Access Mode", font=("Segoe UI", 12), bg=BG_COLOR, fg="#8892B0"
).pack(pady=5)

# Rounded Card-like Container
menu_container = RoundedFrame(root, width=420, height=320, bg_color=CARD_COLOR)
menu_container.pack(pady=10)
menu_frame = menu_container.inner_frame


def btn_config(btn, default_bg=BUTTON_COLOR, hover_bg=BUTTON_HOVER):
    btn.config(
        font=BUTTON_FONT,
        bg=default_bg,
        fg="white",
        activebackground=hover_bg,
        activeforeground="white",
        width=25,
        height=2,
        bd=0,
        cursor="hand2",
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=default_bg))


def open_reg():
    root.iconify()
    import sys
    subprocess.Popen([sys.executable, "register_face.py"])


b1 = tk.Button(
    menu_frame, text="👤  Employee Face Login", command=lambda: face_first_login(root)
)
btn_config(b1, BUTTON_COLOR, BUTTON_HOVER)
b1.pack(pady=10)

b2 = tk.Button(menu_frame, text="🔑  Admin Dashboard", command=launch_admin_dashboard)
btn_config(b2, BUTTON_COLOR, BUTTON_HOVER)
b2.pack(pady=10)

b3 = tk.Button(menu_frame, text="📝  Register New Employee", command=open_reg)
btn_config(b3, BUTTON_COLOR, BUTTON_HOVER)
b3.pack(pady=10)

# Footer
tk.Label(
    root,
    text="Secure Biometric Time Tracking • v2.1",
    font=("Segoe UI", 9),
    bg=BG_COLOR,
    fg="#8892B0",
).pack(side="bottom", pady=25)

if __name__ == "__main__":
    root.mainloop()
