import upstox_helper
import os
import sys

print("--- Python Path Investigation ---")
print(f"Python Executable: {sys.executable}")
print(f"Current Directory: {os.getcwd()}")
print(f"upstox_helper location: {os.path.abspath(upstox_helper.__file__)}")

try:
    with open(os.path.abspath(upstox_helper.__file__), 'r') as f:
        content = f.read()
        if "unix" in content.lower():
            print("CHECK: The file HAS the new 'unix' fix code.")
        else:
            print("CHECK: The file is still the OLD version (no 'unix' found).")
except Exception as e:
    print(f"Error reading file: {e}")
