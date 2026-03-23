import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith("def init_database():") and "def init_database():" in lines[i]:
        skip = True
        
    if skip and line.startswith("# ================================"):
        # We reached the next block (Utility functions)
        # Check if the preceding line was the end of get_db_connection
        if "return conn" in lines[i-2] or "return conn" in lines[i-3]:
            skip = False
            
    if not skip:
        # Patch the imports
        if line.strip() == "import database" and lines[i+1].strip().startswith("from config"):
            new_lines.append(line)
            new_lines.append("    from database import get_db_connection, init_database\n")
        else:
            new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(" app.py successfully patched!")
