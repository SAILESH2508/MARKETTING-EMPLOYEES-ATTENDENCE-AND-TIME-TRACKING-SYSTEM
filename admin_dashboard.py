import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
from manage_salaries import SalaryManager
from dashboard_modules.ui_helpers import theme, RoundedFrame, CustomButton, apply_treeview_style
import hashlib

# ORIGINAL DARK THEME COLORS
BG_COLOR = "#0A192F"
FG_COLOR = "white"
BUTTON_COLOR = "#4CAF50"
BUTTON_HOVER = "#388E3C"
CARD_COLOR = "#172A45"
INPUT_BG = "#0D1E36"
LOGIN_BTN_COLOR = "#FFB300"
LOGIN_BTN_HOVER = "#FFA000"

# Fonts
HEADER_FONT = ("Segoe UI", 26, "bold")
TITLE_FONT = ("Segoe UI", 16, "bold")
BODY_FONT = ("Segoe UI", 11)
BUTTON_FONT = ("Segoe UI", 11, "bold")

ADMIN_ID = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def btn_config(btn, bg=None, width=15):
    bg_color = bg if bg else BUTTON_COLOR
    
    # Map buttons to original color hover values
    if bg_color == BUTTON_COLOR:
        hover_color = BUTTON_HOVER
    elif bg_color == LOGIN_BTN_COLOR:
        hover_color = LOGIN_BTN_HOVER
    elif bg_color == "#2196F3":  # Update blue
        hover_color = "#1976D2"
    elif bg_color == "#F44336":  # Delete red
        hover_color = "#D32F2F"
    elif bg_color == "#4CAF50":  # Success green
        hover_color = "#388E3C"
    else:
        hover_color = BUTTON_HOVER

    btn.config(
        font=BUTTON_FONT,
        bg=bg_color,
        fg="black" if bg_color == LOGIN_BTN_COLOR else "white",
        activebackground=hover_color,
        activeforeground="black" if bg_color == LOGIN_BTN_COLOR else "white",
        width=width,
        height=1,
        bd=0,
        cursor="hand2",
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))


# =======================
# MODULES
# =======================
def open_manage_salary(root):
    try:
        SalaryManager(root)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open salary management: {e}")


def view_attendance():
    att_win = tk.Toplevel()
    att_win.title("Attendance Records")
    att_win.geometry("1100x750")
    att_win.configure(bg=BG_COLOR)

    # Header
    tk.Label(
        att_win, text="Attendance Registry", font=HEADER_FONT, bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=20)

    # Search Bar
    search_frame = tk.Frame(att_win, bg=BG_COLOR)
    search_frame.pack(pady=10)

    tk.Label(
        search_frame, text="Search Name:", font=BODY_FONT, bg=BG_COLOR, fg=FG_COLOR
    ).pack(side="left", padx=10)
    search_var = tk.StringVar()
    entry = tk.Entry(
        search_frame,
        textvariable=search_var,
        font=BODY_FONT,
        width=30,
        bg=INPUT_BG,
        fg=FG_COLOR,
        insertbackground=FG_COLOR,
    )
    entry.pack(side="left", padx=10)

    # Treeview Style
    style = ttk.Style()
    apply_treeview_style(style)

    def refresh_attendance():
        search_term = search_var.get()
        conn = sqlite3.connect("attendance_system.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM attendance WHERE name LIKE ?", ("%" + search_term + "%",)
        )
        rows = cursor.fetchall()
        conn.close()

        for row in tree.get_children():
            tree.delete(row)
        for row in rows:
            # Schema: id, emp_id, name, date, sign_in, sign_out
            db_id, db_emp_id, db_name, db_date, db_in, db_out = row
            # Display: ID, Name, Date, In, Out, Notes
            tree.insert("", "end", values=(db_id, db_name, db_date, db_in, db_out, ""))

    s_btn = tk.Button(search_frame, text="Search", command=refresh_attendance)
    btn_config(s_btn, width=10)
    s_btn.pack(side="left", padx=10)

    # Treeview
    columns = ("ID", "Name", "Date", "Sign In", "Sign Out", "Notes")
    tree_frame = tk.Frame(att_win, bg=BG_COLOR)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

    tree = ttk.Treeview(
        tree_frame, columns=columns, show="headings", style="Dark.Treeview"
    )

    # Scrollbars
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    # Alignment Fix: ID Center, Name/Notes Left, Others Center
    tree.heading("ID", text="ID")
    tree.column("ID", width=60, anchor="center")
    tree.heading("Name", text="Name")
    tree.column("Name", width=150, anchor="w")
    tree.heading("Date", text="Date")
    tree.column("Date", width=100, anchor="center")
    tree.heading("Sign In", text="Sign In")
    tree.column("Sign In", width=100, anchor="center")
    tree.heading("Sign Out", text="Sign Out")
    tree.column("Sign Out", width=100, anchor="center")
    tree.heading("Notes", text="Notes")
    tree.column("Notes", width=150, anchor="w")

    refresh_attendance()


