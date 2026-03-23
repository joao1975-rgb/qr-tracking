import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace strftime('%H', scan_timestamp)
content = content.replace("strftime('%H', scan_timestamp)", "EXTRACT(HOUR FROM scan_timestamp)")
content = content.replace("strftime('%Y-%m-%d', scan_timestamp)", "DATE(scan_timestamp)")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
