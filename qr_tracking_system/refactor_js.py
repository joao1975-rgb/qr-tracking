import re
import os

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract script logic that isn't Chart.js library imports
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
js_content = "\n".join(scripts)

if js_content.strip():
    os.makedirs('static/js', exist_ok=True)
    with open('static/js/dashboard_logic.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    # Replace scripts with link
    html_clean_js = re.sub(r'<script>.*?</script>', '<script src="/static/js/dashboard_logic.js"></script>', html, flags=re.DOTALL)
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_clean_js)
    
    print("Decoupled JS successfully.")
else:
    print("No inline JS found.")
