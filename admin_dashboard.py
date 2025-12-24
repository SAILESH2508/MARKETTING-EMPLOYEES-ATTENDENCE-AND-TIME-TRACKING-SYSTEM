import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import subprocess
import hashlib

ADMIN_ID = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

# Colors and Fonts (Increased font sizes)
BG_COLOR = "#263238"
BTN_COLOR = "#4CAF50"
BTN_HIGHLIGHT = "#FFB300"
FONT_LARGE = ("Arial", 20, "bold")
FONT_MEDIUM = ("Arial", 14)
FONT_SMALL = ("Arial", 12)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def open_manage_salary():
    try:
        subprocess.Popen(["python", "manage_salaries.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open salary management: {e}")

def view_attendance():
    def refresh_attendance():
        search_term = search_var.get()
        conn = sqlite3.connect("attendance_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance WHERE name LIKE ?", ('%' + search_term + '%',))
        rows = cursor.fetchall()
        conn.close()
        
        # Clear existing data
        for row in tree.get_children():
            tree.delete(row)
        
        # Insert the fetched data into the Treeview
        for row in rows:
            tree.insert("", "end", values=row)

    att_win = tk.Toplevel()
    att_win.title("Attendance Records")
    att_win.geometry("800x500")
    att_win.config(bg=BG_COLOR)

    tk.Label(att_win, text="Search by Name:", bg=BG_COLOR, fg="white", font=FONT_MEDIUM).pack()
    search_var = tk.StringVar()
    tk.Entry(att_win, textvariable=search_var, font=FONT_MEDIUM, width=30).pack()
    tk.Button(att_win, text="Search", font=FONT_SMALL, bg=BTN_COLOR, fg="white", command=refresh_attendance).pack(pady=5)
    tk.Button(att_win, text="Back", font=FONT_MEDIUM, bg="#607D8B", fg="white", command=att_win.destroy).pack(pady=10)

    columns = ("ID", "Name", "Date", "Time", "Status", "Notes")
    tree = ttk.Treeview(att_win, columns=columns, show="headings", height=15)
    
    for col in columns:
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=150, anchor="w")

    tree.pack(pady=10, padx=10)
    refresh_attendance()

