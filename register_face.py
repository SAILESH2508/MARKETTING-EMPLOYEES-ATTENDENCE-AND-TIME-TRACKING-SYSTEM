import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")

import cv2
import face_recognition
import numpy as np
import sqlite3
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from dashboard_modules.ui_helpers import (
    theme, HEADER_FONT, BODY_FONT, BUTTON_FONT, TITLE_FONT, SMALL_FONT,
    CustomButton, RoundedFrame, fade_in
)

# Create folder for face images if it doesn't exist
if not os.path.exists("employee_faces"):
    os.makedirs("employee_faces")

# Database Connection (SQLite)
conn = sqlite3.connect("attendance_system.db")
conn.row_factory = sqlite3.Row  # So we can use column names
cursor = conn.cursor()

# Tkinter GUI
root = tk.Tk()
root.title("Employee Face Registration")
root.geometry("600x750")
root.configure(bg=theme['bg'])

# Center
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
root.geometry(f"600x750+{int(sw/2-300)}+{int(sh/2-375)}")

# Header
tk.Label(root, text="Face Registration", font=HEADER_FONT, bg=theme['bg'], fg=theme['fg']).pack(pady=(30, 10))
tk.Label(root, text="Capture photo for biometric login", font=TITLE_FONT, bg=theme['bg'], fg=theme['text_secondary']).pack(pady=(0, 20))

# Form Card
container = RoundedFrame(root, width=540, height=600, bg_color=theme['card'])
container.pack(pady=10)
inner = container.inner_frame

# Form Inputs
tk.Label(inner, text="Employee ID", font=SMALL_FONT, bg=theme['card'], fg=theme['text_secondary']).pack(anchor='w', padx=40, pady=(20, 0))
emp_id_entry = tk.Entry(inner, font=BODY_FONT, bg=theme['bg'], fg=theme['fg'], relief='flat')
emp_id_entry.pack(fill='x', padx=40, pady=(5, 10))

tk.Label(inner, text="Full Name", font=SMALL_FONT, bg=theme['card'], fg=theme['text_secondary']).pack(anchor='w', padx=40)
name_entry = tk.Entry(inner, font=BODY_FONT, bg=theme['bg'], fg=theme['fg'], relief='flat')
name_entry.pack(fill='x', padx=40, pady=(5, 20))

# Camera Layout
cam_frame = tk.Frame(inner, bg='black', width=460, height=300)
cam_frame.pack(padx=20, pady=10)
cam_frame.pack_propagate(False)

camera_label = tk.Label(cam_frame, bg='black')
camera_label.pack(expand=True, fill='both')

# Initialize Camera
cam = cv2.VideoCapture(0)

def show_frame():
    ret, frame = cam.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize to fit?
        img = Image.fromarray(frame)
        # Keep aspect ratio
        img.thumbnail((460, 300))
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)
        camera_label.after(10, show_frame)

show_frame()  # Start preview

def capture_face():
    emp_id = emp_id_entry.get().strip()
    name = name_entry.get().strip()

    if not emp_id or not name:
        messagebox.showerror("Error", "Please enter Employee ID and Name")
        return

    # Check if Employee exists
    # If using shared DB, we might want to INSERT if not exists or assume Admin created entry first.
    # The original code just checked existence. Let's assume Admin flow: Admin creates entry without face, Employee registers face.
    # OR we can auto-create. Let's auto-create if not exists for better UX, or stick to strict check.
    # Sticking to check ensures role security.
    
    conn = sqlite3.connect("attendance_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM employees WHERE id=?", (emp_id,))
    if not cursor.fetchone():
        # Optional: Ask to create?
        if messagebox.askyesno("Not Found", "Employee ID not found. Create new Basic Employee?"):
            try:
                # Default role: Employee, Pwd: 'password' (unsafe but simple for now)
                from hashlib import sha256
                pwd = sha256("password".encode()).hexdigest()
                cursor.execute("INSERT INTO employees (id, name, role, password) VALUES (?, ?, 'Employee', ?)", (emp_id, name, pwd))
                conn.commit()
            except Exception as e:
                messagebox.showerror("Error", f"Could not create: {e}")
                return
        else:
            return

    ret, frame = cam.read()
    if not ret:
        messagebox.showerror("Error", "Failed to access the camera")
        return

    # Check if face is detected before saving
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
    face_locations = face_recognition.face_locations(rgb_frame)
    
    if len(face_locations) == 0:
        messagebox.showerror("Error", "No face detected! Please ensure your face is clearly visible.")
        return
    
    if len(face_locations) > 1:
        messagebox.showwarning("Warning", "Multiple faces detected! Please ensure only one person is in frame.")
        return

    face_path = f"employee_faces/{emp_id}.jpg"
    cv2.imwrite(face_path, frame)

    # Encode
    image = face_recognition.load_image_file(face_path)
    face_encodings = face_recognition.face_encodings(image, face_locations, num_jitters=50) # Moderate jitter for speed/quality balance

    if len(face_encodings) > 0:
        encoding = face_encodings[0]
        encoding_blob = encoding.tobytes()

        cursor.execute("UPDATE employees SET face_encoding=?, name=? WHERE id=?", (encoding_blob, name, emp_id))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", f"Face registered for {name} (ID: {emp_id})")
        root.destroy()
    else:
        messagebox.showerror("Error", "Encoding failed. Try again.")
        conn.close()
        if os.path.exists(face_path): os.remove(face_path)

# Capture Button
CustomButton(inner, text="📸 Capture & Register", command=capture_face, bg=theme['success'], width=30).pack(pady=20)

def on_closing():
    if cam.isOpened():
        cam.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    root.attributes("-alpha", 1.0)
    root.mainloop()
