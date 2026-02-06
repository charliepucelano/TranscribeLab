import os

file_path = r'd:\dev\Transcribe\backend\debug_logs.txt'
try:
    # Try utf-8 with replacement
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        print("".join(lines[-50:]))
except Exception as e:
    print(f"Error reading file: {e}")
