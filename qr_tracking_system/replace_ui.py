import os

html_path = 'templates/admin_campaigns.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

v280_path = 'admin_campaigns_form_v280.html'
with open(v280_path, 'r', encoding='utf-8') as f:
    v280 = f.read()

# Extract modal block from v280 (from <div id="campaignModal" to the closing </div> before <script>)
script_idx = v280.find('<script>')
modal_v280 = v280[:script_idx]
# remove the instruction comment at the top
modal_v280 = modal_v280[modal_v280.find('<!-- ── Modal de Nueva Campaña'):]

# Extract script block from v280
script_v280 = v280[script_idx + len('<script>'):v280.find('</script>')].strip()

# In original HTML, find where the old modal is
start_modal = content.find('<!-- Modal Crear/Editar Campaña -->')
end_modal = content.find('<!-- Modal Copiar URL -->')
if start_modal != -1 and end_modal != -1:
    content = content[:start_modal] + modal_v280 + '\n    ' + content[end_modal:]

# Replace old JS functions
start_js = content.find('// MODAL CREAR/EDITAR')
end_js = content.find('// GENERAR QR')
if start_js != -1 and end_js != -1:
    content = content[:start_js] + '// MODAL CREAR/EDITAR v2.8\n' + script_v280 + '\n\n        ' + content[end_js:]

# Replace button onclick
content = content.replace('openCreateModal()', 'openNewCampaignModal()')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML replacement successful!")
