import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="mplcursors")

import os
import math
import sqlite3 
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Wedge
from PIL import Image, ImageOps, ImageTk

# Try to import mplcursors for hover tooltips
try:
    import mplcursors
    HAS_MPLCURSORS = True
except Exception:
    HAS_MPLCURSORS = False

# ---------------------------
# Theme & Constants
# ---------------------------
DB_PATH = "attendance_system.db"
ICONS_DIR = "icons"  # put icons here by emp_id.png or name.png

# App theme colors
BG = "#1E2A47"        # main background (navy)
FG = "#FFFFFF"        # main foreground (text)
ENTRY_BG = "#2B3B5A"  # entry background (slightly lighter)
ENTRY_FG = "#FFFFFF"  # entry text
ACCENT = "#7B3FE4"    # accent / primary
ACCENT_ALT = "#29B6F6"

# Chart configs
PIE_TOP_N = 8
PIE_MIN_LABEL_PCT = 3.0
BAR_SHOW_STACKED = False

# Matplotlib global theme to match app
plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor': BG,
    'axes.edgecolor': FG,
    'axes.labelcolor': FG,
    'xtick.color': FG,
    'ytick.color': FG,
    'text.color': FG,
    'legend.facecolor': BG,
    'legend.edgecolor': FG,
    'figure.autolayout': True,
})

# ---------------------------
# Tkinter setup
# ---------------------------
root = tk.Tk()
root.title("Salary Manager with Interactive Charts")
root.geometry("1400x800")
root.configure(bg=BG)

label_font = ("Arial", 12, "bold")
entry_font = ("Arial", 12)

# Use a ttk style for centered headings where possible
style = ttk.Style()
try:
    style.theme_use('clam')
except Exception:
    pass
style.configure("Treeview.Heading", anchor=CENTER, font=("Arial", 10, "bold"))
style.configure("Treeview", rowheight=24)

# ---------------------------
# Database helpers
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
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


def recalculate_net_salaries():
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
        c.execute("UPDATE salary SET net_salary = ? WHERE emp_id = ?", (net, emp_id))
    conn.commit()
    conn.close()

