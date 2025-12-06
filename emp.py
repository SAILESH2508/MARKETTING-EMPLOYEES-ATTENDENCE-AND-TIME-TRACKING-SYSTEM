import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")

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
root.geometry("650x450")

tk.Label(
    root,
    text="Marketing Employee Time & Attendance Tracker",
    font=("Helvetica", 20, "bold"),
    bg=DARK_BLUE,
    fg=TEXT_WHITE
).pack(pady=25)

# =========================
# FACE FIRST FUNCTIONALITY (UPDATED: adds a separate status window)
# =========================
def face_first_login(root, cursor, conn):
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    import cv2
    import face_recognition
    import numpy as np

    # Keep original info popup
    messagebox.showinfo("Step 1", "Face recognition starting...")

    # Create a modal face recognition window
    face_window = tk.Toplevel(root)
    face_window.geometry("800x650")
    face_window.title("Face Recognition Login")
    face_window.config(bg=ACCENT_BG)
    face_window.grab_set()  # Make it modal
    try:
        root.attributes('-disabled', True)  # Disable main window
    except Exception:
        pass

    # Create a separate small status window (floating badge)
    status_window = tk.Toplevel(face_window)
    status_window.title("Status")
    status_window.geometry("300x90")
    status_window.resizable(False, False)
    status_window.transient(face_window)  # keep on top of face_window
    try:
        status_window.attributes('-topmost', True)
    except Exception:
        pass
    status_window.config(bg=ACCENT_BG)

    status_label = tk.Label(
        status_window,
        text="Recognizing",
        font=("Helvetica", 14, "bold"),
        bg=ACCENT_BG,
        fg=TEXT_WHITE
    )
    status_label.pack(expand=True, pady=10)

    # animate dots for 'Recognizing...'
    dot_state = {"dots": 0}
    def animate_dots():
        dot_state["dots"] = (dot_state["dots"] + 1) % 4
        status_label.config(text="Recognizing" + "." * dot_state["dots"])
        if not getattr(face_window, "_closed", False):
            status_window.after(400, animate_dots)
    animate_dots()

    def close_status():
        try:
            status_window.destroy()
        except Exception:
            pass

    # Safe on_close (preserve old behavior but more robust)
    def on_close():
        face_window._closed = True  # signal animation to stop
        try:
            if 'video_capture' in locals() and video_capture is not None:
                try:
                    if video_capture.isOpened():
                        video_capture.release()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            root.attributes('-disabled', False)  # Re-enable main window
        except Exception:
            pass
        close_status()
        try:
            face_window.destroy()
        except Exception:
            pass

    face_window.protocol("WM_DELETE_WINDOW", on_close)  # Handle window close
    # prevent direct closing of status window by user (keeps UI consistent)
    status_window.protocol("WM_DELETE_WINDOW", lambda: None)

    # UI layout (same as original)
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

    # Start camera and recognition loop
    video_capture = cv2.VideoCapture(0)
    retry_count = 0
    max_retries = 60

    def proceed_recognized(emp_id, name):
        # Update status to success, give brief pause, then call dashboard
        try:
            status_label.config(text=f"Recognized: {name}", fg=TEXT_WHITE)
            status_window.config(bg="#2e7d32")  # green background for success
            status_label.config(bg="#2e7d32", fg=TEXT_WHITE)
        except Exception:
            pass
        # give user a short moment to read status, then close and open dashboard
        face_window.after(700, lambda: (on_close(), employee_dashboard(root, emp_id, name, cursor, conn)))

    def update_camera_feed():
        nonlocal retry_count
        try:
            ret, frame = video_capture.read()
        except Exception:
            ret = False
            frame = None

        if not ret or frame is None:
            messagebox.showerror("ERROR", "Failed to capture image!")
            on_close()
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Draw rectangles for visual feedback (preserved)
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Show camera frame in Tk label
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

        if face_encodings:
            # update status to show we detected a face
            status_label.config(text="Face detected, checking...", fg=TEXT_WHITE)
            try:
                cursor.execute("SELECT id, name, face_encoding FROM employees")
                employees = cursor.fetchall()
            except Exception as e:
                print("DB fetch error:", e)
                employees = []

            # Track if we found a match and find the best match
            face_matched = False
            best_match = None
            best_distance = 1.0
            
            for emp_id, name, encoding in employees:
                if encoding is None:
                    continue
                try:
                    known_encoding = np.frombuffer(encoding, dtype=np.float64)
                except Exception as e:
                    print(f"Error decoding face for {name}: {e}")
                    continue
                try:
                    # Use stricter tolerance for better accuracy
                    # tolerance: 0.5 is stricter, ensures only correct person is matched
                    match = face_recognition.compare_faces([known_encoding], face_encodings[0], tolerance=0.5)
                    face_distance = face_recognition.face_distance([known_encoding], face_encodings[0])
                    
                    # Debug output
                    print(f"Checking {name} (ID: {emp_id}): Match={match[0]}, Distance={face_distance[0]:.3f}")
                except Exception as e:
                    print("compare_faces error:", e)
                    match = [False]
                    face_distance = [1.0]

                # Track the best match (lowest distance)
                if match[0] and face_distance[0] < best_distance:
                    best_distance = face_distance[0]
                    best_match = (emp_id, name)
                    face_matched = True
            
            # Only accept if best match has good distance (< 0.5 for strict matching)
            if face_matched and best_match and best_distance < 0.5:
                emp_id, name = best_match
                print(f"✅ Recognized: {name} (ID: {emp_id}, distance: {best_distance:.3f})")
                proceed_recognized(emp_id, name)
                return
            
            # If face detected but not matched after checking all employees
            if not face_matched and retry_count >= max_retries - 10:
                # Show warning in last 1 second (10 attempts)
                status_label.config(text="⚠️ Face not in database", fg="yellow")
        else:
            # No face detected in frame
            if retry_count % 10 == 0:  # Update status every 1 second
                status_label.config(text="⚠️ No face detected", fg="orange")

        retry_count += 1
        if retry_count < max_retries:
            face_window.after(100, update_camera_feed)
        else:
            # Determine final message based on what happened
            if face_encodings:
                # Face was detected but not recognized
                status_label.config(text="❌ Face not in database")
                messagebox.showwarning("Access Denied", "Face detected but not found in database.\n\nPlease register your face first.")
            else:
                # No face was detected at all
                status_label.config(text="❌ No face detected")
                messagebox.showwarning("Access Denied", "No face detected.\n\nPlease ensure:\n• Your face is clearly visible\n• Good lighting\n• Look directly at camera")
            try:
                status_window.config(bg=RED)
                status_label.config(bg=RED, fg=TEXT_WHITE)
            except Exception:
                pass
            face_window.after(1200, on_close)

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
create_button(root, "Employee Login", lambda: face_first_login(root, cursor, conn), RED, TEXT_WHITE).pack(pady=15)
create_button(root, "Admin Login", launch_admin_dashboard, RED, TEXT_WHITE).pack(pady=15)
create_button(root, "Register New Employee (Face)", open_register, RED, TEXT_WHITE).pack(pady=15)

root.mainloop()
