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

**Fedora:**
```bash
sudo dnf install python3 python3-pip
sudo dnf install cmake gcc gcc-c++
sudo dnf install opencv opencv-devel
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

## Troubleshooting

### Issue: dlib Installation Fails

**Windows:**
```cmd
pip install dlib-binary
```

**Linux/macOS:**
```bash
# Install cmake first
pip install cmake
pip install dlib
```

### Issue: OpenCV Import Error

```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

### Issue: Face Recognition Not Working

1. Check camera permissions
2. Ensure good lighting
3. Update drivers:
   ```bash
   pip install --upgrade face-recognition
   ```

### Issue: Tkinter Not Found

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
brew install python-tk
```

### Issue: Database Locked

```bash
# Close all instances of the application
# Delete database file (will be recreated)
rm attendance_system.db
```

### Issue: Module Not Found

```bash
# Ensure virtual environment is activated
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Issue: Camera Not Detected

1. Check camera is connected
2. Try different camera index:
   - Edit `emp.py` and `register_face.py`
   - Change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`

3. Test camera:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   print(cap.isOpened())  # Should print True
   cap.release()
   ```

### Issue: Permission Denied (Linux/macOS)

```bash
# Add user to video group
sudo usermod -a -G video $USER
# Logout and login again
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

## Performance Optimization

### For Faster Face Recognition

Edit `emp.py`:
```python
# Reduce max_retries for faster timeout
max_retries = 30  # Default is 60

# Use smaller face detection model
face_locations = face_recognition.face_locations(rgb_frame, model="hog")  # Faster than "cnn"
```

### For Lower Memory Usage

Edit `employee_dashboard.py`:
```python
# Reduce chart sizes
fig, ax = plt.subplots(figsize=(6, 4))  # Instead of (8, 6)
```

---

## Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run application
python emp.py
```

---

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove project folder
cd ..
rm -rf employee-attendance-system

# Or on Windows
rmdir /s employee-attendance-system
```

---

## Getting Help

- 📖 Check [README.md](README.md) for features
- 🐛 Report bugs in [Issues](https://github.com/yourusername/employee-attendance-system/issues)
- 💬 Ask questions in [Discussions](https://github.com/yourusername/employee-attendance-system/discussions)
- 📧 Email: your.email@example.com

---

**Need more help? Open an issue on GitHub!** 🚀
