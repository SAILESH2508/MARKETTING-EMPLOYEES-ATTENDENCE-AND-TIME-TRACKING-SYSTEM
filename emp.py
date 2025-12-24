import cv2
import face_recognition
import numpy as np
import sqlite3
import tkinter as tk
import subprocess
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime, timedelta
from employee_dashboard import employee_dashboard
from admin_dashboard import launch_admin_dashboard

# SQLite Connection
conn = sqlite3.connect("attendance_system.db")
cursor = conn.cursor()

# Lockout Config
LOCKOUT_DURATION = timedelta(minutes=5)

# Create lockout table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS lockout_status (
    id TEXT PRIMARY KEY,
    locked_until TEXT
)
''')
conn.commit()

# THEME COLORS
DARK_BLUE = "#1A237E"
RED = "#D32F2F"
ACCENT_BG = "#263238"
TEXT_WHITE = "white"

# Main Window
root = tk.Tk()
root.title("Marketing Employee Time & Attendance System")
root.config(bg=ACCENT_BG)
root.geometry("")  # Let the window auto-size to content

tk.Label(
    root,
    text="Marketing Employee Time & Attendance Tracker",
    font=("Helvetica", 20, "bold"),
    bg=DARK_BLUE,
    fg=TEXT_WHITE
).pack(pady=25)

# =========================
# FACE FIRST FUNCTIONALITY
# =========================
def face_first_login(root, cursor, conn):
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    import cv2
    import face_recognition
    import numpy as np

    messagebox.showinfo("Step 1", "Face recognition starting...")

    # Create a modal face recognition window
    face_window = tk.Toplevel(root)
    face_window.geometry("700x600")
    face_window.title("Face Recognition Login")
    face_window.config(bg=ACCENT_BG)
    face_window.grab_set()  # Make it modal
    root.attributes('-disabled', True)  # Disable main window

    def on_close():
        video_capture.release()
        root.attributes('-disabled', False)  # Re-enable main window
        face_window.destroy()

    face_window.protocol("WM_DELETE_WINDOW", on_close)  # Handle window close

    # UI layout
    tk.Label(
        face_window,
        text="Look at the camera to verify your face",
        font=("Helvetica", 14),
        bg=DARK_BLUE,
        fg=TEXT_WHITE
    ).pack(pady=15)

    camera_frame = tk.Frame(face_window, width=640, height=480, bg=ACCENT_BG)
    camera_frame.pack(pady=20)

    camera_label = tk.Label(camera_frame)
    camera_label.pack()

    video_capture = cv2.VideoCapture(0)
    retry_count = 0
    max_retries = 60

    def update_camera_feed():
        nonlocal retry_count
        ret, frame = video_capture.read()
        if not ret:
            messagebox.showerror("ERROR", "Failed to capture image!")
            on_close()
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

        if face_encodings:
            cursor.execute("SELECT id, name, face_encoding FROM employees")
            employees = cursor.fetchall()
            for emp_id, name, encoding in employees:
                if encoding is None:
                    continue
                try:
                    known_encoding = np.frombuffer(encoding, dtype=np.float64)
                except Exception as e:
                    print(f"Error decoding face for {name}: {e}")
                    continue
                match = face_recognition.compare_faces([known_encoding], face_encodings[0])
                if match[0]:
                    on_close()
                    employee_dashboard(root, emp_id, name, cursor, conn)
                    return

        retry_count += 1
        if retry_count < max_retries:
            face_window.after(100, update_camera_feed)
        else:
            messagebox.showerror("Access Denied", "Face not recognized.")
            on_close()

    update_camera_feed()

# =========================
def open_register():
    root.iconify()
    subprocess.Popen(["python", "register_face.py"])

# =========================
# Buttons
def create_button(parent, text, command, bg_color, fg_color):
    button = tk.Button(
        parent,
        text=text,
        font=("Helvetica", 16),  # Larger font
        bg=bg_color,
        fg=fg_color,
        activebackground=RED,
        relief="flat",
        bd=0,
        width=30,   # Wider
        height=2    # Taller
    )
    button.bind("<Enter>", lambda e: button.config(bg=DARK_BLUE))
    button.bind("<Leave>", lambda e: button.config(bg=bg_color))
    button.config(command=command)
    return button

# Larger Buttons with spacing
create_button(root, "Employee Login", lambda: face_first_login(root, cursor, conn),RED, TEXT_WHITE).pack(pady=15)
create_button(root, "Admin Login", launch_admin_dashboard,RED, TEXT_WHITE).pack(pady=15)
create_button(root, "Register New Employee (Face)", open_register,RED, TEXT_WHITE).pack(pady=15)

root.mainloop()
