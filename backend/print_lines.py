file_path = r'd:\dev\Transcribe\backend\debug_logs.txt'
try:
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        # grep said line 147. Python is 0-indexed. So index 146.
        start = 146
        end = start + 30
        for i in range(start, min(end, len(lines))):
            print(f"{i+1}: {lines[i].strip()}")
except Exception as e:
    print(f"Error: {e}")
