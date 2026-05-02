import subprocess
import re

with open('templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
for i, script in enumerate(scripts):
    with open(f'temp{i}.js', 'w', encoding='utf-8') as f:
        f.write(script)
    try:
        subprocess.run(['node', '-c', f'temp{i}.js'], check=True, capture_output=True, text=True)
        print(f"Script {i} OK")
    except subprocess.CalledProcessError as e:
        print(f"Script {i} ERROR: {e.stderr}")
