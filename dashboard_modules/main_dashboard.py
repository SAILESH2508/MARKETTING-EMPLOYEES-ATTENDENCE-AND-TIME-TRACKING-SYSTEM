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

# Centralized Imports from ui_helpers
from dashboard_modules.ui_helpers import (
    theme,
    DARK_MODE,
    LIGHT_MODE,
    HEADER_FONT,
    SUBHEADER_FONT,
    TITLE_FONT,
    BODY_FONT,
    BUTTON_FONT,
    CustomButton,
    fade_in,
    update_theme,
    MODEL_DIR,
    RoundedFrame,
)

# Import ML functions
try:
    from dashboard_modules.ml_functions import (
        get_ml_status,
        load_attendance_df,
        train_punctuality_model,
        train_anomaly_detector,
        train_salary_predictor,
        predict_punctuality_for_emp,
        predict_salary,
    )
except ImportError as e:
    print(f"ML functions import error: {e}")

    def get_ml_status(cursor):
        return "ML functions not available"


# Global reference for the content frame (used for navigation)
content = None

# Global flag to prevent ML training loops
ml_training_in_progress = False
ml_trained_this_session = False


def employee_dashboard(root, emp_id, name, cursor, conn):
    """Fixed main dashboard with improved error handling and performance"""

    global content
    dashboard = tk.Toplevel(root)
    dashboard.title(f"Employee Dashboard - {name}")
    dashboard.geometry("1400x800")

    # Proper cleanup function to prevent Tkinter errors
    def on_closing():
        try:
            dashboard.protocol("WM_DELETE_WINDOW", lambda: None)
        except:
            pass
        try:
            if conn:
                conn.close()
        except:
            pass
        try:
            dashboard.quit()
        except:
            pass
        try:
            dashboard.destroy()
        except:
            pass
        try:
            root.destroy()
        except:
            pass

    dashboard.protocol("WM_DELETE_WINDOW", on_closing)
    dashboard.configure(bg=theme["bg"])

    # Set alpha to 1.0 immediately for stability
    dashboard.attributes("-alpha", 1.0)

    def toggle_theme_update():
        """Fixed theme toggle function"""
        try:
            target_mode = LIGHT_MODE if theme["bg"] == DARK_MODE["bg"] else DARK_MODE
            theme.clear()
            theme.update(target_mode)
            update_theme(dashboard)
        except Exception as e:
            print(f"Theme toggle error: {e}")

    # Top bar with employee info and controls
    top_bar = tk.Frame(dashboard, bg=theme["bg"])
    top_bar.pack(fill="x", pady=(5, 0))

    # Left side - Employee name with welcome message
    name_frame = tk.Frame(top_bar, bg=theme["bg"])
    name_frame.pack(side="left", padx=15, pady=8)
    tk.Label(
        name_frame,
        text=f"Welcome, {name}!",
        font=HEADER_FONT,
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(anchor="w")
    tk.Label(
        name_frame,
        text=f"ID: {emp_id}",
        font=TITLE_FONT,
        bg=theme["bg"],
        fg=theme["button"],
    ).pack(anchor="w")

    # Right side - Action buttons
    try:
        CustomButton(top_bar, text="🌗 Toggle Mode", command=toggle_theme_update).pack(
            side="right", padx=5
        )
        CustomButton(
            top_bar,
            text="🔄 Refresh",
            command=lambda: refresh_main_dashboard(content, emp_id, cursor),
        ).pack(side="right", padx=5)
        CustomButton(
            top_bar,
            text="🚪 Logout",
            command=on_closing,
            bg=theme.get("error", "#F44336"),
        ).pack(side="right", padx=5)
    except Exception as e:
        print(f"Button creation error: {e}")

    # Quick action buttons bar
    action_bar = tk.Frame(dashboard, bg=theme["bg"])
    action_bar.pack(fill="x", padx=15, pady=10)

    try:
        CustomButton(
            action_bar,
            text="✅ Sign In",
            command=lambda: sign_in_fixed(emp_id, name, cursor, conn, content),
            bg=theme.get("success", "#4CAF50"),
            width=15,
        ).pack(side="left", padx=5)
        CustomButton(
            action_bar,
            text="❌ Sign Out",
            command=lambda: sign_out_fixed(emp_id, cursor, conn, content),
            bg=theme.get("error", "#F44336"),
            width=15,
        ).pack(side="left", padx=5)
    except Exception as e:
        print(f"Action button error: {e}")

    # Create tabbed interface with error handling
    try:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=theme["card"],
            foreground=theme["fg"],
            padding=[20, 10],
            font=TITLE_FONT,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme["button"])],
            foreground=[("selected", theme.get("button_fg", "white"))],
        )

        notebook = ttk.Notebook(dashboard)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Create tabs
        tab_dashboard = tk.Frame(notebook, bg=theme["bg"])
        tab_attendance = tk.Frame(notebook, bg=theme["bg"])
        tab_analytics = tk.Frame(notebook, bg=theme["bg"])
        tab_ml = tk.Frame(notebook, bg=theme["bg"])

        notebook.add(tab_dashboard, text="📊 Dashboard")
        notebook.add(tab_attendance, text="📅 Attendance")
        notebook.add(tab_analytics, text="📈 Analytics")
        notebook.add(tab_ml, text="🤖 ML Insights")

        # Dashboard tab content - FIXED VERSION
        content = tab_dashboard
        show_main_dashboard_content(content, emp_id, cursor)

        # Attendance tab - create sub-notebook with error handling
        try:
            setup_attendance_tab(tab_attendance, emp_id, cursor)
        except Exception as e:
            tk.Label(
                tab_attendance,
                text=f"Attendance tab error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack(pady=20)

        # Analytics tab - create sub-notebook with error handling
        try:
            setup_analytics_tab(tab_analytics, emp_id, cursor)
        except Exception as e:
            tk.Label(
                tab_analytics,
                text=f"Analytics tab error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack(pady=20)

        # ML tab with error handling
        try:
            setup_ml_tab(tab_ml, emp_id, cursor)
        except Exception as e:
            tk.Label(tab_ml, text=f"ML tab error: {e}", bg=theme["bg"], fg="red").pack(
                pady=20
            )

    except Exception as e:
        # Fallback if notebook creation fails
        tk.Label(
            dashboard,
            text=f"Dashboard creation error: {e}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 14),
        ).pack(pady=50)


def setup_attendance_tab(tab_attendance, emp_id, cursor):
    """Setup attendance tab with error handling"""
    try:
        from dashboard_modules.chart_functions import (
            show_heatmap,
            show_face_log,
            show_leaderboard,
        )

        attendance_notebook = ttk.Notebook(tab_attendance)
        attendance_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        heatmap_frame = tk.Frame(attendance_notebook, bg=theme["bg"])
        history_frame = tk.Frame(attendance_notebook, bg=theme["bg"])
        leaderboard_frame = tk.Frame(attendance_notebook, bg=theme["bg"])

        attendance_notebook.add(heatmap_frame, text="Heatmap")
        attendance_notebook.add(history_frame, text="Login History")
        attendance_notebook.add(leaderboard_frame, text="Leaderboard")

        # Load content with individual error handling
        try:
            show_heatmap(heatmap_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                heatmap_frame, text=f"Heatmap error: {e}", bg=theme["bg"], fg="red"
            ).pack()

        try:
            show_face_log(history_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                history_frame, text=f"History error: {e}", bg=theme["bg"], fg="red"
            ).pack()

        try:
            show_leaderboard(leaderboard_frame, cursor)
        except Exception as e:
            tk.Label(
                leaderboard_frame,
                text=f"Leaderboard error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack()

    except ImportError as e:
        tk.Label(
            tab_attendance, text=f"Import error: {e}", bg=theme["bg"], fg="red"
        ).pack()


def setup_analytics_tab(tab_analytics, emp_id, cursor):
    """Setup analytics tab with error handling"""
    try:
        from dashboard_modules.analytics_functions import (
            show_performance_trends,
            show_work_patterns,
            show_productivity_score,
        )
        from dashboard_modules.chart_functions import (
            show_salary_pie,
            show_attendance_bar,
        )

        analytics_notebook = ttk.Notebook(tab_analytics)
        analytics_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        productivity_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
        performance_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
        patterns_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
        salary_frame = tk.Frame(analytics_notebook, bg=theme["bg"])
        ontime_frame = tk.Frame(analytics_notebook, bg=theme["bg"])

        analytics_notebook.add(productivity_frame, text="Productivity Score")
        analytics_notebook.add(performance_frame, text="Performance Trends")
        analytics_notebook.add(patterns_frame, text="Work Patterns")
        analytics_notebook.add(salary_frame, text="Salary Breakdown")
        analytics_notebook.add(ontime_frame, text="On-Time vs Late")

        # Load content with individual error handling
        try:
            show_productivity_score(productivity_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                productivity_frame,
                text=f"Productivity error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack()

        try:
            show_performance_trends(performance_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                performance_frame,
                text=f"Performance trends error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack()

        try:
            show_work_patterns(patterns_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                patterns_frame,
                text=f"Work patterns error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack()

        try:
            show_salary_pie(salary_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                salary_frame, text=f"Salary chart error: {e}", bg=theme["bg"], fg="red"
            ).pack()

        try:
            show_attendance_bar(ontime_frame, emp_id, cursor)
        except Exception as e:
            tk.Label(
                ontime_frame,
                text=f"Attendance bar error: {e}",
                bg=theme["bg"],
                fg="red",
            ).pack()

    except ImportError as e:
        tk.Label(
            tab_analytics, text=f"Analytics import error: {e}", bg=theme["bg"], fg="red"
        ).pack()


def setup_ml_tab(tab_ml, emp_id, cursor):
    """Setup ML tab with comprehensive ML functionality"""
    try:
        # Clear any existing content
        for widget in tab_ml.winfo_children():
            widget.destroy()

        # Main container
        main_container = tk.Frame(tab_ml, bg=theme["bg"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_frame = tk.Frame(main_container, bg=theme["bg"])
        title_frame.pack(fill="x", pady=(0, 20))
        tk.Label(
            title_frame,
            text="🤖 ML Insights & Analytics",
            font=HEADER_FONT,
            bg=theme["bg"],
            fg=theme["fg"],
        ).pack(anchor="w")

        if not SKLEARN_AVAILABLE:
            # Show installation instructions if ML libraries not available
            error_frame = RoundedFrame(main_container, bg_color=theme["card"])
            error_frame.pack(fill="both", expand=True, padx=10, pady=10)

            tk.Label(
                error_frame.inner_frame,
                text="❌ Machine Learning Libraries Not Available",
                font=("Segoe UI", 14, "bold"),
                bg=theme["card"],
                fg="red",
            ).pack(pady=20)
            tk.Label(
                error_frame.inner_frame,
                text="To enable ML features, install required libraries:",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack(pady=10)
            tk.Label(
                error_frame.inner_frame,
                text="pip install scikit-learn pandas",
                font=("Courier", 12),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(pady=5)
            return

        # ML Status and Controls using RoundedFrame
        status_frame = RoundedFrame(main_container, bg_color=theme["card"])
        status_frame.pack(fill="x", pady=(0, 15))

        status_content = status_frame.inner_frame

        tk.Label(
            status_content,
            text="✅ Machine Learning Ready",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg="#4CAF50",
        ).pack(anchor="w")

        # Model status
        model_status = get_ml_status(cursor)
        tk.Label(
            status_content,
            text=model_status,
            font=("Courier", 10),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(5, 0))

        # ML Features Grid
        features_frame = tk.Frame(main_container, bg=theme["bg"])
        features_frame.pack(fill="both", expand=True)

        # Left column - Training & Models
        left_column = tk.Frame(features_frame, bg=theme["bg"])
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Model Training Section using RoundedFrame
        training_frame = RoundedFrame(left_column, bg_color=theme["card"])
        training_frame.pack(fill="x", pady=(0, 15))

        training_content = training_frame.inner_frame

        tk.Label(
            training_content,
            text="🎯 Model Training",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 10))

        # Training buttons
        btn_frame1 = tk.Frame(training_content, bg=theme["card"])
        btn_frame1.pack(fill="x", pady=2)

        tk.Button(
            btn_frame1,
            text="Train Punctuality Model",
            command=lambda: train_punctuality_model(cursor, silent=False),
            bg=theme["button"],
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_frame1,
            text="Train Anomaly Detector",
            command=lambda: train_anomaly_detector(cursor, silent=False),
            bg=theme["button"],
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left")

        btn_frame2 = tk.Frame(training_content, bg=theme["card"])
        btn_frame2.pack(fill="x", pady=2)

        tk.Button(
            btn_frame2,
            text="Train Salary Predictor",
            command=lambda: train_salary_predictor(cursor, silent=False),
            bg=theme["button"],
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_frame2,
            text="Train All Models",
            command=lambda: train_all_models(cursor),
            bg=theme["hover"],
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left")

        # Predictions Section using RoundedFrame
        predictions_frame = RoundedFrame(left_column, bg_color=theme["card"])
        predictions_frame.pack(fill="both", expand=True)

        pred_content = predictions_frame.inner_frame

        tk.Label(
            pred_content,
            text="🔮 Predictions & Analysis",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 10))

        # Prediction buttons
        pred_btn_frame1 = tk.Frame(pred_content, bg=theme["card"])
        pred_btn_frame1.pack(fill="x", pady=2)

        tk.Button(
            pred_btn_frame1,
            text="Predict Punctuality",
            command=lambda: predict_punctuality_for_emp(emp_id, cursor),
            bg="#4CAF50",
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            pred_btn_frame1,
            text="Predict Salary",
            command=lambda: predict_salary(emp_id, cursor),
            bg="#4CAF50",
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(side="left")

        # Right column - Analysis Results
        right_column = tk.Frame(features_frame, bg=theme["bg"])
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Anomaly Detection Section using RoundedFrame
        anomaly_frame = RoundedFrame(right_column, bg_color=theme["card"])
        anomaly_frame.pack(fill="both", expand=True, pady=(0, 15))

        anomaly_content = anomaly_frame.inner_frame

        tk.Label(
            anomaly_content,
            text="🚨 Anomaly Detection",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 10))

        # Anomaly scan button
        tk.Button(
            anomaly_content,
            text="Run Anomaly Scan",
            command=lambda: show_anomaly_results(anomaly_results_frame, cursor),
            bg="#FF9800",
            fg="white",
            font=BUTTON_FONT,
            relief="flat",
        ).pack(anchor="w", pady=(0, 10))

        # Results area
        anomaly_results_frame = tk.Frame(anomaly_content, bg=theme["card"])
        anomaly_results_frame.pack(fill="both", expand=True)

        # ML Insights Section using RoundedFrame
        insights_frame = RoundedFrame(right_column, bg_color=theme["card"])
        insights_frame.pack(fill="both", expand=True)

        insights_content = insights_frame.inner_frame

        tk.Label(
            insights_content,
            text="📊 ML Insights",
            font=("Arial", 12, "bold"),
            bg=theme["card"],
            fg=theme["fg"],
        ).pack(anchor="w", pady=(0, 10))

        # Show ML insights
        show_ml_insights(insights_content, emp_id, cursor)

    except Exception as e:
        error_label = tk.Label(
            tab_ml,
            text=f"ML tab error: {e}",
            bg=theme["bg"],
            fg="red",
            font=("Arial", 12),
        )
        error_label.pack(pady=50)
        print(f"ML tab setup error: {e}")


def train_all_models(cursor):
    """Train all ML models with progress feedback"""
    try:
        messagebox.showinfo(
            "ML Training", "Training all models... This may take a moment."
        )

        # Train each model
        train_punctuality_model(cursor, silent=True)
        train_anomaly_detector(cursor, silent=True)
        train_salary_predictor(cursor, silent=True)

        messagebox.showinfo("ML Training", "All models trained successfully!")

    except Exception as e:
        messagebox.showerror("ML Training Error", f"Error training models: {e}")


def show_anomaly_results(frame, cursor):
    """Show anomaly detection results in the frame"""
    try:
        # Clear previous results
        for widget in frame.winfo_children():
            widget.destroy()

        path = os.path.join(MODEL_DIR, "anomaly.pkl")
        if not os.path.exists(path):
            tk.Label(
                frame,
                text="❌ Anomaly model not found. Train it first.",
                bg=theme["card"],
                fg="red",
            ).pack(pady=10)
            return

        df, err = load_attendance_df(cursor)
        if err:
            tk.Label(frame, text=f"❌ Error: {err}", bg=theme["card"], fg="red").pack(
                pady=10
            )
            return

        import pickle

        with open(path, "rb") as f:
            iso = pickle.load(f)

        X = df[["sign_in_seconds"]].fillna(df["sign_in_seconds"].median())
        preds = iso.predict(X)
        anomalies = df[preds == -1]

        if anomalies.empty:
            tk.Label(
                frame, text="✅ No anomalies detected", bg=theme["card"], fg="#4CAF50"
            ).pack(pady=10)
        else:
            tk.Label(
                frame,
                text=f"⚠️ Found {len(anomalies)} anomalies:",
                bg=theme["card"],
                fg="#FF9800",
            ).pack(pady=(0, 5))

            # Create scrollable list
            list_frame = tk.Frame(frame, bg=theme["card"])
            list_frame.pack(fill="both", expand=True)

            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(
                list_frame,
                yscrollcommand=scrollbar.set,
                bg=theme["card"],
                fg=theme["fg"],
                font=("Courier", 9),
            )
            listbox.pack(fill="both", expand=True)
            scrollbar.config(command=listbox.yview)

            for _, row in anomalies.iterrows():
                listbox.insert(
                    "end", f"ID:{row['emp_id']} {row['date']} {row['sign_in']}"
                )

    except Exception as e:
        tk.Label(frame, text=f"❌ Error: {e}", bg=theme["card"], fg="red").pack(pady=10)


def show_ml_insights(frame, emp_id, cursor):
    """Show ML insights and statistics"""
    try:
        # Get attendance data for insights
        df, err = load_attendance_df(cursor)
        if err:
            tk.Label(
                frame,
                text=f"No data for insights: {err}",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack(pady=10)
            return

        # Calculate insights
        total_records = len(df)
        on_time_rate = df["on_time"].mean() * 100 if len(df) > 0 else 0
        unique_employees = df["emp_id"].nunique()

        # Display insights
        insights_text = f"""📈 Dataset Overview:
• Total Records: {total_records}
• Unique Employees: {unique_employees}
• Overall On-Time Rate: {on_time_rate:.1f}%

🎯 Model Status:"""

        # Check model files
        models = ["punctuality.pkl", "salary_reg.pkl", "anomaly.pkl"]
        model_names = ["Punctuality", "Salary Predictor", "Anomaly Detector"]

        for model, name in zip(models, model_names):
            path = os.path.join(MODEL_DIR, model)
            status = "✅ Ready" if os.path.exists(path) else "❌ Not Trained"
            insights_text += f"\n• {name}: {status}"

        tk.Label(
            frame,
            text=insights_text,
            bg=theme["card"],
            fg=theme["fg"],
            font=("Courier", 10),
            justify="left",
        ).pack(anchor="w", pady=10)

    except Exception as e:
        tk.Label(
            frame, text=f"Error generating insights: {e}", bg=theme["card"], fg="red"
        ).pack(pady=10)


def show_main_dashboard_content(frame, emp_id, cursor):
    """Fixed main dashboard content with better error handling"""

    # Clear any existing content
    for widget in frame.winfo_children():
        widget.destroy()

    # Create main container with scrolling
    main_container = tk.Frame(frame, bg=theme["bg"])
    main_container.pack(fill="both", expand=True, padx=10, pady=10)

    # Title
    title_frame = tk.Frame(main_container, bg=theme["bg"])
    title_frame.pack(fill="x", pady=(0, 20))
    tk.Label(
        title_frame,
        text="📊 Dashboard Overview",
        font=HEADER_FONT,
        bg=theme["bg"],
        fg=theme["fg"],
    ).pack(anchor="w")

    # Create grid layout
    grid_frame = tk.Frame(main_container, bg=theme["bg"])
    grid_frame.pack(fill="both", expand=True)

    # Configure grid weights
    grid_frame.grid_columnconfigure(0, weight=1)
    grid_frame.grid_columnconfigure(1, weight=1)
    grid_frame.grid_columnconfigure(2, weight=1)

    # Row 1: Quick Stats
    create_quick_stats_card(grid_frame, 0, 0, emp_id, cursor)
    create_salary_summary_card(grid_frame, 0, 1, emp_id, cursor)
    create_status_card(grid_frame, 0, 2, emp_id, cursor)

    # Row 2: Performance Overview
    create_performance_card(grid_frame, 1, 0, emp_id, cursor, colspan=2)
    create_recent_activity_card(grid_frame, 1, 2, emp_id, cursor)


def create_quick_stats_card(parent, row, col, emp_id, cursor):
    """Create quick statistics card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    # Card content
    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="📈 Quick Stats",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        # Get attendance count
        cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL",
            (emp_id,),
        )
        total_days = cursor.fetchone()[0]

        # Get on-time count
        cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE emp_id=? AND TIME(sign_in) <= '09:00:00'",
            (emp_id,),
        )
        on_time_days = cursor.fetchone()[0]

        # Calculate percentage
        on_time_pct = (on_time_days / total_days * 100) if total_days > 0 else 0

        # Display stats
        stats_frame = tk.Frame(content_frame, bg=theme["card"])
        stats_frame.pack(fill="x")

        tk.Label(
            stats_frame, text="Total Days:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            stats_frame,
            text=f"{total_days}",
            font=("Arial", 16, "bold"),
            bg=theme["card"],
            fg=theme["button"],
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            stats_frame, text="On-Time Rate:", bg=theme["card"], fg=theme["fg"]
        ).pack(anchor="w")
        tk.Label(
            stats_frame,
            text=f"{on_time_pct:.1f}%",
            font=("Arial", 16, "bold"),
            bg=theme["card"],
            fg=theme["success"] if on_time_pct >= 80 else theme["warning"],
        ).pack(anchor="w")

    except Exception as e:
        tk.Label(
            content_frame, text=f"Error loading stats: {e}", bg=theme["card"], fg="red"
        ).pack()


def create_salary_summary_card(parent, row, col, emp_id, cursor):
    """Create salary summary card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="💰 Salary Info",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        cursor.execute(
            "SELECT salary, bonus, deductions FROM salary WHERE emp_id=?", (emp_id,)
        )
        result = cursor.fetchone()

        if result:
            salary, bonus, deductions = result
            salary = salary or 0
            bonus = bonus or 0
            deductions = deductions or 0
            net_salary = salary + bonus - deductions

            tk.Label(
                content_frame, text="Base Salary:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                content_frame,
                text=f"₹{salary:,.0f}",
                font=("Arial", 14, "bold"),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(anchor="w", pady=(0, 5))

            tk.Label(
                content_frame, text="Net Salary:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                content_frame,
                text=f"₹{net_salary:,.0f}",
                font=("Arial", 14, "bold"),
                bg=theme["card"],
                fg=theme["success"],
            ).pack(anchor="w")
        else:
            tk.Label(
                content_frame,
                text="No salary data available",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(
            content_frame, text=f"Error loading salary: {e}", bg=theme["card"], fg="red"
        ).pack()


def create_status_card(parent, row, col, emp_id, cursor):
    """Create current status card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="🕐 Today's Status",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT sign_in, sign_out FROM attendance WHERE emp_id=? AND date=?",
            (emp_id, today),
        )
        result = cursor.fetchone()

        if result and result[0]:
            sign_in_time = result[0]
            sign_out_time = result[1]

            tk.Label(
                content_frame, text="Sign In:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                content_frame,
                text=sign_in_time,
                font=("Arial", 12, "bold"),
                bg=theme["card"],
                fg=theme["success"],
            ).pack(anchor="w", pady=(0, 5))

            if sign_out_time:
                tk.Label(
                    content_frame, text="Sign Out:", bg=theme["card"], fg=theme["fg"]
                ).pack(anchor="w")
                tk.Label(
                    content_frame,
                    text=sign_out_time,
                    font=("Arial", 12, "bold"),
                    bg=theme["card"],
                    fg=theme["warning"],
                ).pack(anchor="w")
                tk.Label(
                    content_frame,
                    text="✅ Day Complete",
                    bg=theme["card"],
                    fg=theme["success"],
                ).pack(anchor="w", pady=(5, 0))
            else:
                tk.Label(
                    content_frame,
                    text="🔄 Currently Working",
                    bg=theme["card"],
                    fg=theme["button"],
                ).pack(anchor="w", pady=(5, 0))
        else:
            tk.Label(
                content_frame,
                text="❌ Not signed in today",
                bg=theme["card"],
                fg=theme["warning"],
            ).pack()

    except Exception as e:
        tk.Label(
            content_frame, text=f"Error loading status: {e}", bg=theme["card"], fg="red"
        ).pack()


def create_performance_card(parent, row, col, emp_id, cursor, colspan=1):
    """Create performance overview card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(
        row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=10
    )

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="🎯 Performance Overview",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        # Get performance metrics
        cursor.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN TIME(sign_in) <= '09:00:00' THEN 1 ELSE 0 END) as on_time,
                   AVG(CASE WHEN sign_in IS NOT NULL AND sign_out IS NOT NULL 
                       THEN (julianday(date || ' ' || sign_out) - julianday(date || ' ' || sign_in)) * 24 
                       ELSE NULL END) as avg_hours
            FROM attendance WHERE emp_id=? AND sign_in IS NOT NULL
        """,
            (emp_id,),
        )

        result = cursor.fetchone()
        if result and result[0] > 0:
            total, on_time, avg_hours = result
            punctuality = (on_time / total * 100) if total > 0 else 0
            avg_hours = avg_hours or 0

            # Create performance metrics layout
            metrics_frame = tk.Frame(content_frame, bg=theme["card"])
            metrics_frame.pack(fill="x")
            metrics_frame.grid_columnconfigure(0, weight=1)
            metrics_frame.grid_columnconfigure(1, weight=1)

            # Punctuality
            punct_frame = tk.Frame(metrics_frame, bg=theme["card"])
            punct_frame.grid(row=0, column=0, sticky="w", padx=(0, 20))
            tk.Label(
                punct_frame, text="Punctuality:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                punct_frame,
                text=f"{punctuality:.1f}%",
                font=("Arial", 18, "bold"),
                bg=theme["card"],
                fg=theme["success"] if punctuality >= 90 else theme["warning"],
            ).pack(anchor="w")

            # Average hours
            hours_frame = tk.Frame(metrics_frame, bg=theme["card"])
            hours_frame.grid(row=0, column=1, sticky="w")
            tk.Label(
                hours_frame, text="Avg Hours/Day:", bg=theme["card"], fg=theme["fg"]
            ).pack(anchor="w")
            tk.Label(
                hours_frame,
                text=f"{avg_hours:.1f}h",
                font=("Arial", 18, "bold"),
                bg=theme["card"],
                fg=theme["button"],
            ).pack(anchor="w")

        else:
            tk.Label(
                content_frame,
                text="No performance data available yet",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(
            content_frame,
            text=f"Error loading performance: {e}",
            bg=theme["card"],
            fg="red",
        ).pack()


def create_recent_activity_card(parent, row, col, emp_id, cursor):
    """Create recent activity card"""
    card_frame = RoundedFrame(parent, bg_color=theme["card"])
    card_frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

    content_frame = card_frame.inner_frame

    tk.Label(
        content_frame,
        text="📋 Recent Activity",
        font=TITLE_FONT,
        bg=theme["card"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 10))

    try:
        cursor.execute(
            "SELECT date, sign_in FROM attendance WHERE emp_id=? ORDER BY date DESC LIMIT 5",
            (emp_id,),
        )
        results = cursor.fetchall()

        if results:
            for date, sign_in in results:
                activity_frame = tk.Frame(content_frame, bg=theme["card"])
                activity_frame.pack(fill="x", pady=2)

                tk.Label(
                    activity_frame,
                    text=date,
                    bg=theme["card"],
                    fg=theme["fg"],
                    font=("Arial", 9),
                    width=12,
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    activity_frame,
                    text=sign_in or "No sign-in",
                    bg=theme["card"],
                    fg=theme["fg"],
                    font=("Arial", 9),
                ).pack(side="left", padx=(10, 0))
        else:
            tk.Label(
                content_frame,
                text="No recent activity",
                bg=theme["card"],
                fg=theme["fg"],
            ).pack()

    except Exception as e:
        tk.Label(
            content_frame,
            text=f"Error loading activity: {e}",
            bg=theme["card"],
            fg="red",
        ).pack()


def refresh_main_dashboard(frame, emp_id, cursor):
    """Refresh the main dashboard content"""
    try:
        show_main_dashboard_content(frame, emp_id, cursor)
    except Exception as e:
        print(f"Dashboard refresh error: {e}")


def sign_in_fixed(emp_id, name, cursor, conn, content_frame):
    """Fixed sign-in function with better error handling"""
    try:
        now = datetime.now()
        date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

        # Check if already signed in
        cursor.execute(
            "SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, date)
        )
        if cursor.fetchone():
            messagebox.showinfo("INFO", "Already signed in today!")
            return

        # Sign in
        cursor.execute(
            "INSERT INTO attendance (emp_id, name, date, sign_in) VALUES (?, ?, ?, ?)",
            (emp_id, name, date, time),
        )
        conn.commit()
        messagebox.showinfo("SUCCESS", f"Signed in at {time}")

        # Refresh dashboard
        if content_frame:
            refresh_main_dashboard(content_frame, emp_id, cursor)

    except Exception as e:
        messagebox.showerror("Error", f"Sign-in failed: {e}")


def sign_out_fixed(emp_id, cursor, conn, content_frame):
    """Fixed sign-out function with better error handling"""
    try:
        now = datetime.now()
        date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

        # Check if signed in today
        cursor.execute(
            "SELECT sign_in FROM attendance WHERE emp_id=? AND date=?", (emp_id, date)
        )
        record = cursor.fetchone()

        if not record or not record[0]:
            messagebox.showwarning("ALERT", "You haven't signed in today!")
            return

        # Sign out
        cursor.execute(
            "UPDATE attendance SET sign_out=? WHERE emp_id=? AND date=?",
            (time, emp_id, date),
        )
        conn.commit()
        messagebox.showinfo("SUCCESS", f"Signed out at {time}")

        # Refresh dashboard
        if content_frame:
            refresh_main_dashboard(content_frame, emp_id, cursor)

    except Exception as e:
        messagebox.showerror("Error", f"Sign-out failed: {e}")
