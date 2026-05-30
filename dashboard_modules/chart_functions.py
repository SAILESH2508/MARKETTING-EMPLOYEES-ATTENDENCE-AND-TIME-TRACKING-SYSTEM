import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from dashboard_modules.matplotlib_config import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading

# Theme and constants
try:
    from dashboard_modules.ui_helpers import theme
except ImportError:
    theme = {
        "bg": "#0A192F",
        "fg": "white",
        "button": "#E94560",
        "hover": "#FF6F61",
        "card": "#172A45",
    }


def show_salary_pie(frame, emp_id, cursor):
    """Show salary breakdown with fixed overlapping text - FIXED VERSION"""
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    try:
        # Get salary data
        cursor.execute(
            "SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,)
        )
        result = cursor.fetchone()

        if not result:
            tk.Label(
                frame,
                text="No salary data found for this employee",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 14),
            ).pack(pady=50)
            return

        salary, bonus, deductions = result
        salary = salary if salary is not None else 0.0
        bonus = bonus if bonus is not None else 0.0
        deductions = deductions if deductions is not None else 0.0

        # Main container
        main_container = tk.Frame(frame, bg=theme["bg"])
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_frame = tk.Frame(main_container, bg=theme["bg"])
        title_frame.pack(fill="x", pady=(0, 20))
        tk.Label(
            title_frame,
            text="💰 Salary Breakdown Analysis",
            font=("Arial", 16, "bold"),
            bg=theme["bg"],
            fg=theme["fg"],
        ).pack(anchor="w")

        # Content container - side by side layout
        content_container = tk.Frame(main_container, bg=theme["bg"])
        content_container.pack(fill="both", expand=True)

        # Left side - Pie chart (if there's data to show)
        left_frame = tk.Frame(content_container, bg=theme["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Prepare data for pie chart
        labels = []
        values = []
        colors = []

        if salary > 0:
            labels.append("Base Salary")
            values.append(salary)
            colors.append(theme["button"])

        if bonus > 0:
            labels.append("Bonus")
            values.append(bonus)
            colors.append("#4CAF50")

        if deductions > 0:
            labels.append("Deductions")
            values.append(deductions)
            colors.append("#F44336")

        if not values or sum(values) == 0:
            tk.Label(
                left_frame,
                text="No salary components to display",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
        else:
            # Create pie chart with better text positioning to prevent overlapping
            fig, ax = plt.subplots(
                figsize=(10, 10), facecolor=theme["bg"]
            )  # Increased size
            fig.subplots_adjust(
                left=0.1, right=0.9, top=0.85, bottom=0.15
            )  # More space

            # Create pie chart with optimized text positioning
            pie_result = ax.pie(
                values,
                labels=None,  # Remove labels from pie chart to avoid overlap
                autopct=lambda pct: (
                    f"{pct:.1f}%" if pct > 3 else ""
                ),  # Only show % if slice is significant
                startangle=90,
                colors=colors,
                textprops={"fontsize": 10, "weight": "bold"},
                pctdistance=0.75,  # Move percentage text closer to center
                explode=[0.08] * len(values),  # More separation between slices
                shadow=True,  # Add shadow for better visibility
                radius=0.8,  # Smaller radius to leave more space for labels
            )
            wedges = pie_result[0]
            texts = pie_result[1]
            autotexts = pie_result[2] if len(pie_result) > 2 else []

            # Style the percentage text
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(11)
                autotext.set_fontweight("bold")
                autotext.set_bbox(
                    dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.7)
                )

            # Create custom legend instead of pie chart labels to avoid overlapping
            legend_elements = []
            for i, (label, value, color) in enumerate(zip(labels, values, colors)):
                legend_elements.append(
                    Rectangle(
                        (0, 0), 1, 1, facecolor=color, label=f"{label}: ₹{value:,.0f}"
                    )
                )

            ax.legend(
                handles=legend_elements,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
                fontsize=12,
                frameon=True,
                fancybox=True,
                shadow=True,
            )

            ax.set_title(
                "Salary Components Breakdown",
                color=theme["fg"],
                fontsize=16,
                pad=30,
                weight="bold",
            )

            # Ensure pie chart is circular
            ax.axis("equal")

            canvas = FigureCanvasTkAgg(fig, master=left_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            plt.close(fig)

        # Right side - Detailed breakdown
        right_frame = tk.Frame(
            content_container, bg=theme["card"], relief="raised", bd=2
        )
        right_frame.pack(side="right", fill="both", expand=True)

        # Details content with padding
        details_container = tk.Frame(right_frame, bg=theme["card"])
        details_container.pack(fill="both", expand=True, padx=25, pady=25)

        # Details title
        tk.Label(
            details_container,
            text="📊 Financial Breakdown",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 20))

        # Base Salary
        salary_row = tk.Frame(details_container, bg=theme["card"])
        salary_row.pack(fill="x", pady=8)
        tk.Label(
            salary_row,
            text="💼 Base Salary:",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
            width=14,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            salary_row,
            text=f"₹{salary:,.2f}",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["button"],
        ).pack(side="right")

        # Separator line
        tk.Frame(details_container, bg=theme["fg"], height=1).pack(fill="x", pady=8)

        # Bonus
        bonus_row = tk.Frame(details_container, bg=theme["card"])
        bonus_row.pack(fill="x", pady=8)
        tk.Label(
            bonus_row,
            text="➕ Bonus:",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
            width=14,
            anchor="w",
        ).pack(side="left")
        bonus_color = "#4CAF50" if bonus > 0 else theme["fg"]
        tk.Label(
            bonus_row,
            text=f"₹{bonus:,.2f}",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=bonus_color,
        ).pack(side="right")

        # Separator line
        tk.Frame(details_container, bg=theme["fg"], height=1).pack(fill="x", pady=8)

        # Deductions
        deductions_row = tk.Frame(details_container, bg=theme["card"])
        deductions_row.pack(fill="x", pady=8)
        tk.Label(
            deductions_row,
            text="➖ Deductions:",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
            width=14,
            anchor="w",
        ).pack(side="left")
        deductions_color = "#F44336" if deductions > 0 else theme["fg"]
        tk.Label(
            deductions_row,
            text=f"₹{deductions:,.2f}",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=deductions_color,
        ).pack(side="right")

        # Thick separator for total
        tk.Frame(details_container, bg=theme["fg"], height=2).pack(fill="x", pady=15)

        # Net Salary (Total)
        net_salary = salary + bonus - deductions
        total_row = tk.Frame(details_container, bg=theme["card"])
        total_row.pack(fill="x", pady=12)
        tk.Label(
            total_row,
            text="💰 Net Salary:",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
            width=14,
            anchor="w",
        ).pack(side="left")
        net_color = "#4CAF50" if net_salary > 0 else "#F44336"
        tk.Label(
            total_row,
            text=f"₹{net_salary:,.2f}",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=net_color,
        ).pack(side="right")

        # Analysis section (if base salary exists)
        if salary > 0:
            # Separator
            tk.Frame(details_container, bg=theme["fg"], height=1).pack(
                fill="x", pady=20
            )

            analysis_frame = tk.Frame(details_container, bg=theme["card"])
            analysis_frame.pack(fill="x")

            tk.Label(
                analysis_frame,
                text="📈 Quick Analysis",
                font=("Arial", 12, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).pack(anchor="w", pady=(0, 10))

            # Bonus percentage
            bonus_pct = (bonus / salary) * 100 if salary > 0 else 0
            bonus_analysis = tk.Frame(analysis_frame, bg=theme["card"])
            bonus_analysis.pack(fill="x", pady=3)
            tk.Label(
                bonus_analysis,
                text="Bonus Rate:",
                font=("Arial", 10),
                bg=theme["card"],
                fg=theme["fg"],
                width=12,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                bonus_analysis,
                text=f"{bonus_pct:.1f}% of base",
                font=("Arial", 10),
                bg=theme["card"],
                fg="#4CAF50",
            ).pack(side="left", padx=10)

            # Deduction percentage
            deduction_pct = (deductions / salary) * 100 if salary > 0 else 0
            deduction_analysis = tk.Frame(analysis_frame, bg=theme["card"])
            deduction_analysis.pack(fill="x", pady=3)
            tk.Label(
                deduction_analysis,
                text="Deduction Rate:",
                font=("Arial", 10),
                bg=theme["card"],
                fg=theme["fg"],
                width=12,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                deduction_analysis,
                text=f"{deduction_pct:.1f}% of base",
                font=("Arial", 10),
                bg=theme["card"],
                fg="#F44336",
            ).pack(side="left", padx=10)

            # Net percentage
            net_pct = (net_salary / salary) * 100 if salary > 0 else 0
            net_analysis = tk.Frame(analysis_frame, bg=theme["card"])
            net_analysis.pack(fill="x", pady=3)
            tk.Label(
                net_analysis,
                text="Net Rate:",
                font=("Arial", 10),
                bg=theme["card"],
                fg=theme["fg"],
                width=12,
                anchor="w",
            ).pack(side="left")
            net_color_analysis = (
                "#4CAF50"
                if net_pct >= 100
                else "#FF9800" if net_pct >= 90 else "#F44336"
            )
            tk.Label(
                net_analysis,
                text=f"{net_pct:.1f}% of base",
                font=("Arial", 10),
                bg=theme["card"],
                fg=net_color_analysis,
            ).pack(side="left", padx=10)

    except Exception as e:
        error_label = tk.Label(
            frame,
            text=f"Error loading salary data: {str(e)}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 12),
        )
        error_label.pack(pady=50)
        print(f"Salary pie chart error: {e}")


# Keep other chart functions as they were working
def show_heatmap(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    try:
        cursor.execute("SELECT date FROM attendance WHERE emp_id=?", (emp_id,))
        rows = cursor.fetchall()
        dates = [row[0] for row in rows]
        date_counts = {d: dates.count(d) for d in set(dates)}

        fig, ax = plt.subplots(
            figsize=(12, 7), facecolor=theme["bg"]
        )  # Increased width
        fig.subplots_adjust(
            left=0.1, right=0.9, top=0.85, bottom=0.2
        )  # More space for labels
        ax.set_facecolor(theme["card"])
        ax.tick_params(colors=theme["fg"])
        ax.xaxis.label.set_color(theme["fg"])
        ax.yaxis.label.set_color(theme["fg"])
        ax.title.set_color(theme["fg"])

        year, month = datetime.now().year, datetime.now().month
        days = list(calendar.Calendar().itermonthdays(year, month))
        labels, values = [], []

        for day in days:
            if day == 0:
                labels.append("")
                values.append(0)
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                labels.append(str(day))
                values.append(date_counts.get(date_str, 0))

        bars = ax.bar(labels, values, color=theme["button"])
        ax.set_title(
            f"Attendance Heatmap ({calendar.month_name[month]} {year})",
            fontsize=16,
            pad=25,
        )
        ax.set_ylabel("Sign-ins", fontsize=12)
        ax.set_xlabel("Day of Month", fontsize=12)

        # Rotate x-axis labels to prevent overlapping
        plt.xticks(rotation=45, ha="right")

        # Add value labels on bars
        for bar, value in zip(bars, values):
            if value > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 0.05,
                    f"{int(value)}",
                    ha="center",
                    va="bottom",
                    color=theme["fg"],
                    fontsize=10,
                )

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    except Exception as e:
        tk.Label(
            frame, text=f"Error loading heatmap: {str(e)}", bg=theme["bg"], fg="red"
        ).pack(pady=20)


def show_leaderboard(frame, cursor):
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    tk.Label(
        frame,
        text="🏆 Punctuality Leaderboard 🏆",
        font=("Arial", 16),
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(pady=10)

    leaderboard = tk.Frame(frame, bg=theme["card"])
    leaderboard.pack(padx=10, pady=10, fill="both", expand=True)

    try:
        cursor.execute(
            """ 
            SELECT e.name, COUNT(a.date),
                    SUM(CASE WHEN TIME(a.sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN TIME(a.sign_in) > '09:00:00' THEN 1 ELSE 0 END)
            FROM attendance a
            JOIN employees e ON a.emp_id = e.id
            WHERE a.sign_in IS NOT NULL
            GROUP BY a.emp_id
            ORDER BY COUNT(a.date) DESC
            LIMIT 5
        """
        )
        rows = cursor.fetchall()

        # Header
        header = tk.Frame(leaderboard, bg=theme["card"])
        header.pack(fill="x", padx=5, pady=2)
        tk.Label(
            header,
            text="Rank",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(side="left", padx=5, ipadx=5)
        tk.Label(
            header,
            text="Name",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(side="left", padx=20, ipadx=5)
        tk.Label(
            header,
            text="On-Time/Total",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(side="left", padx=20, ipadx=5)
        tk.Label(
            header,
            text="Badge",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(side="left", padx=20, ipadx=5)

        for i, (name, days, on_time, late) in enumerate(rows or [], 1):
            pct = on_time / days if days > 0 else 0
            badge = (
                "🥇 Gold" if pct >= 0.9 else "🥈 Silver" if pct >= 0.75 else "🥉 Bronze"
            )

            row_frame = tk.Frame(leaderboard, bg=theme["card"])
            row_frame.pack(fill="x", padx=5, pady=2)
            tk.Label(
                row_frame,
                text=f"{i}.",
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(side="left", padx=5, ipadx=5)
            tk.Label(
                row_frame,
                text=name,
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(side="left", padx=20, ipadx=5)
            tk.Label(
                row_frame,
                text=f"{on_time}/{days}",
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(side="left", padx=20, ipadx=5)
            tk.Label(
                row_frame,
                text=badge,
                bg=theme["card"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(side="left", padx=20, ipadx=5)

    except Exception as e:
        tk.Label(
            leaderboard,
            text=f"Error loading leaderboard: {str(e)}",
            bg=theme["card"],
            fg="red",
        ).pack(pady=20)


def show_attendance_bar(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    try:
        cursor.execute(
            """ 
            SELECT COUNT(*),
                    SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END)
            FROM attendance
            WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        row = cursor.fetchone()
        if not row or row[0] == 0:
            tk.Label(
                frame, text="No attendance data found.", bg=theme["bg"], fg=theme["fg"]
            ).pack(pady=50)
            return

        total, on_time, late = row

        fig, ax = plt.subplots(
            figsize=(10, 7), facecolor=theme["bg"]
        )  # Increased height
        fig.subplots_adjust(
            left=0.15, right=0.9, top=0.85, bottom=0.2
        )  # Better margins
        ax.set_facecolor(theme["card"])

        bars = ax.bar(
            ["On-Time", "Late"],
            [on_time, late],
            color=[theme["button"], theme["hover"]],
            width=0.6,
        )

        ax.set_title(
            "On-Time vs Late Attendance", color=theme["fg"], fontsize=16, pad=25
        )
        ax.set_ylabel("Number of Days", color=theme["fg"], fontsize=12)
        ax.tick_params(colors=theme["fg"])
        ax.xaxis.label.set_color(theme["fg"])
        ax.yaxis.label.set_color(theme["fg"])

        # Add value labels on bars
        for bar, value in zip(bars, [on_time, late]):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.5,
                f"{int(value)}",
                ha="center",
                va="bottom",
                color=theme["fg"],
                fontsize=14,
                fontweight="bold",
            )

        # Add percentage labels
        total_days = on_time + late
        if total_days > 0:
            on_time_pct = (on_time / total_days) * 100
            late_pct = (late / total_days) * 100

            ax.text(
                bars[0].get_x() + bars[0].get_width() / 2.0,
                bars[0].get_height() / 2,
                f"{on_time_pct:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=12,
                fontweight="bold",
            )
            ax.text(
                bars[1].get_x() + bars[1].get_width() / 2.0,
                bars[1].get_height() / 2,
                f"{late_pct:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=12,
                fontweight="bold",
            )

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    except Exception as e:
        tk.Label(
            frame,
            text=f"Error loading attendance bar chart: {str(e)}",
            bg=theme["bg"],
            fg="red",
        ).pack(pady=20)


def show_face_log(frame, emp_id, cursor):
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    tk.Label(
        frame,
        text="Recent Face Login History",
        font=("Arial", 14),
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(pady=10)

    log_frame = tk.Frame(frame, bg=theme["card"])
    log_frame.pack(fill="both", expand=True, padx=10, pady=5)

    try:
        cursor.execute(
            "SELECT date, sign_in FROM attendance WHERE emp_id=? ORDER BY date DESC LIMIT 10",
            (emp_id,),
        )
        rows = cursor.fetchall()

        if not rows:
            tk.Label(
                log_frame, text="No login data found.", bg=theme["card"], fg=theme["fg"]
            ).pack(pady=20)
        else:
            tree = ttk.Treeview(log_frame, columns=("Date", "Sign In"), show="headings")
            tree.heading("Date", text="Date")
            tree.heading("Sign In", text="Sign In Time")

            for date, sign_in in rows:
                tree.insert("", "end", values=(date, sign_in or "Not Recorded"))

            tree.pack(padx=10, pady=10, fill="both", expand=True)

    except Exception as e:
        tk.Label(
            log_frame,
            text=f"Error loading face log: {str(e)}",
            bg=theme["card"],
            fg="red",
        ).pack(pady=20)
