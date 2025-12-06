import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading

# ML imports removed as they are not used in this module


# Theme and constants
DARK_MODE = {"bg": "#1A1A2E", "fg": "white", "button": "#E94560", "hover": "#FF6F61", "card": "#2E2E2E"}
LIGHT_MODE = {"bg": "#F0F0F0", "fg": "#1A1A2E", "button": "#007BFF", "hover": "#0056b3", "card": "#FFFFFF"}
theme = DARK_MODE.copy()
BUTTON_FONT = ("Arial", 12)
MODEL_DIR = "models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Global reference for the content frame (used for navigation)
content = None

# Global flag to prevent ML training loops
ml_training_in_progress = False
ml_trained_this_session = False


# Extracted from employee_dashboard.py

# ------------------
class ToolTip:
    """Simple tooltip for widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwin = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tipwin or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width()
            y = self.widget.winfo_rooty() + self.widget.winfo_height()
        except Exception:
            x, y = 100, 100
        x = max(0, x)
        y = max(0, y)
        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#ffffe0",
                         relief='solid', borderwidth=1, font=("tahoma", 8))
        label.pack(ipadx=4)

    def hide(self, _=None):
        if self.tipwin:
            self.tipwin.destroy()
            self.tipwin = None

class CustomButton:
    def __init__(self, parent, text, command):
        self.button = tk.Button(parent, text=text, font=BUTTON_FONT,
                                 bg=theme["button"], fg=theme["fg"],
                                 activebackground=theme["hover"], relief="flat", bd=0,
                                 command=command)
        self.button.bind("<Enter>", lambda e: self.button.config(bg=theme["hover"]))
        self.button.bind("<Leave>", lambda e: self.button.config(bg=theme["button"]))
        self.button.pack(fill='x', pady=5, padx=10)

def rounded_card(parent, width=320, height=140, radius=12, bg=None):
    bg = bg or theme['card']
    c = tk.Canvas(parent, width=width, height=height, bg=theme['bg'], highlightthickness=0)
    x1, y1, x2, y2 = 6, 6, width-6, height-6
    r = radius
    c.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=bg, outline=bg)
    c.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=bg, outline=bg)
    c.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=bg, outline=bg)
    c.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=bg, outline=bg)
    c.create_rectangle(x1+r, y1, x2-r, y2, fill=bg, outline=bg)
    c.create_rectangle(x1, y1+r, x2, y2-r, fill=bg, outline=bg)
    return c

# ------------------
# Utility functions
# ------------------
def create_scrollable_frame(parent):
    """Create a scrollable frame with mousewheel support"""
    canvas = tk.Canvas(parent, bg=theme['bg'], highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=theme['bg'])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    
    # Enable mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    return scrollable_frame, canvas

def clear_content(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def fade_in(win, alpha=0.0):
    alpha += 0.05
    if alpha <= 1.0:
        win.attributes("-alpha", alpha)
        win.after(20, lambda: fade_in(win, alpha))

def update_theme(window):
    bg_color = theme.get("bg", "white")
    fg_color = theme.get("fg", "black")
    card_color = theme.get("card", "lightgray")
    button_color = theme.get("button", "blue")
    try:
        window.config(bg=bg_color)
    except:
        pass
    for widget in window.winfo_children():
        widget_class = widget.winfo_class()
        try:
            if widget_class in ('Frame', 'Toplevel'):
                widget.config(bg=bg_color)
            elif widget_class in ('Label', 'Checkbutton', 'Text'):
                widget.config(bg=bg_color, fg=fg_color)
            elif widget_class == 'Button':
                widget.config(bg=button_color, fg=fg_color)
                widget.bind("<Enter>", lambda e, b=widget: b.config(bg=theme["hover"]))
                widget.bind("<Leave>", lambda e, b=widget: b.config(bg=theme["button"]))
            elif widget_class == 'Canvas':
                pass
            elif widget_class == 'Listbox':
                widget.config(bg=card_color, fg=fg_color)
            update_theme(widget)
        except:
            pass

def append_status(txt_widget, msg):
    txt_widget.config(state='normal')
    txt_widget.insert('end', f"\n{datetime.now().strftime('%H:%M:%S')} - {msg}")
    txt_widget.see('end')
    txt_widget.config(state='disabled')

# ------------------
# THREAD-SAFE DB ACCESS HELPER
# ------------------
def get_db_data_safely(query, params=(), fetch_all=True):
    try:
        conn = sqlite3.connect("attendance_system.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall() if fetch_all else cursor.fetchone()
        conn.close()
        return data, None
    except sqlite3.OperationalError as e:
        return None, f"Database Error: {e}"
    except Exception as e:
        return None, f"General Error: {e}"

# ------------------
# ML helpers (data loading, train/save/load)
