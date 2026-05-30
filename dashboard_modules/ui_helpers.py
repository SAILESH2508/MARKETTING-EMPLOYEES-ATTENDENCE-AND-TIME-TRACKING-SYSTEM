import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
try:
    from sklearn.exceptions import InconsistentVersionWarning

    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except ImportError:
    pass

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading


# ------------------
# Theme & Constants
# ------------------

# "Classic Dark" aesthetic (Matches emp.py / admin_dashboard.py)
# Matches user request: "Global Dark Theme" but "not black"
DARK_MODE = {
    "bg": "#0A0F1D",  # Premium deep dark navy
    "fg": "#F8FAFC",  # Crisp off-white
    "card": "#131B2E",  # Rich navy card
    "card_border": "#1E2943",  # Deep card border
    "button": "#6366F1",  # Sleek Indigo button
    "button_fg": "#FFFFFF",
    "hover": "#4F46E5",  # Darker Indigo hover
    "success": "#10B981",  # Emerald success
    "warning": "#F59E0B",  # Amber warning
    "error": "#EF4444",  # Red error
    "text_secondary": "#94A3B8",  # Slate-400 secondary text
}

LIGHT_MODE = {
    "bg": "#F8FAFC",
    "fg": "#0F172A",
    "card": "#FFFFFF",
    "card_border": "#E2E8F0",
    "button": "#3B82F6",
    "button_fg": "#FFFFFF",
    "hover": "#2563EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "text_secondary": "#64748B",
}

# Current Theme - Set to DARK_MODE by default
theme = DARK_MODE.copy()

# Fonts
HEADER_FONT = ("Segoe UI", 24, "bold")
SUBHEADER_FONT = ("Segoe UI", 16, "bold")
TITLE_FONT = ("Segoe UI", 12, "bold")
BODY_FONT = ("Segoe UI", 10)
SMALL_FONT = ("Segoe UI", 9)
BUTTON_FONT = ("Segoe UI", 10, "bold")

MODEL_DIR = "models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Global reference for the content frame (used for navigation)
content = None

# Global flag to prevent ML training loops
ml_training_in_progress = False
ml_trained_this_session = False


# ------------------
# UI Components
# ------------------


class RoundedFrame(tk.Canvas):
    """
    A responsive container with rounded corners and custom background color.
    It acts like a Frame but draws a rounded rectangle background.
    """

    def __init__(
        self,
        parent,
        width=300,
        height=150,
        corner_radius=15,
        bg_color=None,
        border_color=None,
        **kwargs,
    ):
        super().__init__(
            parent, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.corner_radius = corner_radius
        self.bg_color = bg_color if bg_color else theme["card"]
        self.border_color = (
            border_color if border_color else theme.get("card_border", self.bg_color)
        )

        # This frame will hold the actual widgets
        self.inner_frame = tk.Frame(self, bg=self.bg_color)
        self.window_item = self.create_window(
            (corner_radius, corner_radius), window=self.inner_frame, anchor="nw"
        )

        # Initial background draw
        self.bind("<Configure>", self._on_resize)
        self._draw_background(width, height)

        # Propagate background color changes
        self.configure(bg=theme["bg"])  # Canvas background matches parent bg

    def _draw_background(self, width, height):
        self.delete("bg_rect")

        # Points for a rounded rectangle
        r = self.corner_radius
        x0, y0 = 2, 2
        x1, y1 = width - 2, height - 2

        # Draw the rounded shape
        self.create_polygon(
            x0 + r,
            y0,
            x1 - r,
            y0,
            x1,
            y0,
            x1,
            y0 + r,
            x1,
            y1 - r,
            x1,
            y1,
            x1 - r,
            y1,
            x0 + r,
            y1,
            x0,
            y1,
            x0,
            y1 - r,
            x0,
            y0 + r,
            x0,
            y0,
            smooth=True,
            fill=self.bg_color,
            outline=self.border_color,
            width=1,
            tags="bg_rect",
        )
        # Move background to bottom
        self.tag_lower("bg_rect")

    def _on_resize(self, event):
        w, h = event.width, event.height
        self._draw_background(w, h)
        # Resize inner frame to fit inside the rounded borders (approx)
        inner_w = max(1, w - 2 * self.corner_radius)
        inner_h = max(1, h - 2 * self.corner_radius)
        self.itemconfigure(self.window_item, width=inner_w, height=inner_h)


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
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except Exception:
            x, y = 100, 100

        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#333333",
            foreground="#FFFFFF",
            relief="solid",
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        label.pack(ipadx=8, ipady=4)

    def hide(self, _=None):
        if self.tipwin:
            self.tipwin.destroy()
            self.tipwin = None


class CustomButton(tk.Button):
    def __init__(self, parent, text, command, bg=None, fg=None, width=None, hover_color=None, **kwargs):
        bg = bg or theme["button"]
        fg = fg or theme.get("button_fg", "white")
        hover = hover_color or theme["hover"]

        btn_kwargs = {}
        if width is not None:
            btn_kwargs["width"] = width

        # Extract invalid options for tk.Button if necessary, but **kwargs usually handles standard ones like height
        super().__init__(
            parent,
            text=text,
            font=BUTTON_FONT,
            bg=bg,
            fg=fg,
            activebackground=hover,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command,
            **btn_kwargs,
            **kwargs,
        )

        self.bind("<Enter>", lambda e: self.config(bg=hover))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


# ------------------
# Utility Functions
# ------------------


# Legacy support for older calls - simply creates a canvas, but doesn't handle resize as well as RoundedFrame
def rounded_card(parent, width=320, height=140, radius=12, bg=None):
    # This acts as a bridge for legacy code, but we prefer using RoundedFrame directly
    # For now, we return a Canvas to keep API compatible if needed,
    # but we will try to migrate everything to RoundedFrame
    bg = bg or theme["card"]
    c = tk.Canvas(
        parent, width=width, height=height, bg=theme["bg"], highlightthickness=0
    )
    x1, y1, x2, y2 = 6, 6, width - 6, height - 6
    r = radius
    c.create_arc(
        x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=bg, outline=bg
    )
    c.create_arc(
        x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=bg, outline=bg
    )
    c.create_arc(
        x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=bg, outline=bg
    )
    c.create_arc(
        x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=bg, outline=bg
    )
    c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=bg, outline=bg)
    c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=bg, outline=bg)
    return c