def open_manage_employees():
    emp_win = tk.Toplevel()
    emp_win.title("Manage Employees")
    emp_win.geometry("1100x800")
    emp_win.configure(bg=BG_COLOR)

    tk.Label(
        emp_win, text="Employee Management", font=HEADER_FONT, bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=20)

    container = tk.Frame(emp_win, bg=BG_COLOR)
    container.pack(fill="both", expand=True, padx=20, pady=10)

    # Treeview Style (Ensure consistent)
    style = ttk.Style()
    apply_treeview_style(style)

    # Left Form
    form_frame = tk.Frame(container, bg=CARD_COLOR, width=350, padx=20, pady=20)
    form_frame.pack(side="left", fill="y", padx=10)

    tk.Label(
        form_frame, text="Employee Details", font=TITLE_FONT, bg=CARD_COLOR, fg=FG_COLOR
    ).pack(pady=(0, 20))

    entries = {}
    for label in ["ID", "Name", "Role", "Password"]:
        tk.Label(
            form_frame, text=label, font=("Arial", 10), bg=CARD_COLOR, fg="#8892B0"
        ).pack(anchor="w", pady=(10, 0))
        e = tk.Entry(
            form_frame,
            font=BODY_FONT,
            show="*" if label == "Password" else "",
            bg=INPUT_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            relief="flat",
        )
        e.pack(fill="x", pady=5)
        entries[label.lower()] = e

    def get_vals():
        return (
            entries["id"].get(),
            entries["name"].get(),
            entries["role"].get(),
            entries["password"].get(),
        )

    def clear_entries():
        for e in entries.values():
            e.delete(0, tk.END)

    def refresh_employees():
        conn = sqlite3.connect("attendance_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role FROM employees")
        rows = cursor.fetchall()
        conn.close()
        for r in tree.get_children():
            tree.delete(r)
        for r in rows:
            tree.insert("", "end", values=r)

    def add_emp():
        eid, name, role, pwd = get_vals()
        if not eid or not name:
            return messagebox.showerror("Error", "ID and Name required")
        try:
            conn = sqlite3.connect("attendance_system.db")
            conn.execute(
                "INSERT INTO employees (id, name, role, password) VALUES (?, ?, ?, ?)",
                (int(eid), name, role, hash_password(pwd)),
            )
            conn.commit()
            conn.close()
            refresh_employees()
            clear_entries()
            messagebox.showinfo("Success", "Added")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_emp():
        eid, name, role, pwd = get_vals()
        try:
            conn = sqlite3.connect("attendance_system.db")
            conn.execute(
                "UPDATE employees SET name=?, role=?, password=? WHERE id=?",
                (name, role, hash_password(pwd), int(eid)),
            )
            conn.commit()
            conn.close()
            refresh_employees()
            clear_entries()
            messagebox.showinfo("Success", "Updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def del_emp():
        eid = entries["id"].get()
        if not eid:
            return
        if messagebox.askyesno("Confirm", "Delete this employee?"):
            try:
                conn = sqlite3.connect("attendance_system.db")
                conn.execute("DELETE FROM employees WHERE id=?", (int(eid),))
                conn.commit()
                conn.close()
                refresh_employees()
                clear_entries()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    btn_box = tk.Frame(form_frame, bg=CARD_COLOR)
    btn_box.pack(pady=20, fill="x")

    b1 = tk.Button(btn_box, text="Add", command=add_emp)
    btn_config(b1, "#4CAF50", 8)
    b1.pack(side="left", padx=5)

    b2 = tk.Button(btn_box, text="Update", command=update_emp)
    btn_config(b2, "#2196F3", 8)
    b2.pack(side="left", padx=5)

    b3 = tk.Button(btn_box, text="Delete", command=del_emp)
    btn_config(b3, "#F44336", 8)
    b3.pack(side="left", padx=5)

    # Right List
    list_frame = tk.Frame(container, bg=BG_COLOR)
    list_frame.pack(side="right", fill="both", expand=True, padx=10)

    columns = ("ID", "Name", "Role")
    tree = ttk.Treeview(
        list_frame, columns=columns, show="headings", style="Dark.Treeview"
    )

    # Scrollbars for Employee Table
    vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")

    # Alignment Fix: ID Center, Name/Role Left
    tree.heading("ID", text="ID")
    tree.column("ID", width=50, anchor="center")
    tree.heading("Name", text="Name")
    tree.column("Name", width=150, anchor="w")
    tree.heading("Role", text="Role")
    tree.column("Role", width=120, anchor="w")

    tree.pack(fill="both", expand=True)
    refresh_employees()


def open_dashboard(root):
    for widget in root.winfo_children():
        widget.destroy()

    root.configure(bg=BG_COLOR)

    # Header
    tk.Label(
        root, text="ADMIN DASHBOARD", font=("Segoe UI", 26, "bold"), bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=(50, 5))
    tk.Label(
        root, text="Control Panel", font=("Segoe UI Semibold", 12), bg=BG_COLOR, fg="#8892B0"
    ).pack(pady=(0, 25))

    # Menu using RoundedFrame
    menu_container = RoundedFrame(root, width=450, height=360, bg_color=CARD_COLOR)
    menu_container.pack(pady=10)
    menu_frame = menu_container.inner_frame

    buttons = [
        ("📅  View Attendance", view_attendance),
        ("👥  Manage Employees", open_manage_employees),
        ("💰  Manage Salaries", lambda: open_manage_salary(root)),
    ]

    for text, cmd in buttons:
        b = tk.Button(menu_frame, text=text, command=cmd)
        btn_config(b, BUTTON_COLOR, 25)
        b.config(height=2)
        b.pack(pady=10)

    def logout():
        root.destroy()
        launch_admin_dashboard()

    b_out = tk.Button(menu_frame, text="🚪 Logout", command=logout)
    btn_config(b_out, "#1E3A8A", 25)
    b_out.config(height=2)
    b_out.bind("<Enter>", lambda e: e.widget.config(bg="#172554"))
    b_out.bind("<Leave>", lambda e: e.widget.config(bg="#1E3A8A"))
    b_out.pack(pady=15)


def login(entry_id, entry_pwd, root):
    if (
        entry_id.get() == ADMIN_ID
        and hash_password(entry_pwd.get()) == ADMIN_PASSWORD_HASH
    ):
        open_dashboard(root)
    else:
        messagebox.showerror("Access Denied", "Invalid credentials")


def launch_admin_dashboard():
    root = tk.Tk()
    root.title("Admin Portal")
    root.geometry("800x600")
    root.configure(bg=BG_COLOR)

    # Center
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"800x600+{int(sw/2-400)}+{int(sh/2-300)}")

    # Header
    tk.Label(
        root, text="ADMIN LOGIN", font=("Segoe UI", 26, "bold"), bg=BG_COLOR, fg=FG_COLOR
    ).pack(pady=(80, 30))

    # Form container using RoundedFrame
    login_container = RoundedFrame(root, width=400, height=300, bg_color=CARD_COLOR)
    login_container.pack(pady=10)
    login_frame = login_container.inner_frame

    tk.Label(
        login_frame, text="Admin ID", font=("Segoe UI", 11, "bold"), bg=CARD_COLOR, fg=FG_COLOR
    ).pack(anchor="w", padx=10, pady=(15, 0))
    e_id = tk.Entry(
        login_frame,
        font=("Segoe UI", 12),
        bg=INPUT_BG,
        fg=FG_COLOR,
        insertbackground=FG_COLOR,
        relief="flat",
    )
    e_id.pack(fill="x", pady=(5, 15), padx=10)

    tk.Label(
        login_frame, text="Password", font=("Segoe UI", 11, "bold"), bg=CARD_COLOR, fg=FG_COLOR
    ).pack(anchor="w", padx=10)
    e_pass = tk.Entry(
        login_frame,
        font=("Segoe UI", 12),
        show="•",
        bg=INPUT_BG,
        fg=FG_COLOR,
        insertbackground=FG_COLOR,
        relief="flat",
    )
    e_pass.pack(fill="x", pady=(5, 20), padx=10)

    b_login = tk.Button(
        login_frame, text="UNLOCK", command=lambda: login(e_id, e_pass, root)
    )
    btn_config(b_login, LOGIN_BTN_COLOR, 20)
    b_login.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    launch_admin_dashboard()
