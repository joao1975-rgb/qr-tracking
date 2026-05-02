import re

with open('templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'<script>(.*?)</script>', text, re.DOTALL)
if match:
    with open('temp.js', 'w', encoding='utf-8') as f:
        f.write(match.group(1))
    print("Saved script to temp.js")
else:
    print("Script not found")
