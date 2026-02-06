def find_error():
    file_path = r'd:\dev\Transcribe\backend\debug_logs.txt'
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    lines = content.splitlines()
    found = False
    for i, line in enumerate(lines):
        if "DEBUG TRANSCRIPT" in line:
            print(f"FOUND at line {i+1}:")
            for j in range(i, min(i+20, len(lines))):
                 print(f"{j+1}: {lines[j].strip()}")
            return 
            
    if not found:
        print("Error pattern not found in file.")

find_error()
