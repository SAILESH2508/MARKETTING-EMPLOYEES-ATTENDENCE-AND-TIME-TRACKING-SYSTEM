# Marketing Employee Time & Attendance System

A Face Recognition-based time and attendance tracking system built with Python, Tkinter, and SQLite.

## Features
- **Face Recognition Login**: Fast and secure clock-in/out using facial biometrics.
- **Admin Dashboard**: Manage employees, view attendance records, and handle salaries.
- **Anti-Spoofing**: Basic liveness checks (optional config).
- **SQLite Database**: Lightweight local data storage.

## Prerequisites
- **Python 3.11** (Recommended)
- **CMake** (Required for compiling `dlib`)
    - *Windows*: Install via Visual Studio Build Tools or [CMake website](https://cmake.org/download/).
    - *Linux/Mac*: `sudo apt-get install cmake` or `brew install cmake`.

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "MARKETTING EMPLOYEES ATTENDENCE AND TIME TRACKING SYSTEM"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If `dlib` fails to install, ensure CMake is in your system PATH.*

3. **Verify Environment**
   Run the check script to ensure all libraries are correctly installed:
   ```bash
   python check_env.py
   ```

## Usage

### 1. Employee Interface
Launch the main application for clocking in/out:
```bash
python emp.py
```
- Click **Employee Login** to verify your face and mark attendance.
- Click **Register New Employee** (requires admin password) to add new faces.

### 2. Admin Dashboard
Launch the dashboard to manage the system:
```bash
python admin_dashboard.py
```
- **Login**: (Default credentials: `admin` / `admin123`)
- **Features**:
    - View/Edit employee details.
    - Check daily attendance logs.
    - Calculate and manage salaries.

## Troubleshooting
- **`dlib` install error**: Make sure you have the C++ build tools installed (Visual Studio Community -> Desktop development with C++).
- **Camera not found**: Ensure your webcam is connected and not used by another app.
