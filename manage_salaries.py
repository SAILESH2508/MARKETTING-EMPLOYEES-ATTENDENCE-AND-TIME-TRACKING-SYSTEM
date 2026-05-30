import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="mplcursors")

import os
import math
import sqlite3
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import BOTH, LEFT, RIGHT, Y, X, CENTER, W, E, END, BOTTOM, HORIZONTAL, VERTICAL, TOP
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # type: ignore
from PIL import Image, ImageTk

try:
    from dashboard_modules.ui_helpers import (
        theme,
        HEADER_FONT,
        BODY_FONT,
        BUTTON_FONT,
        TITLE_FONT,
        SMALL_FONT,
        CustomButton,
        RoundedFrame,
        apply_treeview_style,
    )
except ImportError:
    # Fallback if run standalone and path issues
    from ui_helpers import (
        theme,
        HEADER_FONT,
        BODY_FONT,
        BUTTON_FONT,
        TITLE_FONT,
        SMALL_FONT,
        CustomButton,
        RoundedFrame,
        apply_treeview_style,
    )

# ---------------------------
# Theme & Constants
# ---------------------------
DB_PATH = "attendance_system.db"
ICONS_DIR = "icons"

# THEME COLORS (Mapped from global theme)
BG = theme["bg"]
FG = theme["fg"]
ACCENT = theme["button"]
CARD_COLOR = theme["card"]
TEXT_SECONDARY = theme["text_secondary"]
INPUT_BG = theme.get("card_border", "#1E2943")

# Chart configs
PIE_TOP_N = 8
PIE_MIN_LABEL_PCT = 3.0

# Matplotlib global theme
plt.rcParams.update(
    {
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "axes.edgecolor": TEXT_SECONDARY,
        "axes.labelcolor": FG,
        "xtick.color": FG,
        "ytick.color": FG,
        "text.color": FG,
        "legend.facecolor": BG,
        "legend.edgecolor": TEXT_SECONDARY,
        "figure.autolayout": True,
    }
)


def style_btn(btn, bg_color, hover_color, fg_color="white", width=12, height=1):
    btn.config(
        font=BUTTON_FONT,
        bg=bg_color,
        fg=fg_color,
        activebackground=hover_color,
        activeforeground=fg_color,
        width=width,
        height=height,
        bd=0,
        cursor="hand2",
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))