def open_manage_employees():
    def refresh_employees():
        name_filter = search_var.get()
        conn = sqlite3.connect("attendance_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role FROM employees WHERE name LIKE ?", ('%' + name_filter + '%',))
        employees = cursor.fetchall()
        conn.close()
        
        # Clear existing data
        for row in tree.get_children():
            tree.delete(row)
        
        # Insert the fetched data into the Treeview
        for emp in employees:
            tree.insert("", "end", values=emp)

    def clear_entries():
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)
        entry_role.delete(0, tk.END)
        entry_password.delete(0, tk.END)

    def add_employee():
        try:
            conn = sqlite3.connect("attendance_system.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO employees (id, name, role, password) VALUES (?, ?, ?, ?)", (
                int(entry_id.get()), entry_name.get(), entry_role.get(), hash_password(entry_password.get())
            ))
            conn.commit()
            conn.close()
            refresh_employees()
            clear_entries()
            messagebox.showinfo("Success", "Employee added successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_employee():
        try:
            conn = sqlite3.connect("attendance_system.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE employees SET name=?, role=?, password=? WHERE id=?", (
                entry_name.get(), entry_role.get(), hash_password(entry_password.get()), int(entry_id.get())
            ))
            conn.commit()
            conn.close()
            refresh_employees()
            clear_entries()
            messagebox.showinfo("Success", "Employee updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_employee():
        try:
            conn = sqlite3.connect("attendance_system.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE id=?", (int(entry_id.get()),))
            conn.commit()
            conn.close()
            refresh_employees()
            clear_entries()
            messagebox.showinfo("Success", "Employee deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    emp_win = tk.Toplevel()
    emp_win.title("Manage Employees")
    emp_win.geometry("800x600")
    emp_win.config(bg=BG_COLOR)

    search_var = tk.StringVar()
    tk.Label(emp_win, text="Search by Name:", bg=BG_COLOR, fg="white", font=FONT_MEDIUM).pack()
    tk.Entry(emp_win, textvariable=search_var, font=FONT_MEDIUM, width=30).pack()
    tk.Button(emp_win, text="Search", font=FONT_SMALL, bg=BTN_COLOR, fg="white", command=refresh_employees).pack(pady=5)

    columns = ("ID", "Name", "Role")
    tree = ttk.Treeview(emp_win, columns=columns, show="headings", height=15)
    
    for col in columns:
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=150, anchor="w")

    tree.pack(pady=10, padx=10)

    form_frame = tk.Frame(emp_win, bg=BG_COLOR)
    form_frame.pack(pady=10)

    labels = ["ID", "Name", "Role", "Password"]
    for i, label in enumerate(labels):
        tk.Label(form_frame, text=label, font=FONT_SMALL, bg=BG_COLOR, fg="white").grid(row=0, column=i, padx=10)

    entry_id = tk.Entry(form_frame, width=10, font=FONT_SMALL)
    entry_id.grid(row=1, column=0, padx=5)

    entry_name = tk.Entry(form_frame, width=20, font=FONT_SMALL)
    entry_name.grid(row=1, column=1, padx=5)

    entry_role = tk.Entry(form_frame, width=20, font=FONT_SMALL)
    entry_role.grid(row=1, column=2, padx=5)

    entry_password = tk.Entry(form_frame, width=15, font=FONT_SMALL, show="*")
    entry_password.grid(row=1, column=3, padx=5)

    btn_frame = tk.Frame(emp_win, bg=BG_COLOR)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Add", width=12, bg="#388E3C", fg="white", font=FONT_MEDIUM, command=add_employee).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Update", width=12, bg="#1976D2", fg="white", font=FONT_MEDIUM, command=update_employee).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Delete", width=12, bg="#D32F2F", fg="white", font=FONT_MEDIUM, command=delete_employee).pack(side=tk.LEFT, padx=10)
    tk.Button(emp_win, text="Back", font=FONT_MEDIUM, bg="#607D8B", fg="white", command=emp_win.destroy).pack(pady=10)

    refresh_employees()

def login(entry_id, entry_password, login_frame, root):
    if entry_id.get() == ADMIN_ID and hash_password(entry_password.get()) == ADMIN_PASSWORD_HASH:
        login_frame.destroy()
        open_dashboard(root)
    else:
        messagebox.showerror("Login Failed", "Invalid admin credentials.")

def open_dashboard(root):
    dashboard = tk.Frame(root, bg=BG_COLOR)
    dashboard.pack(pady=20, fill="both", expand=True)

    def logout():
        dashboard.destroy()
        launch_admin_dashboard()

    tk.Label(dashboard, text="ADMIN DASHBOARD", font=FONT_LARGE, fg="white", bg=BG_COLOR).pack(pady=20)

    buttons = [
        ("View Attendance", view_attendance),
        ("Manage Employees", open_manage_employees),
        ("Manage Salaries", open_manage_salary),
    ]

    for text, cmd in buttons:
        tk.Button(dashboard, text=text, width=30, height=2, font=FONT_MEDIUM, bg="red", fg="white", command=cmd).pack(pady=10)

    # Add logout button at the bottom
    tk.Button(dashboard, text="Logout", width=15, font=FONT_MEDIUM, bg="#FFC107", fg="black", command=logout).pack(pady=30)


def launch_admin_dashboard():
    root = tk.Tk()
    root.title("Admin Login - Attendance System")
    root.geometry("400x500")
    root.config(bg=BG_COLOR)

    login_frame = tk.Frame(root, bg=BG_COLOR)
    login_frame.pack(pady=50)

    tk.Label(login_frame, text="Admin", font=("Arial", 12), bg="#263238", fg="white").pack(pady=10)
    entry_id = tk.Entry(login_frame, font=("Arial", 12))
    entry_id.pack(pady=5)

    tk.Label(login_frame, text="Password", font=("Arial", 12), bg="#263238", fg="white").pack(pady=10)
    entry_password = tk.Entry(login_frame, show="*", font=("Arial", 12))
    entry_password.pack(pady=5)

    tk.Button(login_frame, text="Login", width=15, font=FONT_MEDIUM, bg=BTN_HIGHLIGHT, fg="black",
          command=lambda: login(entry_id, entry_password, login_frame, root)).pack(pady=20)

    root.mainloop()

# Run it
if __name__ == "__main__":
    launch_admin_dashboard()

