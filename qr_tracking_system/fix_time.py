import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace datetime.now() with get_caracas_time() 
# but ignoring the def get_caracas_time() itself
def replacer(match):
    full_line = match.group(0)
    if 'def get_caracas_time' in full_line or 'return datetime.now' in full_line:
         return full_line
    return full_line.replace('datetime.now()', 'get_caracas_time()')

# Apply replacement line by line to be safe
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'datetime.now()' in line and 'def get_caracas_time' not in line and 'return datetime.now(ZoneInfo' not in line:
        lines[i] = line.replace('datetime.now()', 'get_caracas_time()')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Replacement complete.")
