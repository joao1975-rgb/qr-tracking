import re

with open('templates/admin_campaigns.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if '<div id="campaignModal"' in line:
        start_idx = i
        break

if start_idx != -1:
    open_divs = 0
    end_idx = -1
    for i in range(start_idx, len(lines)):
        open_divs += lines[i].count('<div') - lines[i].count('</div')
        if open_divs == 0:
            end_idx = i
            break
            
    print(f"Modal is from line {start_idx + 1} to {end_idx + 1}")
    
    # We replace from start_idx to end_idx + 1
    new_lines = lines[:start_idx]
    
    with open('fix_modal.py', 'r', encoding='utf-8') as f:
        code = f.read()
        import ast
        for node in ast.walk(ast.parse(code)):
            if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'NEW_MODAL':
                new_modal = node.value.value
                break
    
    new_lines.append(new_modal + '\n')
    new_lines.extend(lines[end_idx + 1:])
    
    with open('templates/admin_campaigns.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Done!")
