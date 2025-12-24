import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import *
import sqlite3
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Initialize main window
root = tk.Tk()
root.title("Salary Manager with Charts")
root.geometry("1050x700")
root.configure(bg="#1E2A47")

# Fonts
label_font = ("Arial", 12, "bold")
entry_font = ("Arial", 12)

# Database setup
def init_db():
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS salary (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            salary REAL,
            bonus REAL,
            deductions REAL,
            net_salary REAL
        )
    ''')
    conn.commit()
    conn.close()

# CRUD Operations
def add_salary():
    try:
        emp_id = emp_id_entry.get()
        name = name_entry.get()
        salary = float(salary_entry.get())
        bonus = float(bonus_entry.get())
        deductions = float(deductions_entry.get())
        net_salary = salary + bonus - deductions

        conn = sqlite3.connect("attendance_system.db")
        c = conn.cursor()
        c.execute("INSERT INTO salary VALUES (?, ?, ?, ?, ?, ?)",
                  (emp_id, name, salary, bonus, deductions, net_salary))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Salary record added.")
        fetch_all()
        clear_entries()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_salary():
    try:
        emp_id = emp_id_entry.get()
        name = name_entry.get()
        salary = float(salary_entry.get())
        bonus = float(bonus_entry.get())
        deductions = float(deductions_entry.get())
        net_salary = salary + bonus - deductions

        conn = sqlite3.connect("attendance_system.db")
        c = conn.cursor()
        c.execute("UPDATE salary SET name=?, salary=?, bonus=?, deductions=?, net_salary=? WHERE emp_id=?",
                  (name, salary, bonus, deductions, net_salary, emp_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Updated", "Salary record updated.")
        fetch_all()
        clear_entries()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_salary():
    emp_id = emp_id_entry.get()
    if not emp_id:
        messagebox.showwarning("Input Required", "Please enter Employee ID.")
        return
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("DELETE FROM salary WHERE emp_id=?", (emp_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Deleted", "Salary record deleted.")
    fetch_all()
    clear_entries()

def fetch_all():
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM salary")
    rows = c.fetchall()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", END, values=row)
    conn.close()

def clear_entries():
    emp_id_entry.delete(0, END)
    name_entry.delete(0, END)
    salary_entry.delete(0, END)
    bonus_entry.delete(0, END)
    deductions_entry.delete(0, END)

def on_row_select(event):
    selected = tree.focus()
    if selected:
        values = tree.item(selected, 'values')
        emp_id_entry.delete(0, END)
        emp_id_entry.insert(0, values[0])
        name_entry.delete(0, END)
        name_entry.insert(0, values[1])
        salary_entry.delete(0, END)
        salary_entry.insert(0, values[2])
        bonus_entry.delete(0, END)
        bonus_entry.insert(0, values[3])
        deductions_entry.delete(0, END)
        deductions_entry.insert(0, values[4])

def search():
    keyword = search_entry.get().strip()
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM salary WHERE emp_id LIKE ? OR name LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
    rows = c.fetchall()
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", END, values=row)
    conn.close()

def export_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM salary")
    rows = c.fetchall()
    conn.close()
    with open(file_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Emp ID", "Name", "Salary", "Bonus", "Deductions", "Net Salary"])
        writer.writerows(rows)
    messagebox.showinfo("Exported", f"Data exported to {file_path}")

def show_highest_paid():
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT * FROM salary ORDER BY net_salary DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        messagebox.showinfo("Top Earner", f"ID: {row[0]}\nName: {row[1]}\nNet Salary: {row[5]}")

# Charts
def draw_pie_chart():
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT name, net_salary FROM salary")
    data = c.fetchall()
    conn.close()

    if not data:
        messagebox.showwarning("No Data", "No salary data available.")
        return

    names = [row[0] for row in data]
    net_salaries = [row[1] for row in data]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(net_salaries, labels=names, autopct='%1.1f%%', startangle=140)
    ax.set_title("Net Salary Distribution")

    for widget in chart_canvas_frame.winfo_children():
        widget.destroy()

    chart_canvas = FigureCanvasTkAgg(fig, master=chart_canvas_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack()

def draw_bar_chart():
    conn = sqlite3.connect("attendance_system.db")
    c = conn.cursor()
    c.execute("SELECT name, salary, bonus, deductions FROM salary")
    data = c.fetchall()
    conn.close()

    if not data:
        messagebox.showwarning("No Data", "No salary data available.")
        return

    names = [row[0] for row in data]
    salaries = [row[1] for row in data]
    bonuses = [row[2] for row in data]
    deductions = [row[3] for row in data]

    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(names))
    ax.bar(x, salaries, label="Salary")
    ax.bar(x, bonuses, bottom=salaries, label="Bonus")
    ax.bar(x, deductions, bottom=[salaries[i] + bonuses[i] for i in range(len(salaries))], label="Deductions", color='red')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.set_title("Salary Components")
    ax.legend()

    for widget in chart_canvas_frame.winfo_children():
        widget.destroy()

    chart_canvas = FigureCanvasTkAgg(fig, master=chart_canvas_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack()

# --- UI Components ---
form_frame = Frame(root, bg="#1E2A47")
form_frame.pack(pady=10)

# Labels and Entries
Label(form_frame, text="Employee ID:", font=label_font, bg="#1E2A47", fg="white").grid(row=0, column=0, padx=10, pady=5, sticky=W)
emp_id_entry = Entry(form_frame, font=entry_font)
emp_id_entry.grid(row=0, column=1, padx=10, pady=5)

Label(form_frame, text="Name:", font=label_font, bg="#1E2A47", fg="white").grid(row=0, column=2, padx=10, pady=5, sticky=W)
name_entry = Entry(form_frame, font=entry_font)
name_entry.grid(row=0, column=3, padx=10, pady=5)

Label(form_frame, text="Salary:", font=label_font, bg="#1E2A47", fg="white").grid(row=1, column=0, padx=10, pady=5, sticky=W)
salary_entry = Entry(form_frame, font=entry_font)
salary_entry.grid(row=1, column=1, padx=10, pady=5)

Label(form_frame, text="Bonus:", font=label_font, bg="#1E2A47", fg="white").grid(row=1, column=2, padx=10, pady=5, sticky=W)
bonus_entry = Entry(form_frame, font=entry_font)
bonus_entry.grid(row=1, column=3, padx=10, pady=5)

Label(form_frame, text="Deductions:", font=label_font, bg="#1E2A47", fg="white").grid(row=2, column=0, padx=10, pady=5, sticky=W)
deductions_entry = Entry(form_frame, font=entry_font)
deductions_entry.grid(row=2, column=1, padx=10, pady=5)

# Buttons
btn_frame = Frame(root, bg="#1E2A47")
btn_frame.pack(pady=10)

Button(btn_frame, text="Add", command=add_salary, width=12, font=entry_font, bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)
Button(btn_frame, text="Update", command=update_salary, width=12, font=entry_font, bg="#FFC107", fg="black").grid(row=0, column=1, padx=5)
Button(btn_frame, text="Delete", command=delete_salary, width=12, font=entry_font, bg="#F44336", fg="white").grid(row=0, column=2, padx=5)
Button(btn_frame, text="Clear", command=clear_entries, width=12, font=entry_font, bg="#9E9E9E", fg="white").grid(row=0, column=3, padx=5)
Button(btn_frame, text="Export CSV", command=export_csv, width=12, font=entry_font, bg="#7B1FA2", fg="white").grid(row=0, column=4, padx=5)
Button(btn_frame, text="Top Earner", command=show_highest_paid, width=12, font=entry_font, bg="#455A64", fg="white").grid(row=0, column=5, padx=5)
Button(btn_frame, text="Exit", command=root.quit, width=12, font=entry_font, bg="#607D8B", fg="white").grid(row=0, column=4, padx=5)

# Search bar
search_frame = Frame(root, bg="#1E2A47", pady=10)
search_frame.pack()

Label(search_frame, text="Search by Name/ID: ", font=label_font, bg="#1E2A47", fg="white").pack(side=LEFT, padx=10)
search_entry = Entry(search_frame, font=entry_font, width=30)
search_entry.pack(side=LEFT, padx=5)
Button(search_frame, text="Search", command=search, font=entry_font, bg="#0288D1", fg="white").pack(side=LEFT, padx=5)
Button(search_frame, text="Show All", command=fetch_all, font=entry_font, bg="#009688", fg="white").pack(side=LEFT, padx=5)

# Treeview
tree_frame = Frame(root, bg="#1E2A47")
tree_frame.pack(pady=10)

columns = ("emp_id", "name", "salary", "bonus", "deductions", "net_salary")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
for col in columns:
    tree.heading(col, text=col.capitalize())
    tree.column(col, width=150, anchor=CENTER)
tree.pack(side=LEFT, padx=10)
tree.bind("<ButtonRelease-1>", on_row_select)

scrollbar = Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
scrollbar.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=scrollbar.set)

# Chart Buttons
chart_btn_frame = Frame(root, bg="#1E2A47")
chart_btn_frame.pack(pady=10)

Button(chart_btn_frame, text="Pie Chart", command=draw_pie_chart, font=entry_font, bg="#FF7043", fg="white", width=15).pack(side=LEFT, padx=10)
Button(chart_btn_frame, text="Bar Chart", command=draw_bar_chart, font=entry_font, bg="#29B6F6", fg="white", width=15).pack(side=LEFT, padx=10)

# Chart Display Frame
chart_canvas_frame = Frame(root, bg="#1E2A47")
chart_canvas_frame.pack(pady=10)

# Initialize DB and run
init_db()
fetch_all()
root.mainloop()