class SalaryManager:
    root: tk.Tk | tk.Toplevel

    def __init__(self, root=None):
        if root:
            self.root = tk.Toplevel(root)
        else:
            self.root = tk.Tk()

        self.root.title("Salary Manager")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG)

        # Style Configuration
        self.style = ttk.Style()
        apply_treeview_style(self.style)

        # Initialize DB
        self.init_db()
        self.recalculate_net_salaries()

        # Build UI
        self.build_ui()
        self.fetch_all()

        if not root:
            self.root.mainloop()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS salary (
                emp_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                salary REAL,
                bonus REAL,
                deductions REAL,
                net_salary REAL
            )
        """
        )
        conn.commit()
        conn.close()

    def recalculate_net_salaries(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT emp_id, salary, bonus, deductions FROM salary")
        rows = c.fetchall()
        for emp_id, salary, bonus, deductions in rows:
            try:
                s = float(salary or 0)
            except:
                s = 0.0
            try:
                b = float(bonus or 0)
            except:
                b = 0.0
            try:
                d = float(deductions or 0)
            except:
                d = 0.0
            net = s + b - d
            c.execute(
                "UPDATE salary SET net_salary = ? WHERE emp_id = ?", (net, emp_id)
            )
        conn.commit()
        conn.close()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(pady=20)
        tk.Label(
            header, text="Salary Management", font=HEADER_FONT, bg=BG, fg=FG
        ).pack()

        # Actions Grid
        action_frame = RoundedFrame(
            self.root, width=1200, height=100, bg_color=CARD_COLOR
        )
        action_frame.pack(pady=10)
        inner_act = action_frame.inner_frame

        b_pie = tk.Button(inner_act, text="🥧 View Pie Chart", command=self.draw_pie_chart)
        style_btn(b_pie, "#7B1FA2", "#6A1B9A", width=20, height=2)
        b_pie.grid(row=0, column=0, padx=20, pady=20)

        b_bar = tk.Button(inner_act, text="📊 View Bar Chart", command=self.draw_bar_chart)
        style_btn(b_bar, "#0288D1", "#0277BD", width=20, height=2)
        b_bar.grid(row=0, column=1, padx=20, pady=20)

        b_export = tk.Button(inner_act, text="📥 Export CSV", command=self.export_csv)
        style_btn(b_export, "#5D4037", "#4E342E", width=20, height=2)
        b_export.grid(row=0, column=2, padx=20, pady=20)

        b_top = tk.Button(inner_act, text="🏆 Top Earner", command=self.show_highest_paid)
        style_btn(b_top, "#512DA8", "#4527A0", width=20, height=2)
        b_top.grid(row=0, column=3, padx=20, pady=20)

        # Main Content
        content_frame = tk.Frame(self.root, bg=BG)
        content_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        # Left: Form
        self.build_form(content_frame)

        # Right: Table
        self.build_table(content_frame)

    def build_form(self, parent):
        form_container = RoundedFrame(
            parent, width=400, height=500, bg_color=CARD_COLOR
        )
        form_container.pack(side=LEFT, fill=Y, padx=10)
        f_inner = form_container.inner_frame

        tk.Label(
            f_inner,
            text="Edit Details",
            font=TITLE_FONT,
            bg=CARD_COLOR,
            fg=FG,
        ).pack(pady=15)

        self.inputs = {}
        for field in ["Employee ID", "Name", "Salary", "Bonus", "Deductions"]:
            tk.Label(
                f_inner,
                text=field,
                font=SMALL_FONT,
                bg=CARD_COLOR,
                fg=TEXT_SECONDARY,
            ).pack(anchor="w", padx=20, pady=(10, 0))
            e = tk.Entry(
                f_inner, font=BODY_FONT, bg=INPUT_BG, fg=FG, relief="flat", insertbackground=FG
            )
            e.pack(fill="x", padx=20, pady=5)
            self.inputs[field] = e

        self.emp_id_entry = self.inputs["Employee ID"]
        self.name_entry = self.inputs["Name"]
        self.salary_entry = self.inputs["Salary"]
        self.bonus_entry = self.inputs["Bonus"]
        self.deductions_entry = self.inputs["Deductions"]

        btn_box = tk.Frame(f_inner, bg=CARD_COLOR)
        btn_box.pack(pady=20, fill="x", padx=20)

        b_update = tk.Button(btn_box, text="Update", command=self.update_salary)
        style_btn(b_update, theme["button"], theme["hover"], width=10)
        b_update.pack(side=LEFT, padx=5)

        b_add = tk.Button(btn_box, text="Add", command=self.add_salary)
        style_btn(b_add, theme["success"], "#059669", width=10)
        b_add.pack(side=LEFT, padx=5)

        b_clear = tk.Button(btn_box, text="Clear", command=self.clear_entries)
        style_btn(b_clear, theme["warning"], "#D97706", fg_color="black", width=8)
        b_clear.pack(side=LEFT, padx=5)

    def build_table(self, parent):
        table_container = tk.Frame(parent, bg=BG)
        table_container.pack(side=RIGHT, fill=BOTH, expand=True, padx=10)

        search_box = tk.Frame(table_container, bg=BG)
        search_box.pack(fill=X, pady=(0, 10))
        tk.Label(search_box, text="Search:", font=BODY_FONT, bg=BG, fg=FG).pack(
            side=LEFT
        )
        self.search_entry = tk.Entry(search_box, font=BODY_FONT, bg=INPUT_BG, fg=FG, relief="flat", insertbackground=FG)
        self.search_entry.pack(side=LEFT, padx=10)
        
        b_go = tk.Button(search_box, text="Go", command=self.search)
        style_btn(b_go, theme["button"], theme["hover"], width=5)
        b_go.pack(side=LEFT)

        b_all = tk.Button(search_box, text="Show All", command=self.fetch_all)
        style_btn(b_all, theme["card_border"], "#334155", width=10)
        b_all.pack(side=LEFT, padx=10)

        # Style for Treeview wrapper to handle scrollbars perfectly
        tree_frame = tk.Frame(table_container, bg=CARD_COLOR)
        tree_frame.pack(fill=BOTH, expand=True)

        columns = ("emp_id", "name", "salary", "bonus", "deductions", "net_salary")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", style="Dark.Treeview"
        )

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)
        self.tree.pack(fill=BOTH, expand=True)

        # Configure columns
        for col in columns:
            title = col.replace("_", " ").title()

            # Alignment: ID Center, Name Left, Numbers Right
            if col == "emp_id":
                anchor = CENTER
            elif col == "name":
                anchor = W
            else:
                # Salary, Bonus, Deductions, Net Salary -> Right Aligned
                anchor = E

            self.tree.heading(col, text=title, anchor=anchor)
            self.tree.column(col, width=120, anchor=anchor)

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

    def get_float(self, val):
        try:
            return float(val or 0)
        except:
            return 0.0

    def format_currency(self, val):
        return f"₹{self.get_float(val):,.2f}"

    def fetch_all(self):
        self.tree.delete(*self.tree.get_children())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM salary")
        rows = c.fetchall()
        conn.close()

        for row in rows:
            # Format row data
            emp_id, name, sal, bon, ded, net = row
            display_row = (
                emp_id,
                name,
                self.format_currency(sal),
                self.format_currency(bon),
                self.format_currency(ded),
                self.format_currency(net),
            )
            self.tree.insert("", END, values=display_row)

    def add_salary(self):
        try:
            emp_id = self.emp_id_entry.get().strip()
            if not emp_id:
                return messagebox.showwarning(
                    "Input Required", "Employee ID is required."
                )
            name = self.name_entry.get().strip()
            if not name:
                return messagebox.showwarning("Input Required", "Name is required.")

            salary = self.get_float(self.salary_entry.get())
            bonus = self.get_float(self.bonus_entry.get())
            deductions = self.get_float(self.deductions_entry.get())
            net_salary = salary + bonus - deductions

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO salary (emp_id, name, salary, bonus, deductions, net_salary) VALUES (?, ?, ?, ?, ?, ?)",
                (emp_id, name, salary, bonus, deductions, net_salary),
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Salary record added.")
            self.fetch_all()
            self.clear_entries()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Employee ID already exists.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_salary(self):
        try:
            emp_id = self.emp_id_entry.get().strip()
            if not emp_id:
                return messagebox.showwarning(
                    "Input Required", "Employee ID is required."
                )
            name = self.name_entry.get().strip()
            if not name:
                return messagebox.showwarning("Input Required", "Name is required.")

            salary = self.get_float(self.salary_entry.get())
            bonus = self.get_float(self.bonus_entry.get())
            deductions = self.get_float(self.deductions_entry.get())
            net_salary = salary + bonus - deductions

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "UPDATE salary SET name=?, salary=?, bonus=?, deductions=?, net_salary=? WHERE emp_id=?",
                (name, salary, bonus, deductions, net_salary, emp_id),
            )
            if c.rowcount == 0:
                messagebox.showwarning("Not Found", "No record found.")
            else:
                messagebox.showinfo("Updated", "Salary record updated.")
            conn.commit()
            conn.close()
            self.fetch_all()
            self.clear_entries()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_highest_paid(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM salary ORDER BY net_salary DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            messagebox.showinfo(
                "Top Earner",
                f"ID: {row[0]}\nName: {row[1]}\nNet Salary: {self.format_currency(row[5])}",
            )
        else:
            messagebox.showinfo("Top Earner", "No data available.")

    def clear_entries(self):
        self.emp_id_entry.delete(0, END)
        self.name_entry.delete(0, END)
        self.salary_entry.delete(0, END)
        self.bonus_entry.delete(0, END)
        self.deductions_entry.delete(0, END)

    def on_row_select(self, event):
        selected = self.tree.focus()
        if selected:
            values = self.tree.item(selected, "values")
            if values:
                self.clear_entries()
                self.emp_id_entry.insert(0, values[0])
                self.name_entry.insert(0, values[1])
                # Remove currency symbol for editing
                self.salary_entry.insert(0, values[2].replace("₹", "").replace(",", ""))
                self.bonus_entry.insert(0, values[3].replace("₹", "").replace(",", ""))
                self.deductions_entry.insert(
                    0, values[4].replace("₹", "").replace(",", "")
                )

    def search(self):
        keyword = self.search_entry.get().strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM salary WHERE emp_id LIKE ? OR name LIKE ?",
            (f"%{keyword}%", f"%{keyword}%"),
        )
        rows = c.fetchall()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            emp_id, name, sal, bon, ded, net = row
            display_row = (
                emp_id,
                name,
                self.format_currency(sal),
                self.format_currency(bon),
                self.format_currency(ded),
                self.format_currency(net),
            )
            self.tree.insert("", END, values=display_row)
        conn.close()

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM salary")
        rows = c.fetchall()
        conn.close()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Emp ID", "Name", "Salary", "Bonus", "Deductions", "Net Salary"]
                )
                writer.writerows(rows)
            messagebox.showinfo("Exported", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def embed_figure_in_scrollable_toplevel(self, fig, title="Chart"):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG)
        win.geometry(f"1000x700")

        outer = tk.Frame(win, bg=BG)
        outer.pack(fill=BOTH, expand=True)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        hbar = tk.Scrollbar(outer, orient=HORIZONTAL, command=canvas.xview)
        vbar = tk.Scrollbar(outer, orient=VERTICAL, command=canvas.yview)
        canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        hbar.pack(side=BOTTOM, fill=X)
        vbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        inner = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        canvas_fig = FigureCanvasTkAgg(fig, master=inner)
        canvas_fig.draw()
        widget = canvas_fig.get_tk_widget()
        widget.pack(fill=BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas_fig, win)
        toolbar.update()
        toolbar.pack(side=TOP, fill=X)

        def _on_config(event=None):
            inner.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", _on_config)
        return canvas_fig

    def draw_pie_chart(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT emp_id, name, net_salary FROM salary")
        rows = c.fetchall()
        conn.close()

        if not rows:
            return messagebox.showwarning("No Data", "No salary data available.")

        items = []
        for emp_id, name, net in rows:
            items.append((emp_id, f"{name}", self.get_float(net), name))

        items.sort(key=lambda x: x[2], reverse=True)
        total = sum(it[2] for it in items)
        if total == 0:
            return messagebox.showwarning("No Data", "Net salaries are zero.")

        top = items[:PIE_TOP_N]
        other = items[PIE_TOP_N:]
        labels = [t[1] for t in top]
        vals = [t[2] for t in top]

        if other:
            other_sum = sum(x[2] for x in other)
            labels.append("Other")
            vals.append(other_sum)

        fig, ax = plt.subplots(figsize=(9, 6))
        pie_result = ax.pie(
            vals,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            textprops={"color": FG},
        )
        wedges = pie_result[0]
        texts = pie_result[1]
        autotexts = pie_result[2] if len(pie_result) > 2 else []
        ax.set_title("Salary Distribution", color=FG)

        canvas = self.embed_figure_in_scrollable_toplevel(fig, "Salary Pie Chart")
        from dashboard_modules.safe_charts import enable_pie_hover
        enable_pie_hover(canvas, fig, ax, wedges, labels, vals, is_currency=True)

    def draw_bar_chart(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, net_salary FROM salary")
        rows = c.fetchall()
        conn.close()
        if not rows:
            return messagebox.showwarning("No Data", "No salary data available.")

        items = [(name, self.get_float(net)) for name, net in rows]
        items.sort(key=lambda x: x[1], reverse=True)
        names = [x[0] for x in items]
        nets = [x[1] for x in items]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(names, nets, color=ACCENT)
        ax.set_xlabel("Net Salary", color=FG)
        ax.set_title("Salary Rankings", color=FG)
        ax.invert_yaxis()

        canvas = self.embed_figure_in_scrollable_toplevel(fig, "Salary Rankings")
        from dashboard_modules.safe_charts import enable_bar_hover
        enable_bar_hover(canvas, fig, ax, list(bars), names, nets, is_horizontal=True, is_currency=True)


if __name__ == "__main__":
    SalaryManager()
