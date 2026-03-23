import re
with open('app.py', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('@app.') or line.strip().startswith('def get_dashboard_stats'):
            print(line.strip())
