import cv2
import face_recognition
import numpy as np
import sqlite3
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

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
root.geometry("600x600")
root.configure(bg="#263238")

tk.Label(root, text="Employee Face Registration", font=("Arial", 16, "bold"), bg="#263238", fg="white").pack(pady=10)

# Employee ID Entry
tk.Label(root, text="Employee ID:", font=("Arial", 12), bg="#263238", fg="white").pack(pady=5)
emp_id_entry = tk.Entry(root, font=("Arial", 12))
emp_id_entry.pack(pady=5)

# Employee Name Entry
tk.Label(root, text="Employee Name:", font=("Arial", 12), bg="#263238", fg="white").pack(pady=5)
name_entry = tk.Entry(root, font=("Arial", 12))
name_entry.pack(pady=5)

# Camera Preview Frame
camera_frame = tk.Label(root, bg="black", width=500, height=300)
camera_frame.pack(pady=10)

# Initialize Camera
cam = cv2.VideoCapture(0)

def show_frame():
    ret, frame = cam.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_frame.imgtk = imgtk
        camera_frame.configure(image=imgtk)
        camera_frame.after(10, show_frame)

show_frame()  # Start preview

def capture_face():
    emp_id = emp_id_entry.get().strip()
    name = name_entry.get().strip()

    if not emp_id or not name:
        messagebox.showerror("Error", "Please enter Employee ID and Name")
        return

    # Check if Employee exists
    cursor.execute("SELECT id FROM employees WHERE id=?", (emp_id,))
    if not cursor.fetchone():
        messagebox.showerror("Error", "Employee ID not found! Please add the employee first.")
        return

    ret, frame = cam.read()
    if not ret:
        messagebox.showerror("Error", "Failed to access the camera")
        return

    face_path = f"employee_faces/{emp_id}.jpg"
    cv2.imwrite(face_path, frame)

    messagebox.showinfo("Success", "Face Captured Successfully!")
    encode_face(emp_id, face_path)

def encode_face(emp_id, face_path):
    image = face_recognition.load_image_file(face_path)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) > 0:
        encoding = face_encodings[0]

        if encoding.shape != (128,):
            messagebox.showerror("Error", "Invalid face encoding shape!")
            os.remove(face_path)
            return

        encoding_blob = encoding.tobytes()

        cursor.execute("UPDATE employees SET face_encoding=? WHERE id=?", (encoding_blob, emp_id))
        conn.commit()

        messagebox.showinfo("Success", "Employee Registered with Face Successfully!")
    else:
        messagebox.showerror("Error", "No face detected! Try again.")
        os.remove(face_path)

# Capture Button
tk.Button(root, text="Capture Face", font=("Arial", 14), bg="green", fg="white", command=capture_face).pack(pady=20)

def on_closing():
    cam.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
