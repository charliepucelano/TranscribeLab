file_path = r'd:\dev\Transcribe\backend\debug_logs.txt'
output_path = r'd:\dev\Transcribe\backend\extracted.txt'

try:
    with open(file_path, 'r', encoding='utf-16', errors='replace') as f:
        lines = f.readlines()
    
    found = False
    with open(output_path, 'w', encoding='utf-8') as out:
        for i, line in enumerate(lines):
            if "DEBUG TRANSCRIPT" in line:
                out.write(f"FOUND at line {i+1}:\n")
                for j in range(i, min(i+20, len(lines))):
                    out.write(f"{j+1}: {lines[j]}") # lines[j] has newline
                found = True
                
    if not found:
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write("Error pattern not found in file.")
    else:
        print("Extraction complete.")

except Exception as e:
    print(f"Error: {e}")