# ---------------------------
# CRUD Operations
# ---------------------------
def add_salary():
    try:
        emp_id = emp_id_entry.get().strip()
        if not emp_id:
            messagebox.showwarning("Input Required", "Employee ID is required.")
            return
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Name is required.")
            return
        salary = float(salary_entry.get() or 0)
        bonus = float(bonus_entry.get() or 0)
        deductions = float(deductions_entry.get() or 0)
        net_salary = salary + bonus - deductions
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO salary (emp_id, name, salary, bonus, deductions, net_salary) VALUES (?, ?, ?, ?, ?, ?)",
                  (emp_id, name, salary, bonus, deductions, net_salary))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Salary record added.")
        fetch_all()
        clear_entries()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Employee ID already exists.")
    except ValueError:
        messagebox.showerror("Error", "Please enter numeric values for Salary/Bonus/Deductions.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def update_salary():
    try:
        emp_id = emp_id_entry.get().strip()
        if not emp_id:
            messagebox.showwarning("Input Required", "Employee ID is required.")
            return
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Name is required.")
            return
        salary = float(salary_entry.get() or 0)
        bonus = float(bonus_entry.get() or 0)
        deductions = float(deductions_entry.get() or 0)
        net_salary = salary + bonus - deductions
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE salary SET name=?, salary=?, bonus=?, deductions=?, net_salary=? WHERE emp_id=?",
                  (name, salary, bonus, deductions, net_salary, emp_id))
        if c.rowcount == 0:
            messagebox.showwarning("Not Found", "No record found with that Employee ID.")
        else:
            messagebox.showinfo("Updated", "Salary record updated.")
        conn.commit()
        conn.close()
        fetch_all()
        clear_entries()
    except ValueError:
        messagebox.showerror("Error", "Please enter numeric values for Salary/Bonus/Deductions.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def delete_salary():
    emp_id = emp_id_entry.get().strip()
    if not emp_id:
        messagebox.showwarning("Input Required", "Please enter Employee ID.")
        return
    if not messagebox.askyesno("Confirm Delete", f"Delete record for Employee ID '{emp_id}'?"):
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM salary WHERE emp_id=?", (emp_id,))
    if c.rowcount == 0:
        messagebox.showwarning("Not Found", "No record found with that Employee ID.")
    else:
        messagebox.showinfo("Deleted", "Salary record deleted.")
    conn.commit()
    conn.close()
    fetch_all()
    clear_entries()


def fetch_all():
    conn = sqlite3.connect(DB_PATH)
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
        if values:
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM salary")
    rows = c.fetchall()
    conn.close()
    try:
        with open(file_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Emp ID", "Name", "Salary", "Bonus", "Deductions", "Net Salary"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Data exported to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export: {e}")


def show_highest_paid():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM salary ORDER BY net_salary DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        messagebox.showinfo("Top Earner", f"ID: {row[0]}\nName: {row[1]}\nNet Salary: {row[5]}")
    else:
        messagebox.showinfo("Top Earner", "No data available.")

# ---------------------------
# Helper: robust index extraction from mplcursors selection
# ---------------------------
def safe_index_from_sel(sel):
    idx = None
    try:
        if hasattr(sel, "index"):
            idx_attr = sel.index
            try:
                if callable(idx_attr):
                    idx = idx_attr()
                else:
                    idx = idx_attr
            except Exception:
                idx = None
        if idx is None and hasattr(sel, "ind"):
            ind = sel.ind
            if ind:
                try:
                    idx = int(ind[0])
                except Exception:
                    idx = None
        if idx is None and hasattr(sel, "target"):
            tgt = sel.target
            try:
                if hasattr(tgt, "index"):
                    t = tgt.index
                    idx = t() if callable(t) else int(t)
                else:
                    idx = int(tgt)
            except Exception:
                idx = None
        if idx is None:
            artist = getattr(sel, "artist", None)
            mouseevent = getattr(sel, "mouseevent", None)
            if artist is not None and mouseevent is not None:
                patches = getattr(artist, "patches", None) or getattr(artist, "artists", None) or getattr(artist, "get_children", lambda: [])()
                if patches:
                    for j, p in enumerate(patches):
                        try:
                            contains, _ = p.contains(mouseevent)
                        except Exception:
                            contains = False
                        if contains:
                            idx = j
                            break
    except Exception:
        idx = None
    try:
        if idx is None:
            return 0
        return int(idx)
    except Exception:
        return 0

# ---------------------------
# Chart utilities
# ---------------------------
def load_icon_for(name_or_id, max_size=(48,48)):
    if not os.path.isdir(ICONS_DIR):
        return None
    candidates = [
        os.path.join(ICONS_DIR, f"{name_or_id}.png"),
        os.path.join(ICONS_DIR, f"{name_or_id}.jpg"),
        os.path.join(ICONS_DIR, f"{name_or_id}.jpeg"),
        os.path.join(ICONS_DIR, f"{name_or_id}.ico"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA")
                img.thumbnail(max_size, Image.LANCZOS)
                return img
            except Exception:
                return None
    return None


def embed_figure_in_scrollable_toplevel(fig, title="Chart", width=1000, height=700):
    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg=BG)
    win.geometry(f"{width}x{height}")

    outer = tk.Frame(win, bg=BG)
    outer.pack(fill=BOTH, expand=True, anchor='center')

    canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
    hbar = tk.Scrollbar(outer, orient=HORIZONTAL, command=canvas.xview)
    vbar = tk.Scrollbar(outer, orient=VERTICAL, command=canvas.yview)
    canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    hbar.pack(side=BOTTOM, fill=X)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    inner = tk.Frame(canvas, bg=BG)
    canvas.create_window((0, 0), window=inner, anchor='nw')

    canvas_fig = FigureCanvasTkAgg(fig, master=inner)
    canvas_fig.draw()
    widget = canvas_fig.get_tk_widget()
    widget.pack(fill=BOTH, expand=True)

    toolbar_frame = tk.Frame(win, bg=BG)
    toolbar_frame.pack(fill=X)
    toolbar = NavigationToolbar2Tk(canvas_fig, toolbar_frame)
    toolbar.update()

    def _on_config(event=None):
        inner.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    inner.bind("<Configure>", _on_config)
    _on_config()

    def _on_mousewheel(event):
        if event.state & 0x0001:
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        else:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    widget.bind_all("<MouseWheel>", _on_mousewheel)
    widget.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    widget.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    return win, canvas_fig

# ---------------------------
# Charts (pie with icons, zoomable, scrollable, interactive tooltips)
# ---------------------------

def draw_pie_chart():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT emp_id, name, net_salary FROM salary")
    rows = c.fetchall()
    conn.close()

    if not rows:
        messagebox.showwarning("No Data", "No salary data available.")
        return

    items = []
    for emp_id, name, net in rows:
        try:
            val = float(net or 0)
        except:
            val = 0.0
        display_name = f"{name} ({emp_id})"
        items.append((emp_id, display_name, val, name))

    items.sort(key=lambda x: x[2], reverse=True)
    total = sum(it[2] for it in items)
    if total == 0:
        messagebox.showwarning("No Data", "Net salaries are zero.")
        return

    top = items[:PIE_TOP_N]
    other = items[PIE_TOP_N:]
    labels = [t[1] for t in top]
    vals = [t[2] for t in top]
    underlying = [t for t in top]
    if other:
        other_sum = sum(x[2] for x in other)
        labels.append("Other")
        vals.append(other_sum)
        underlying.append((None, "Other", other_sum, None))

    fig_w = 9
    fig_h = max(6, 0.35 * max(6, len(labels)))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # color palette: generate from accent colors for consistency
    cmap = plt.get_cmap('tab20')
    colors = [cmap(i % 20) for i in range(len(vals))]

    wedges, texts = ax.pie(vals, startangle=140, colors=colors, wedgeprops=dict(width=0.45, edgecolor=BG))
    ax.set(aspect="equal")
    ax.set_title("Net Salary Distribution (Top contributors + Other)", fontsize=14, color=FG)

    legend_labels = []
    for val, entry in zip(vals, underlying):
        pct = val / total * 100 if total else 0
        emp_id = entry[0] if len(entry) >= 4 else None
        display_name = entry[1] if len(entry) >= 2 else str(entry)
        legend_labels.append(f"{display_name} — {int(round(val))} ({pct:.1f}%)")

    leg = ax.legend(wedges, legend_labels, title="Employees", loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=10, title_fontsize=11)
    for txt in leg.get_texts():
        txt.set_color(FG)
    try:
        leg.get_title().set_color(FG)
    except Exception:
        pass

    try:
        renderer = fig.canvas.get_renderer()
        for i, text in enumerate(leg.get_texts()):
            if i >= len(underlying):
                break
            emp_id, display_name, _, name = underlying[i]
            icon_img = None
            if emp_id:
                icon_img = load_icon_for(emp_id)
            if not icon_img and name:
                icon_img = load_icon_for(name)
            if not icon_img:
                continue
            ab = AnnotationBbox(OffsetImage(icon_img, zoom=0.7), (1.02 + 0.05, 0.5 - (i - len(underlying)/2) * 0.06),
                                xycoords='axes fraction', frameon=False)
            ax.add_artist(ab)
    except Exception:
        pass

    for w, v in zip(wedges, vals):
        pct = 0 if sum(vals) == 0 else (v / sum(vals)) * 100
        if pct >= PIE_MIN_LABEL_PCT:
            ang = (w.theta2 + w.theta1) / 2.0
            x = math.cos(math.radians(ang))
            y = math.sin(math.radians(ang))
            ax.annotate(f"{pct:.1f}%", xy=(0.8 * x, 0.8 * y), ha='center', va='center', fontsize=10, color=FG)

    if HAS_MPLCURSORS:
        cursor = mplcursors.cursor(wedges, hover=True)
        @cursor.connect("add")
        def _(sel):
            i = safe_index_from_sel(sel)
            label = legend_labels[i] if i < len(legend_labels) else f"{i}"
            sel.annotation.set_text(label)
            sel.annotation.get_bbox_patch().set_alpha(0.9)
            sel.annotation.get_bbox_patch().set_facecolor(ENTRY_BG)
            sel.annotation.get_bbox_patch().set_edgecolor(FG)
    else:
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc=ENTRY_BG),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        def motion(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for wedge, lab in zip(wedges, legend_labels):
                    contains, _ = wedge.contains(event)
                    if contains:
                        annot.xy = (event.xdata, event.ydata)
                        annot.set_text(lab)
                        annot.get_bbox_patch().set_facecolor(ENTRY_BG)
                        annot.get_bbox_patch().set_edgecolor(FG)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
        fig.canvas.mpl_connect("motion_notify_event", motion)

    win, canvas_fig = embed_figure_in_scrollable_toplevel(fig, title="Donut/Pie - Interactive", width=1100, height=750)
    plt.close(fig)


def draw_bar_chart(sorted_by_net=True):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT emp_id, name, salary, bonus, deductions, net_salary FROM salary")
    rows = c.fetchall()
    conn.close()
    if not rows:
        messagebox.showwarning("No Data", "No salary data available.")
        return

    items = []
    for emp_id, name, salary, bonus, deductions, net in rows:
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
        try:
            netv = float(net or s + b - d)
        except:
            netv = s + b - d
        display_name = f"{name} ({emp_id})"
        items.append((emp_id, display_name, s, b, d, netv, name))

    items.sort(key=lambda x: x[5], reverse=True)
    names = [it[1] for it in items]
    net_vals = [it[5] for it in items]

    fig_w = 10
    fig_h = max(4, 0.35 * max(6, len(names)))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    y_pos = list(range(len(names)))

    cmap = plt.get_cmap('tab20')
    colors = [cmap(i % 20) for i in range(len(names))]
    bars = ax.barh(y_pos, net_vals, align='center', color=colors, edgecolor=BG)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9, color=FG)
    ax.invert_yaxis()
    ax.set_xlabel("Net Salary", color=FG)
    ax.set_title("Net Salary by Employee (sorted)", color=FG)

    max_net = max(net_vals) if net_vals else 1
    for i, v in enumerate(net_vals):
        vstr = f"{int(round(v))}" if abs(v - round(v)) < 1e-8 else f"{v:.2f}"
        ax.text(v + max(1, max_net * 0.01), i, vstr, va='center', fontsize=8, color=FG)

    if HAS_MPLCURSORS:
        cursor = mplcursors.cursor(bars, hover=True)
        @cursor.connect("add")
        def _(sel):
            i = safe_index_from_sel(sel)
            if i < 0 or i >= len(items):
                i = 0
            it = items[i]
            emp_id, display_name, s, b, d, netv, name = it
            sel.annotation.set_text(f"{display_name}\nSalary: {s}\nBonus: {b}\nDeductions: {d}\nNet: {netv}")
            sel.annotation.get_bbox_patch().set_alpha(0.9)
            sel.annotation.get_bbox_patch().set_facecolor(ENTRY_BG)
            sel.annotation.get_bbox_patch().set_edgecolor(FG)
    else:
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc=ENTRY_BG),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        def motion(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for rect, it in zip(bars, items):
                    contains, _ = rect.contains(event)
                    if contains:
                        emp_id, display_name, s, b, d, netv, name = it
                        annot.xy = (event.xdata, event.ydata)
                        annot.set_text(f"{display_name}\nSalary: {s}\nBonus: {b}\nDeductions: {d}\nNet: {netv}")
                        annot.get_bbox_patch().set_facecolor(ENTRY_BG)
                        annot.get_bbox_patch().set_edgecolor(FG)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
        fig.canvas.mpl_connect("motion_notify_event", motion)

    ax.grid(axis='x', linestyle='--', alpha=0.4)

    win, canvas_fig = embed_figure_in_scrollable_toplevel(fig, title="Net Salary - Bar Chart", width=1100, height=700)
    plt.close(fig)

# ---------------------------
# UI Layout (center-aligned with better spacing)
# ---------------------------
center_container = Frame(root, bg=BG)
center_container.pack(fill=BOTH, expand=True)

# Title
title_frame = Frame(center_container, bg=BG)
title_frame.pack(pady=(15, 10))
Label(title_frame, text="💰 Salary Management System", font=("Arial", 20, "bold"), bg=BG, fg=FG).pack()

# Chart buttons at the top
chart_container = Frame(center_container, bg=BG)
chart_container.pack(pady=10, padx=20)

chart_btn_frame = Frame(chart_container, bg=BG)
chart_btn_frame.pack()

Button(chart_btn_frame, text="🥧 Pie Chart (with icons)", command=draw_pie_chart, font=("Arial", 11, "bold"), bg="#FF7043", fg="white", width=22, relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=10)
Button(chart_btn_frame, text="📊 Bar Chart (interactive)", command=lambda: draw_bar_chart(sorted_by_net=True), font=("Arial", 11, "bold"), bg="#29B6F6", fg="white", width=22, relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=10)

# Form frame with better structure
form_frame = Frame(center_container, bg=BG)
form_frame.pack(pady=15, padx=20)

# Configure grid for proper alignment
form_frame.grid_columnconfigure(1, weight=1, minsize=200)
form_frame.grid_columnconfigure(3, weight=1, minsize=200)
form_frame.grid_columnconfigure(5, weight=1, minsize=200)

# Row 0 - Employee ID and Name
Label(form_frame, text="Employee ID:", font=label_font, bg=BG, fg=FG, anchor='e', width=14).grid(row=0, column=0, padx=(0, 10), pady=10, sticky=E)
emp_id_entry = Entry(form_frame, font=entry_font, width=20, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
emp_id_entry.grid(row=0, column=1, padx=(0, 20), pady=10, sticky=EW)

Label(form_frame, text="Name:", font=label_font, bg=BG, fg=FG, anchor='e', width=14).grid(row=0, column=2, padx=(0, 10), pady=10, sticky=E)
name_entry = Entry(form_frame, font=entry_font, width=30, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
name_entry.grid(row=0, column=3, padx=(0, 20), pady=10, sticky=EW, columnspan=3)

# Row 1 - Salary, Bonus, Deductions
Label(form_frame, text="Salary:", font=label_font, bg=BG, fg=FG, anchor='e', width=14).grid(row=1, column=0, padx=(0, 10), pady=10, sticky=E)
salary_entry = Entry(form_frame, font=entry_font, width=20, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
salary_entry.grid(row=1, column=1, padx=(0, 20), pady=10, sticky=EW)

Label(form_frame, text="Bonus:", font=label_font, bg=BG, fg=FG, anchor='e', width=14).grid(row=1, column=2, padx=(0, 10), pady=10, sticky=E)
bonus_entry = Entry(form_frame, font=entry_font, width=20, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
bonus_entry.grid(row=1, column=3, padx=(0, 20), pady=10, sticky=EW)

Label(form_frame, text="Deductions:", font=label_font, bg=BG, fg=FG, anchor='e', width=14).grid(row=1, column=4, padx=(0, 10), pady=10, sticky=E)
deductions_entry = Entry(form_frame, font=entry_font, width=20, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
deductions_entry.grid(row=1, column=5, padx=(0, 0), pady=10, sticky=EW)

# Action buttons - organized in rows
btn_container = Frame(center_container, bg=BG)
btn_container.pack(pady=15, padx=20)

# Primary actions row
btn_frame_primary = Frame(btn_container, bg=BG)
btn_frame_primary.pack(pady=5)

Button(btn_frame_primary, text="➕ Add", command=add_salary, width=14, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)
Button(btn_frame_primary, text="✏️ Update", command=update_salary, width=14, font=("Arial", 11, "bold"), bg="#FFC107", fg="black", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)
Button(btn_frame_primary, text="🗑️ Delete", command=delete_salary, width=14, font=("Arial", 11, "bold"), bg="#F44336", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)
Button(btn_frame_primary, text="🧹 Clear", command=clear_entries, width=14, font=("Arial", 11, "bold"), bg="#9E9E9E", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)

# Secondary actions row
btn_frame_secondary = Frame(btn_container, bg=BG)
btn_frame_secondary.pack(pady=5)

Button(btn_frame_secondary, text="📊 Export CSV", command=export_csv, width=14, font=("Arial", 11, "bold"), bg="#7B1FA2", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)
Button(btn_frame_secondary, text="🏆 Top Earner", command=show_highest_paid, width=14, font=("Arial", 11, "bold"), bg="#455A64", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)
Button(btn_frame_secondary, text="🚪 Exit", command=root.quit, width=14, font=("Arial", 11, "bold"), bg="#607D8B", fg="white", relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8, pady=5)

# Search section with better alignment
search_container = Frame(center_container, bg=BG)
search_container.pack(fill=X, padx=20, pady=15)

search_frame = Frame(search_container, bg=BG)
search_frame.pack()

Label(search_frame, text="🔍 Search:", font=("Arial", 12, "bold"), bg=BG, fg=FG).pack(side=LEFT, padx=(0, 10))
search_entry = Entry(search_frame, font=entry_font, width=35, justify='left', bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG)
search_entry.pack(side=LEFT, padx=5)
Button(search_frame, text="Search", command=search, font=("Arial", 11, "bold"), bg="#0288D1", fg="white", width=12, relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8)
Button(search_frame, text="Show All", command=fetch_all, font=("Arial", 11, "bold"), bg="#009688", fg="white", width=12, relief='flat', bd=0, cursor="hand2").pack(side=LEFT, padx=8)

# Treeview area with title
tree_container = Frame(center_container, bg=BG)
tree_container.pack(pady=10, padx=20, fill=BOTH, expand=True)

tree_title = Frame(tree_container, bg=BG)
tree_title.pack(fill=X, pady=(0, 10))
Label(tree_title, text="📋 Employee Salary Records", font=("Arial", 14, "bold"), bg=BG, fg=FG).pack(anchor='w')

tree_frame = Frame(tree_container, bg=BG)
tree_frame.pack(fill=BOTH, expand=True)

columns = ("emp_id", "name", "salary", "bonus", "deductions", "net_salary")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)

# Configure column headings and widths with better alignment
column_config = {
    "emp_id": ("Employee ID", 120),
    "name": ("Name", 280),
    "salary": ("Base Salary", 130),
    "bonus": ("Bonus", 120),
    "deductions": ("Deductions", 130),
    "net_salary": ("Net Salary", 130)
}

for col, (heading, width) in column_config.items():
    tree.heading(col, text=heading)
    tree.column(col, width=width, anchor=CENTER)

tree.pack(side=LEFT, fill=BOTH, expand=True)
tree.bind("<ButtonRelease-1>", on_row_select)

scrollbar = Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
scrollbar.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=scrollbar.set)

# ---------------------------
# Startup
# ---------------------------
init_db()
recalculate_net_salaries()
fetch_all()

if not HAS_MPLCURSORS:
    print("Tip: install 'mplcursors' for nicer hover tooltips (pip install mplcursors).")

root.mainloop()
