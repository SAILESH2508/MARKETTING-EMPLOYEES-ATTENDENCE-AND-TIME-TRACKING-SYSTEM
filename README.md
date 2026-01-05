# 🎯 Employee Attendance & Time Tracking System

A comprehensive employee management system with facial recognition, attendance tracking, salary management, and ML-powered analytics.

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Detailed Setup Guide](#-detailed-setup-guide)
- [Usage Guide](#-usage-guide)
- [Modules Overview](#-modules-overview)
- [Detailed Module Architecture](#-detailed-module-architecture)
- [Database Schema](#-database-schema)
- [ML Features](#-ml-features)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing-to-employee-attendance-system)
- [Changelog](#-changelog)
- [License](#-license)

## ✨ Features

### 🔐 Authentication & Security
- **Facial Recognition Login** - Secure employee authentication using face recognition
- **Lockout Protection** - Automatic lockout after failed attempts
- **Admin Dashboard** - Separate admin interface for management

### ⏰ Attendance Management
- **Real-time Sign In/Out** - Track employee attendance with timestamps
- **Attendance Heatmap** - Visual calendar view of attendance patterns
- **Punctuality Leaderboard** - Gamified on-time performance tracking
- **Face Login History** - Complete audit trail of all logins

### 💰 Salary Management
- **Salary Tracking** - Manage base salary, bonuses, and deductions
- **Interactive Charts** - Pie charts and bar graphs for salary visualization
- **Salary Predictions** - ML-powered salary forecasting
- **CSV Export** - Export salary data for external processing

### 📊 Analytics & Insights
- **Productivity Score** - Comprehensive employee productivity metrics
- **Performance Trends** - Track performance over time
- **Work Patterns Analysis** - Identify work habits and patterns
- **ML Predictions** - Punctuality and performance predictions

### 🤖 Machine Learning
- **Punctuality Predictor** - Predict if employee will be on-time
- **Anomaly Detection** - Identify unusual attendance patterns
- **Salary Estimator** - Predict salary based on performance
- **Auto-training** - Models train automatically on startup

### 🎨 User Interface
- **Modern Dark/Light Themes** - Toggle between themes
- **Responsive Design** - Adapts to different screen sizes
- **Interactive Charts** - Matplotlib-powered visualizations
- **Smooth Animations** - Fade-in effects and transitions

## 📸 Screenshots

### Login Screen
![Login Screen](screenshots/login_screen.png)

### Employee Dashboard
![Employee Dashboard](screenshots/employee_dashboard.png)

### Admin Dashboard
![Admin Dashboard](screenshots/admin_dashboard.png)

### Salary Management
![Salary Management](screenshots/salary_management.png)


## 💻 System Requirements

### Required
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Webcam**: For facial recognition (optional for admin)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 500MB free space

### Python Packages
```
tkinter (usually included with Python)
opencv-python
face-recognition
numpy
pandas
scikit-learn
matplotlib
Pillow
sqlite3 (included with Python)
```

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd employee-attendance-system
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python test_imports.py
```

You should see:
```
✅ All imports successful!
✅ Ready to run!
```

## 🎬 Quick Start

### Option 1: Face Recognition Login
```bash
python emp.py
```
- Look at the webcam for facial recognition
- System will automatically log you in

### Option 2: Admin Dashboard
```bash
python admin_dashboard.py
```
- Access admin features
- Manage employees and view reports

### Option 3: Salary Management
```bash
python manage_salaries.py
```
- Manage employee salaries
- View salary charts and analytics

### Option 4: Register New Employee
```bash
python register_face.py
```
- Register new employee faces
- Add employee to the system

## 📁 Project Structure

```
employee-attendance-system/
│
├── 📱 Main Applications
│   ├── emp.py                      # Face recognition login
│   ├── admin_dashboard.py          # Admin interface
│   ├── manage_salaries.py          # Salary management
│   ├── register_face.py            # Employee registration
│   └── employee_dashboard.py       # Employee dashboard (main entry)
│
├── 📦 Dashboard Modules (Modular Architecture)
│   ├── dashboard_modules/
│   │   ├── ui_helpers.py           # UI components
│   │   ├── ml_functions.py         # ML models
│   │   ├── chart_functions.py      # Charts
│   │   ├── summary_functions.py    # Dashboard cards
│   │   ├── analytics_functions.py  # Analytics
│   │   ├── main_dashboard.py       # Main window
│   │   ├── action_functions.py     # Actions
│   │   └── app_setup.py            # Setup
│
├── 💾 Data & Models
│   ├── attendance_system.db        # SQLite database
│   ├── employee_faces/             # Employee face images
│   ├── models/                     # Trained ML models
│   │   ├── punctuality.pkl
│   │   ├── salary_reg.pkl
│   │   └── anomaly.pkl
│   └── charts/                     # Generated charts
│
├── 📚 Documentation
│   ├── README.md                   # Comprehensive documentation (Merged)
│
├── ⚙️ Configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .gitignore                  # Git ignore rules
│   └── start.bat                   # Windows startup script
```

## 📖 Usage Guide

### For Employees

#### 1. Sign In
1. Run `python emp.py`
2. Look at the webcam
3. System recognizes your face and logs you in
4. Dashboard opens automatically

#### 2. View Dashboard
- **Summary Cards**: See your salary, predictions, and scores
- **Productivity Score**: View detailed performance metrics
- **Quick Stats**: Today's status and weekly summary
- **Charts**: Attendance heatmap, performance trends

#### 3. Sign Out
- Click "❌ Sign Out" button in the dashboard
- Or close the dashboard window

### For Administrators

#### 1. Access Admin Dashboard
```bash
python admin_dashboard.py
```

#### 2. Manage Employees
- Add new employees
- View all employee records
- Edit employee information
- Delete employees

#### 3. View Reports
- Attendance reports
- Salary summaries
- Performance analytics
- Export data to CSV

#### 4. Manage Salaries
```bash
python manage_salaries.py
```
- Set base salaries
- Add bonuses
- Apply deductions
- View salary charts

### For System Setup

#### 1. Register New Employee
```bash
python register_face.py
```
- Enter employee ID and name
- Capture face images
- System trains recognition model

#### 2. Database Management
- Database: `attendance_system.db`
- Backup regularly
- Use SQLite browser for direct access

## 🔧 Modules Overview

### 1. UI Helpers (`ui_helpers.py`)
**Purpose**: Core UI components and utilities

**Key Functions**:
- `ToolTip` - Hover tooltips
- `CustomButton` - Styled buttons
- `rounded_card()` - Card UI elements
- `create_scrollable_frame()` - Scrollable containers
- `fade_in()` - Smooth animations
- `get_db_data_safely()` - Thread-safe DB access

### 2. ML Functions (`ml_functions.py`)
**Purpose**: Machine learning models and predictions

**Key Functions**:
- `train_punctuality_model()` - Train punctuality predictor
- `predict_punctuality_for_emp()` - Predict on-time probability
- `train_anomaly_detector()` - Train anomaly detection
- `run_anomaly_scan()` - Detect unusual patterns
- `train_salary_predictor()` - Train salary estimator
- `predict_salary()` - Estimate salary

### 3. Chart Functions (`chart_functions.py`)
**Purpose**: Data visualization and charts

**Key Functions**:
- `show_heatmap()` - Attendance calendar heatmap
- `show_leaderboard()` - Punctuality rankings
- `show_salary_pie()` - Salary breakdown chart
- `show_attendance_bar()` - On-time vs late chart
- `show_face_log()` - Login history table

### 4. Summary Functions (`summary_functions.py`)
**Purpose**: Dashboard summary cards and displays

**Key Functions**:
- `show_default_summary()` - Main dashboard view
- `get_predicted_salary_value()` - Get salary prediction
- `get_punctuality_probability()` - Get punctuality score
- `compute_perfection_score()` - Calculate performance
- `refresh_summary()` - Update dashboard

### 5. Analytics Functions (`analytics_functions.py`)
**Purpose**: Performance analytics and trends

**Key Functions**:
- `show_performance_trends()` - Performance over time
- `show_work_patterns()` - Work habit analysis
- `show_productivity_score()` - Comprehensive metrics
- `auto_train_ml_models()` - Background model training

### 6. Action Functions (`action_functions.py`)
**Purpose**: User actions and operations

**Key Functions**:
- `sign_in()` - Employee sign-in
- `sign_out()` - Employee sign-out
- `auto_reminder()` - Automatic reminders
- `export_attendance_csv()` - Export data

### 7. Main Dashboard (`main_dashboard.py`)
**Purpose**: Main dashboard window and layout

**Key Functions**:
- `employee_dashboard()` - Create main window
- Tab management
- Theme toggling
- Navigation

### 8. App Setup (`app_setup.py`)
**Purpose**: Application initialization

**Key Functions**:
- `setup_database_and_start_app()` - Initialize app
- Employee selection
- First-time setup

## 🗄️ Database Schema

### Tables

#### 1. `employees`
```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    department TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `attendance`
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id TEXT NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    sign_in TEXT,
    sign_out TEXT,
    FOREIGN KEY (emp_id) REFERENCES employees(id)
);
```

#### 3. `salary`
```sql
CREATE TABLE salary (
    emp_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    salary REAL,
    bonus REAL,
    deductions REAL,
    net_salary REAL,
    FOREIGN KEY (emp_id) REFERENCES employees(id)
);
```

#### 4. `lockout_status`
```sql
CREATE TABLE lockout_status (
    id TEXT PRIMARY KEY,
    locked_until TEXT
);
```

## 🤖 ML Features

### 1. Punctuality Prediction
**Algorithm**: Logistic Regression with Calibration
**Features**: Day of week, historical average sign-in time
**Output**: Probability of being on-time (0-100%)

**Usage**:
```python
from dashboard_modules.ml_functions import predict_punctuality_for_emp
predict_punctuality_for_emp(emp_id, cursor)
```

### 2. Anomaly Detection
**Algorithm**: Isolation Forest
**Features**: Sign-in times
**Output**: Anomalous attendance records

**Usage**:
```python
from dashboard_modules.ml_functions import run_anomaly_scan
run_anomaly_scan(cursor, frame)
```

### 3. Salary Prediction
**Algorithm**: Linear Regression
**Features**: Bonus, deductions
**Output**: Predicted base salary

**Usage**:
```python
from dashboard_modules.ml_functions import predict_salary
predict_salary(emp_id, cursor)
```

### Model Training
Models train automatically on dashboard startup. Manual training:
```python
from dashboard_modules.ml_functions import train_punctuality_model
train_punctuality_model(cursor, silent=False)
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Face Recognition Not Working
**Problem**: Camera not detected or face not recognized

**Solutions**:
- Check webcam connection
- Ensure good lighting
- Re-register face: `python register_face.py`
- Update face_recognition library: `pip install --upgrade face-recognition`

#### 2. Import Errors
**Problem**: `ModuleNotFoundError` or `NameError`

**Solutions**:
- Verify installation: `python test_imports.py`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

#### 3. Database Errors
**Problem**: `sqlite3.OperationalError`

**Solutions**:
- Check database file exists: `attendance_system.db`
- Verify file permissions
- Backup and recreate database if corrupted

#### 4. ML Models Not Training
**Problem**: Models not found or training fails

**Solutions**:
- Install scikit-learn: `pip install scikit-learn pandas`
- Ensure sufficient data (minimum 10 attendance records)
- Check `models/` directory exists

#### 5. UI Not Displaying Correctly
**Problem**: Blank window or missing elements

**Solutions**:
- Update tkinter (usually comes with Python)
- Check theme settings
- Try toggling theme: Click "🌗 Toggle Mode"

### Performance Optimization

#### Speed Up Loading
- Reduce number of employees
- Archive old attendance records
- Optimize database queries

#### Reduce Memory Usage
- Close unused windows
- Clear matplotlib cache
- Limit chart data points

## 🤝 Contributing

We welcome contributions! Please see [Contributing Guidelines](#-contributing-to-employee-attendance-system) below.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Run diagnostics: `python test_imports.py`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature-name`
7. Create Pull Request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to functions
- Comment complex logic
- Keep functions focused and small

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **face_recognition** library by Adam Geitgey
- **OpenCV** for computer vision
- **scikit-learn** for machine learning
- **matplotlib** for visualizations
- **tkinter** for GUI framework

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

# 🛠️ Detailed Setup Guide

Complete installation guide for the Employee Attendance System.

## Table of Contents
- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS:** Windows 10/11, Ubuntu 20.04+, macOS 10.15+
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 500MB free space
- **Camera:** Webcam (built-in or USB)
- **Internet:** Required for initial setup

### Recommended Specifications
- **Python:** 3.10 or 3.11
- **RAM:** 8GB or more
- **Storage:** 1GB free space
- **Camera:** HD webcam (720p or higher)

---

## Windows Installation

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Install Visual C++ Build Tools (for dlib)

**Option A: Visual Studio Build Tools (Recommended)**
1. Download from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/)
2. Select "Build Tools for Visual Studio"
3. Install "Desktop development with C++"

**Option B: Use pre-built dlib**
```cmd
pip install dlib-binary
```

### Step 3: Clone Repository

```cmd
git clone https://github.com/yourusername/employee-attendance-system.git
cd employee-attendance-system
```

### Step 4: Create Virtual Environment

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Step 5: Install Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Run Application

```cmd
python emp.py
```

---

## Linux Installation

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y cmake build-essential
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y libboost-all-dev
```

### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/employee-attendance-system.git
cd employee-attendance-system
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Run Application

```bash
python3 emp.py
```

---

## macOS Installation

### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python and Dependencies

```bash
brew install python@3.11
brew install cmake
brew install opencv
```

### Step 3: Clone Repository

```bash
git clone https://github.com/yourusername/employee-attendance-system.git
cd employee-attendance-system
```

### Step 4: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Run Application

```bash
python3 emp.py
```

---

## First Time Setup

### 1. Create First Employee

1. Run application: `python emp.py`
2. Click "Register New Employee (Face)"
3. Enter Employee ID: `1`
4. Enter Name: `Admin User`
5. Click "Capture Face"

### 2. Add Employee to Database

The employee must be added to the database first:

**Option A: Use Admin Panel**
1. Click "Admin Login"
2. Username: `admin`, Password: `admin123`
3. Click "Manage Employees"
4. Add employee with ID, Name, Role

**Option B: Direct Database**
```python
import sqlite3
conn = sqlite3.connect("attendance_system.db")
cursor = conn.cursor()
cursor.execute("INSERT INTO employees (id, name, role) VALUES (1, 'Admin User', 'Manager')")
conn.commit()
conn.close()
```

### 3. Register Face

After adding to database:
1. Click "Register New Employee (Face)"
2. Enter same Employee ID
3. Capture face

### 4. Test Login

1. Click "Employee Login"
2. Look at camera
3. Should recognize and open dashboard

---

# 🤝 Contributing to Employee Attendance System

Thank you for considering contributing to this project! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, etc.)

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature already exists
- Provide clear use case
- Explain why it would be useful
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Ensure all features work
   - Test on different scenarios
   - Check for any warnings or errors

5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```
   Use prefixes:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for improvements
   - `Remove:` for deletions
   - `Docs:` for documentation

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Provide clear description
   - Reference related issues
   - Add screenshots if UI changes

## Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small
- Use type hints where appropriate

### Example:
```python
def calculate_productivity_score(attendance_data: dict) -> float:
    """
    Calculate employee productivity score.
    
    Args:
        attendance_data: Dictionary containing attendance records
        
    Returns:
        float: Productivity score between 0 and 100
    """
    # Implementation
    pass
```

### Comments
- Explain WHY, not WHAT
- Keep comments up-to-date
- Use clear, concise language

### Database
- Use parameterized queries (prevent SQL injection)
- Close connections properly
- Handle errors gracefully

## Development Setup

1. Clone your fork
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Make changes
5. Test thoroughly

## Testing

Before submitting PR:
- [ ] Test face recognition with multiple faces
- [ ] Test all CRUD operations
- [ ] Verify ML models train correctly
- [ ] Check all navigation buttons work
- [ ] Test on different screen sizes
- [ ] Ensure no console errors/warnings

---

# 📜 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-01

### Added
- 🎉 Initial release
- Face recognition login system
- Employee dashboard with ML insights
- Admin panel for employee management
- Salary management with interactive charts
- Automatic ML model training
- Productivity scoring system
- Performance trends analysis
- Work pattern analysis
- Anomaly detection
- Attendance heatmap
- Leaderboard with badges
- CSV export functionality
- Dark mode theme
- Comprehensive documentation

### Features
- **Authentication**
  - Biometric face recognition
  - Secure admin login with SHA-256 hashing
  - Employee registration system

- **Dashboard**
  - Real-time attendance tracking
  - ML-powered predictions
  - Interactive charts and graphs
  - Productivity metrics

- **Analytics**
  - Punctuality predictions
  - Salary predictions
  - Anomaly detection
  - Performance trends

- **Management**
  - Employee CRUD operations
  - Salary management
  - Attendance records
  - Export to CSV

### Technical
- Python 3.8+ support
- SQLite database
- Tkinter GUI
- OpenCV for camera handling
- scikit-learn for ML models
- matplotlib for visualizations

### Documentation
- Comprehensive README
- Detailed setup guide
- Contributing guidelines
- MIT License

---

## [Unreleased]

### Planned Features
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Mobile app
- [ ] Cloud sync
- [ ] Multi-language support
- [ ] Advanced reporting
- [ ] Role-based permissions
- [ ] Shift management
- [ ] Leave management
- [ ] Payroll integration

---

## Version History

### Version 1.0.0 (2024-12-01)
- Initial public release
- Core features implemented
- Documentation complete
- Ready for production use

---

## How to Update

```bash
git pull origin main
pip install -r requirements.txt --upgrade
python emp.py
```

---

# 🏗️ Detailed Module Architecture

The employee dashboard has been split into modular files for better organization and maintainability.

## File Structure

```
dashboard_modules/
├── __init__.py                 # Package initialization
├── ui_helpers.py              # UI components and helpers
├── ml_functions.py            # Machine learning models
├── chart_functions.py         # Chart and visualization functions
├── summary_functions.py       # Dashboard summary and cards
├── analytics_functions.py     # Performance analytics
├── main_dashboard.py          # Main dashboard window
├── action_functions.py        # Sign-in/out actions
└── app_setup.py               # Database setup and app start
```

## Benefits of Modular Structure

### ✅ Better Organization
- Each file has a clear, single responsibility
- Easy to find specific functionality
- Logical grouping of related functions

### ✅ Improved Maintainability
- Smaller files are easier to read and understand
- Changes are isolated to specific modules
- Reduced risk of breaking unrelated functionality

### ✅ Enhanced Collaboration
- Multiple developers can work on different modules simultaneously
- Clear module boundaries reduce merge conflicts

### ✅ Easier Testing
- Individual modules can be tested independently
- Mock dependencies more easily

### ✅ Reusability
- Modules can be imported independently
- Functions can be reused in other projects
