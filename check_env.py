import sys
import shutil
import os

print(f"Python Executable: {sys.executable}")
print(f"Path: {os.environ.get('PATH')}")

try:
    import cv2
    print("cv2 imported successfully")
except ImportError as e:
    print(f"cv2 import failed: {e}")

cmake_path = shutil.which("cmake")
print(f"CMake path: {cmake_path}")

try:
    import face_recognition
    print("face_recognition imported successfully")
except ImportError as e:
    print(f"face_recognition import failed: {e}")
