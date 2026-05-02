with open('templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's count divs from <div id="tab-overview"...> down to <!-- MASTER ...>
start_idx = content.find('<div id="tab-overview"')
master_idx = content.find('<!-- MASTER DATA FLOW')

if start_idx != -1 and master_idx != -1:
    sub_content = content[start_idx:master_idx]
    opens = sub_content.count('<div')
    closes = sub_content.count('</div')
    print(f"Between tab-overview and MASTER DATA FLOW: Opens={opens}, Closes={closes}")

comp_idx = content.find('<div id="tab-compare"')
if master_idx != -1 and comp_idx != -1:
    sub_content2 = content[master_idx:comp_idx]
    opens = sub_content2.count('<div')
    closes = sub_content2.count('</div')
    print(f"Between MASTER DATA FLOW and tab-compare: Opens={opens}, Closes={closes}")
