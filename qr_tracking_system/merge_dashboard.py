import os

phygital_path = "templates/phygital_dashboard.html"
target_path = "templates/dashboard_antigravity_v28.html"

with open(phygital_path, "r", encoding="utf-8") as f:
    phygital_lines = f.readlines()

new_css = phygital_lines[2:78] # Lines 3-78
new_html = ['<div class="dash-wrap" style="width: 100%; font-family: var(--sans);">\n'] + phygital_lines[98:339] + ['</div>\n']
new_js = phygital_lines[342:386] # Lines 343-386

with open(target_path, "r", encoding="utf-8") as f:
    target_lines = f.readlines()

css_insert = target_lines.index("</style>\n")
html_start = -1
html_end = -1
js_insert = -1

for i, line in enumerate(target_lines):
    if '<main class="main">' in line:
        html_start = i
    if '</main>' in line:
        html_end = i
    if '</body>' in line:
        js_insert = i

final_lines = (
    target_lines[:css_insert] + 
    new_css + 
    target_lines[css_insert:html_start+1] + 
    ['<div id="tab-overview" class="tab-content active" style="padding-top:10px;">\n'] + 
    new_html + 
    ['</div>\n'] + 
    target_lines[html_end:js_insert] + 
    new_js + 
    target_lines[js_insert:]
)

with open(target_path, "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("Dashboard successfully merged!")
