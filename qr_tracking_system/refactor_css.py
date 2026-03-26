import re
import os

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract styles
styles = re.findall(r'<style>(.*?)</style>', html, re.DOTALL)
css_content = "\n".join(styles)

# Create static dirs
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

with open('static/css/dashboard_premium.css', 'w', encoding='utf-8') as f:
    f.write(css_content)

# Replace <style> blocks with <link>
html_clean_css = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="/static/css/dashboard_premium.css">', html, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_clean_css)

print("Decoupled CSS successfully.")
