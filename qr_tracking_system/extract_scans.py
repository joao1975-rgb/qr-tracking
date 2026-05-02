import re
import os

with open('templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for Scans detail table block
m_html = re.search(r'(<div class="card" id="scansCard".*?</table.*?>\s*</div>\s*</div>\s*</div>)', html, re.DOTALL)
if m_html:
    with open('scans_html.txt', 'w', encoding='utf-8') as out:
        out.write(m_html.group(1))
    print('HTML EXTRACTED')
else:
    print('HTML NOT FOUND')

# Look for updateScansTable function
m_js = re.search(r'(function updateScansTable.*?)^        }', html, re.DOTALL | re.MULTILINE)
if m_js:
    with open('scans_js.txt', 'w', encoding='utf-8') as out:
        out.write(m_js.group(1) + "        }")
    print('JS EXTRACTED')
else:
    print('JS NOT FOUND')

# Look for rendering body function
m_tbody = re.search(r'(function renderScansTableBody.*?)^        }', html, re.DOTALL | re.MULTILINE)
if m_tbody:
    with open('scans_tbody_js.txt', 'w', encoding='utf-8') as out:
        out.write(m_tbody.group(1) + "        }")
    print('RENDER BODY EXTRACTED')

# Look for format duration
m_dur = re.search(r'(function formatDuration.*?)^        }', html, re.DOTALL | re.MULTILINE)
if m_dur:
    with open('scans_dur_js.txt', 'w', encoding='utf-8') as out:
        out.write(m_dur.group(1) + "        }")
    print('DUR EXTRACTED')
