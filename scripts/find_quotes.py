import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    # Check if line contains SQL queries with double quoted literals
    if any(sql_word in line for sql_word in ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'WHERE', 'AND', 'OR']):
        if re.search(r'status\s*=\s*"[^"]+"', line) or re.search(r'status\s+IN\s*\([^)]*"[^"]*"[^)]*\)', line) or re.search(r'role\s*=\s*"[^"]+"', line):
            print(f"Line {idx+1}: {line.strip()}")