def create_scrollable_frame(parent):
    """Create a scrollable frame with mousewheel support and modern styling."""
    container = tk.Frame(parent, bg=theme["bg"])

    # Grid configuration for container to ensure it expands
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(container, bg=theme["bg"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    scrollable_frame = tk.Frame(canvas, bg=theme["bg"])

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Store ID to update width
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Force the scrollable frame to expand to canvas width
    def on_canvas_configure(event):
        canvas.itemconfig(window_id, width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Enable mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    return scrollable_frame, canvas


def clear_content(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def fade_in(win, alpha=0.0):
    alpha += 0.08
    if alpha <= 1.0:
        win.attributes("-alpha", alpha)
        win.after(15, lambda: fade_in(win, alpha))


def update_theme(window):
    """Recursively update the theme of the window and its widgets."""
    bg_color = theme["bg"]
    fg_color = theme["fg"]
    card_color = theme["card"]

    try:
        window.config(bg=bg_color)
    except:
        pass

    for widget in window.winfo_children():
        widget_class = widget.winfo_class()
        try:
            if isinstance(widget, RoundedFrame):
                widget.bg_color = card_color
                widget.border_color = theme.get("card_border", card_color)
                widget.configure(bg=bg_color)
                widget.inner_frame.config(bg=card_color)
                widget._draw_background(widget.winfo_width(), widget.winfo_height())
                # Recurse into inner_frame
                update_theme(widget.inner_frame)
                continue

            if widget_class in ("Frame", "Toplevel"):
                widget.config(bg=bg_color)
            elif widget_class in ("Label", "Checkbutton", "Text"):
                widget.config(bg=bg_color, fg=fg_color)
            elif widget_class == "Button" and not isinstance(widget, CustomButton):
                widget.config(bg=theme["button"], fg=theme.get("button_fg", "white"))
            elif widget_class == "Canvas":
                if not isinstance(widget, RoundedFrame):
                    widget.config(bg=bg_color)
            elif widget_class == "Listbox":
                widget.config(bg=card_color, fg=fg_color)
            elif isinstance(widget, ttk.Notebook):
                style = ttk.Style()
                style.configure("TNotebook", background=bg_color)
                style.configure(
                    "TNotebook.Tab", background=theme["card"], foreground=fg_color
                )

            update_theme(widget)
        except Exception:
            pass


def append_status(txt_widget, msg):
    try:
        txt_widget.config(state="normal")
        txt_widget.insert("end", f"\n{datetime.now().strftime('%H:%M:%S')} - {msg}")
        txt_widget.see("end")
        txt_widget.config(state="disabled")
    except:
        pass


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
# Treeview Styling Helper
# ------------------
def apply_treeview_style(style):
    """
    Applies a consistent Dark Theme to a Treeview style object.
    Parameters:
        style (ttk.Style): The style object to configure.
    """
    try:
        style.theme_use("clam")
    except:
        pass

    # Header Style: Dark Grey Background, White Text
    # Header Style: Card Border/Indigo Accent Background, Theme Text
    style.configure(
        "Dark.Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background=theme.get("card_border", "#24324D"),
        foreground=theme["fg"],
        relief="flat",
    )
    style.map("Dark.Treeview.Heading", background=[("active", theme.get("hover", "#4F46E5"))])

    # Row Style: Card Background, Theme Text
    row_bg = theme.get("card", "#151F32")
    row_fg = theme.get("fg", "#F8FAFC")

    style.configure(
        "Dark.Treeview",
        rowheight=32,
        font=("Segoe UI", 10),
        background=row_bg,
        fieldbackground=row_bg,
        foreground=row_fg,
        borderwidth=0,
    )

    # Selection Style: Theme Button Color
    style.map(
        "Dark.Treeview",
        background=[("selected", theme.get("button", "#6366F1"))],
        foreground=[("selected", theme.get("button_fg", "#FFFFFF"))],
    )
