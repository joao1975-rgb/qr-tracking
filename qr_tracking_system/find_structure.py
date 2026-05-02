lines = open('templates/dashboard_antigravity_v28.html', encoding='utf-8').readlines()
for i, line in enumerate(lines):
    if '<body' in line or '</style' in line or '<div class="shell"' in line or 'class="main"' in line or 'class="sidebar"' in line or 'class="topbar"' in line or 'Dash Grid' in line or '<!-- MAIN DASHBOARD CONTENT -->' in line.upper():
        print(f"{i+1}: {line.strip()[:150]}")
