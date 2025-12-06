#!/bin/bash
# Quick start script for Linux/macOS

echo "========================================"
echo "Employee Attendance System"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo ""

# Install/update dependencies
echo "Checking dependencies..."
pip install -r requirements.txt --quiet
echo ""

# Run the application
echo "Starting application..."
echo ""
python3 emp.py

# Check for errors
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "An error occurred!"
    echo "========================================"
    read -p "Press Enter to exit..."
fi
