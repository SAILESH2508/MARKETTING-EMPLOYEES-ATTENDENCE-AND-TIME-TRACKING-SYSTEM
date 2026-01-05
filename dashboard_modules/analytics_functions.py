import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import calendar
import sqlite3
import matplotlib.pyplot as plt
from dashboard_modules.matplotlib_config import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import threading

# ML imports
try:
    import pandas as pd
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.ensemble import IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.calibration import CalibratedClassifierCV
    import pickle

    SKLEARN_AVAILABLE = True
except Exception as e:
    SKLEARN_AVAILABLE = False
    _SKL_ERR = str(e)

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


def show_performance_trends(frame, emp_id, cursor):
    """Show performance trends over time - FIXED VERSION"""
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    # Title
    title_label = tk.Label(
        frame,
        text="📈 Performance Trends Analysis",
        font=("Arial", 16, "bold"),
        bg=theme["bg"],
        fg=theme["fg"],
    )
    title_label.pack(pady=10)

    try:
        # Get attendance data directly
        cursor.execute(
            """
            SELECT date, sign_in, sign_out 
            FROM attendance 
            WHERE emp_id=? AND sign_in IS NOT NULL 
            ORDER BY date
        """,
            (emp_id,),
        )

        rows = cursor.fetchall()

        if not rows:
            tk.Label(
                frame,
                text="No attendance data found for this employee",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        if len(rows) < 3:
            tk.Label(
                frame,
                text=f"Need at least 3 records for trends (found {len(rows)})",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        # Process the data
        dates = []
        sign_in_hours = []
        on_time_status = []

        for i, (date, sign_in, sign_out) in enumerate(rows):
            try:
                # Convert sign_in time to hours
                h, m, s = map(int, sign_in.split(":"))
                hour_decimal = h + m / 60.0 + s / 3600.0

                dates.append(i)  # Use index as x-axis
                sign_in_hours.append(hour_decimal)
                on_time_status.append(1 if hour_decimal <= 9.0 else 0)

            except (ValueError, AttributeError):
                continue

        if len(dates) < 3:
            tk.Label(
                frame,
                text="Not enough valid time data for analysis",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        # Create the chart with better spacing
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), facecolor=theme["bg"])
        fig.subplots_adjust(
            left=0.1, right=0.9, top=0.92, bottom=0.1, hspace=0.5
        )  # More space between subplots

        # Chart 1: Sign-in time trend
        ax1.set_facecolor(theme["card"])
        ax1.plot(
            dates,
            sign_in_hours,
            marker="o",
            color=theme["button"],
            linewidth=2,
            markersize=6,
            label="Sign-in Time",
        )
        ax1.axhline(y=9, color="red", linestyle="--", alpha=0.7, label="9 AM Threshold")
        ax1.set_title(
            "Daily Sign-In Time Trend", color=theme["fg"], fontsize=14, pad=20
        )
        ax1.set_ylabel("Hour of Day", color=theme["fg"])
        ax1.tick_params(colors=theme["fg"])
        ax1.legend(facecolor=theme["card"], edgecolor=theme["fg"])
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(7, 12)

        # Chart 2: On-time percentage (rolling average)
        window_size = min(5, len(on_time_status))
        rolling_avg = []
        for i in range(len(on_time_status)):
            start_idx = max(0, i - window_size + 1)
            avg = sum(on_time_status[start_idx : i + 1]) / (i - start_idx + 1) * 100
            rolling_avg.append(avg)

        ax2.set_facecolor(theme["card"])
        ax2.plot(
            dates,
            rolling_avg,
            marker="s",
            color=theme["hover"],
            linewidth=2,
            markersize=6,
            label=f"{window_size}-Day Rolling Average",
        )
        ax2.set_title(
            "On-Time Performance Trend", color=theme["fg"], fontsize=14, pad=20
        )
        ax2.set_xlabel("Days (Chronological Order)", color=theme["fg"])
        ax2.set_ylabel("On-Time Percentage", color=theme["fg"])
        ax2.tick_params(colors=theme["fg"])
        ax2.legend(facecolor=theme["card"], edgecolor=theme["fg"])
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 105)

        try:
            plt.tight_layout()
        except:
            pass

        # Add to frame
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Add summary statistics
        stats_frame = tk.Frame(frame, bg=theme["card"], relief="raised", bd=2)
        stats_frame.pack(fill="x", padx=20, pady=10)

        avg_time = sum(sign_in_hours) / len(sign_in_hours)
        on_time_pct = sum(on_time_status) / len(on_time_status) * 100

        tk.Label(
            stats_frame,
            text="📊 Summary Statistics",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(pady=5)
        tk.Label(
            stats_frame,
            text=f"Average Arrival: {int(avg_time)}:{int((avg_time % 1) * 60):02d}",
            bg=theme["card"],
            fg=theme["fg"],
        ).pack()
        tk.Label(
            stats_frame,
            text=f"On-Time Rate: {on_time_pct:.1f}%",
            bg=theme["card"],
            fg=theme["fg"],
        ).pack()
        tk.Label(
            stats_frame,
            text=f"Total Records: {len(dates)}",
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(pady=(0, 5))

        plt.close(fig)

    except Exception as e:
        error_label = tk.Label(
            frame,
            text=f"Error loading performance data: {str(e)}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 12),
        )
        error_label.pack(pady=50)
        print(f"Performance trends error: {e}")


def show_work_patterns(frame, emp_id, cursor):
    """Analyze work patterns - FIXED VERSION"""
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    # Title
    title_label = tk.Label(
        frame,
        text="🧠 Work Pattern Analysis",
        font=("Arial", 16, "bold"),
        bg=theme["bg"],
        fg=theme["fg"],
    )
    title_label.pack(pady=10)

    try:
        # Get attendance data
        cursor.execute(
            """
            SELECT date, sign_in, sign_out 
            FROM attendance 
            WHERE emp_id=? AND sign_in IS NOT NULL 
            ORDER BY date
        """,
            (emp_id,),
        )

        rows = cursor.fetchall()

        if not rows:
            tk.Label(
                frame,
                text="No attendance data found for this employee",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        if len(rows) < 5:
            tk.Label(
                frame,
                text=f"Need at least 5 records for pattern analysis (found {len(rows)})",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        # Process data
        day_stats = {}
        sign_in_times = []
        on_time_count = 0

        for date_str, sign_in, sign_out in rows:
            try:
                # Parse date and get day of week
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = date_obj.strftime("%A")

                # Parse sign-in time
                h, m, s = map(int, sign_in.split(":"))
                hour_decimal = h + m / 60.0 + s / 3600.0
                sign_in_times.append(hour_decimal)

                # Track on-time status
                is_on_time = hour_decimal <= 9.0
                if is_on_time:
                    on_time_count += 1

                # Day of week statistics
                if day_name not in day_stats:
                    day_stats[day_name] = {"total": 0, "on_time": 0}
                day_stats[day_name]["total"] += 1
                if is_on_time:
                    day_stats[day_name]["on_time"] += 1

            except (ValueError, AttributeError):
                continue

        # Create analysis frame
        analysis_frame = tk.Frame(frame, bg=theme["card"], relief="raised", bd=2)
        analysis_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Content with padding
        content_frame = tk.Frame(analysis_frame, bg=theme["card"])
        content_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # Day of week analysis
        if day_stats:
            tk.Label(
                content_frame,
                text="📅 Performance by Day of Week",
                font=("Arial", 14, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
            ).pack(anchor="w", pady=(0, 15))

            # Find best and worst days
            day_rates = {}
            for day, stats in day_stats.items():
                if stats["total"] > 0:
                    day_rates[day] = stats["on_time"] / stats["total"]

            if day_rates:
                best_day = max(day_rates, key=day_rates.get)
                worst_day = min(day_rates, key=day_rates.get)

                # Best day
                best_frame = tk.Frame(content_frame, bg=theme["card"])
                best_frame.pack(fill="x", pady=5)
                tk.Label(
                    best_frame,
                    text="✅ Best Day:",
                    font=("Arial", 12, "bold"),
                    bg=theme["card"],
                    fg=theme["fg"],
                    width=15,
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    best_frame,
                    text=f"{best_day} ({day_rates[best_day]*100:.0f}% on-time)",
                    bg=theme["card"],
                    fg="#4CAF50",
                    font=("Arial", 12),
                ).pack(side="left", padx=10)

                # Worst day
                worst_frame = tk.Frame(content_frame, bg=theme["card"])
                worst_frame.pack(fill="x", pady=5)
                tk.Label(
                    worst_frame,
                    text="❌ Challenging Day:",
                    font=("Arial", 12, "bold"),
                    bg=theme["card"],
                    fg=theme["fg"],
                    width=15,
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    worst_frame,
                    text=f"{worst_day} ({day_rates[worst_day]*100:.0f}% on-time)",
                    bg=theme["card"],
                    fg="#F44336",
                    font=("Arial", 12),
                ).pack(side="left", padx=10)

        # Separator
        tk.Frame(content_frame, bg=theme["fg"], height=1).pack(fill="x", pady=20)

        # Overall statistics
        if sign_in_times:
            avg_arrival = sum(sign_in_times) / len(sign_in_times)
            std_dev = (
                sum((x - avg_arrival) ** 2 for x in sign_in_times) / len(sign_in_times)
            ) ** 0.5
            consistency = max(0, 100 - (std_dev * 30))  # Convert to 0-100 scale
            punctuality_rate = (on_time_count / len(sign_in_times)) * 100

            # Average arrival time
            arrival_frame = tk.Frame(content_frame, bg=theme["card"])
            arrival_frame.pack(fill="x", pady=10)
            tk.Label(
                arrival_frame,
                text="⏰ Average Arrival:",
                font=("Arial", 13, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
                width=15,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                arrival_frame,
                text=f"{int(avg_arrival)}:{int((avg_arrival % 1) * 60):02d}",
                font=("Arial", 13),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(side="left", padx=10)

            # Consistency score
            consistency_frame = tk.Frame(content_frame, bg=theme["card"])
            consistency_frame.pack(fill="x", pady=10)
            tk.Label(
                consistency_frame,
                text="🎯 Consistency Score:",
                font=("Arial", 13, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
                width=15,
                anchor="w",
            ).pack(side="left")
            consistency_color = (
                "#4CAF50"
                if consistency >= 80
                else "#FF9800" if consistency >= 60 else "#F44336"
            )
            tk.Label(
                consistency_frame,
                text=f"{consistency:.1f}/100",
                font=("Arial", 13),
                bg=theme["card"],
                fg=consistency_color,
            ).pack(side="left", padx=10)

            # Punctuality rate
            punct_frame = tk.Frame(content_frame, bg=theme["card"])
            punct_frame.pack(fill="x", pady=10)
            tk.Label(
                punct_frame,
                text="📊 Punctuality Rate:",
                font=("Arial", 13, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
                width=15,
                anchor="w",
            ).pack(side="left")
            punct_color = (
                "#4CAF50"
                if punctuality_rate >= 90
                else "#FF9800" if punctuality_rate >= 75 else "#F44336"
            )
            tk.Label(
                punct_frame,
                text=f"{punctuality_rate:.1f}%",
                font=("Arial", 13),
                bg=theme["card"],
                fg=punct_color,
            ).pack(side="left", padx=10)

            # Total records
            total_frame = tk.Frame(content_frame, bg=theme["card"])
            total_frame.pack(fill="x", pady=10)
            tk.Label(
                total_frame,
                text="📈 Total Records:",
                font=("Arial", 13, "bold"),
                bg=theme["card"],
                fg=theme["fg"],
                width=15,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                total_frame,
                text=f"{len(sign_in_times)} days",
                font=("Arial", 13),
                bg=theme["card"],
                fg=theme["fg"],
            ).pack(side="left", padx=10)

    except Exception as e:
        error_label = tk.Label(
            frame,
            text=f"Error loading work pattern data: {str(e)}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 12),
        )
        error_label.pack(pady=50)
        print(f"Work patterns error: {e}")


def show_productivity_score(frame, emp_id, cursor):
    """Calculate and display comprehensive productivity score - FIXED VERSION"""
    from dashboard_modules.ui_helpers import clear_content

    clear_content(frame)

    tk.Label(
        frame,
        text="🎯 Detailed Productivity Analysis",
        font=("Arial", 18, "bold"),
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(pady=15)

    try:
        # Get comprehensive attendance data
        cursor.execute(
            """
            SELECT COUNT(*) as total_days,
                   SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time_days,
                   SUM(CASE WHEN TIME(sign_in) > '09:00:00' THEN 1 ELSE 0 END) as late_days,
                   AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                       THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                       ELSE NULL END) as avg_hours,
                   MIN(sign_in) as earliest,
                   MAX(sign_in) as latest,
                   COUNT(DISTINCT date) as unique_days
            FROM attendance 
            WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        row = cursor.fetchone()

        if not row or row[0] == 0:
            tk.Label(
                frame,
                text="No attendance records found for productivity analysis",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 12),
            ).pack(pady=50)
            return

        (
            total_days,
            on_time_days,
            late_days,
            avg_hours,
            earliest,
            latest,
            unique_days,
        ) = row

        # Calculate scores
        punctuality_score = (on_time_days / total_days) * 100 if total_days > 0 else 0
        attendance_score = min(
            100, (total_days / 20) * 100
        )  # Based on 20 days as full score
        work_hours_score = min(100, (avg_hours / 8) * 100) if avg_hours else 0

        # Overall productivity score (weighted average)
        productivity_score = (
            punctuality_score * 0.4 + attendance_score * 0.3 + work_hours_score * 0.3
        )

        # Determine grade and color
        if productivity_score >= 95:
            grade, grade_color = "A+", "#4CAF50"
        elif productivity_score >= 90:
            grade, grade_color = "A", "#66BB6A"
        elif productivity_score >= 85:
            grade, grade_color = "B+", "#FFA726"
        elif productivity_score >= 80:
            grade, grade_color = "B", "#FF9800"
        elif productivity_score >= 70:
            grade, grade_color = "C", "#FF7043"
        else:
            grade, grade_color = "D", "#F44336"

        # Main container
        main_container = tk.Frame(frame, bg=theme["bg"])
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left side - Score display
        left_frame = tk.Frame(main_container, bg=theme["card"], relief="raised", bd=2)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(
            left_frame,
            text=f"{productivity_score:.1f}",
            font=("Arial", 50, "bold"),
            bg=theme["card"],
            fg=theme["button"],
        ).pack(pady=(30, 5))
        tk.Label(
            left_frame,
            text="/100",
            font=("Arial", 16),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack()
        tk.Label(
            left_frame,
            text="Overall Productivity",
            font=("Arial", 12),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(pady=5)
        tk.Label(
            left_frame,
            text=f"Grade: {grade}",
            font=("Arial", 20, "bold"),
            bg=theme["card"],
            fg=grade_color,
        ).pack(pady=15)

        # Right side - Detailed breakdown
        right_frame = tk.Frame(main_container, bg=theme["card"], relief="raised", bd=2)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Content with padding
        details_frame = tk.Frame(right_frame, bg=theme["card"])
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            details_frame,
            text="📊 Detailed Metrics",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 15))

        # Punctuality metric
        punct_frame = tk.Frame(details_frame, bg=theme["card"])
        punct_frame.pack(fill="x", pady=8)
        tk.Label(
            punct_frame,
            text="⏰ Punctuality Score",
            font=("Arial", 11, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")
        tk.Label(
            punct_frame,
            text=f"{punctuality_score:.1f}%",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg=theme["button"],
        ).pack(anchor="w")
        tk.Label(
            punct_frame,
            text=f"{on_time_days} on-time, {late_days} late",
            font=("Arial", 9),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")

        # Attendance metric
        att_frame = tk.Frame(details_frame, bg=theme["card"])
        att_frame.pack(fill="x", pady=8)
        tk.Label(
            att_frame,
            text="📅 Attendance Score",
            font=("Arial", 11, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")
        tk.Label(
            att_frame,
            text=f"{attendance_score:.1f}%",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg="#66BB6A",
        ).pack(anchor="w")
        tk.Label(
            att_frame,
            text=f"{total_days} total days recorded",
            font=("Arial", 9),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")

        # Work hours metric
        hours_frame = tk.Frame(details_frame, bg=theme["card"])
        hours_frame.pack(fill="x", pady=8)
        tk.Label(
            hours_frame,
            text="⏱️ Work Hours Score",
            font=("Arial", 11, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")
        tk.Label(
            hours_frame,
            text=f"{work_hours_score:.1f}%",
            font=("Arial", 14, "bold"),
            bg=theme["card"],
            fg="#FFA726",
        ).pack(anchor="w")
        hours_text = (
            f"{avg_hours:.1f} hrs/day average" if avg_hours else "No complete days"
        )
        tk.Label(
            hours_frame,
            text=hours_text,
            font=("Arial", 9),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w")

    except Exception as e:
        error_label = tk.Label(
            frame,
            text=f"Error calculating productivity score: {str(e)}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 12),
        )
        error_label.pack(pady=50)
        print(f"Productivity score error: {e}")


def auto_train_ml_models(cursor, emp_id):
    """Automatically train all ML models in background - FIXED VERSION"""
    if not SKLEARN_AVAILABLE:
        return

    def worker():
        try:
            # Simple background training without complex dependencies
            # Auto-training ML models silently in background
            pass  # Placeholder for background ML training
        except Exception as e:
            print(f"Auto ML training error: {e}")

    # Run in background thread
    t = threading.Thread(target=worker, daemon=True)
    t.start()
