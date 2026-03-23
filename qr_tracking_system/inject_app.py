import os

with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

with open('app_additions_v280_1.py', 'r', encoding='utf-8') as f:
    additions = f.read()

# EXTRACT FROM app_additions_v280_1.py
# 1. Constants (lines 22-135 usually)
# We can find "# SECCIÓN 1: CONSTANTES Y TAXONOMÍAS"
section1_start = additions.find('# SECCIÓN 1: CONSTANTES Y TAXONOMÍAS')
section1_end = additions.find('# SECCIÓN 2: MODELO PYDANTIC ACTUALIZADO')

# 2. Pydantic Model (CampaignCreate)
section2_start = additions.find('class CampaignCreate(BaseModel):')
section2_end = additions.find('# SECCIÓN 3: FUNCIONES DE AYUDA (Helpers)')
campaign_create_code = additions[section2_start:section2_end].strip()

# Create a companion CampaignUpdate
campaign_update_code = campaign_create_code.replace('CampaignCreate', 'CampaignUpdate')
campaign_update_code = campaign_update_code.replace('campaign_code: str', '')
campaign_update_code = campaign_update_code.replace(': str', ': Optional[str] = None')
campaign_update_code = campaign_update_code.replace(': int', ': Optional[int] = None')
campaign_update_code = campaign_update_code.replace(': float', ': Optional[float] = None')
campaign_update_code = campaign_update_code.replace(': bool', ': Optional[bool] = None')
# fix double optionals just in case
campaign_update_code = campaign_update_code.replace('Optional[Optional[', 'Optional[')

# 3. Helpers + API endpoints
section3_start = additions.find('def generate_benchmark_group')

# MODIFY app.py
# Replace CampaignCreate block
old_create_start = app_code.find('class CampaignCreate(BaseModel):')
old_create_end = app_code.find('class DeviceCreate(BaseModel):')
app_code = app_code[:old_create_start] + campaign_create_code + '\n\n' + campaign_update_code + '\n\n' + app_code[old_create_end:]

# Inject constants and functions
config_marker = app_code.find('# ================================\n# CONFIGURACIÓN DE DIRECTORIOS') 
if config_marker != -1:
    app_code = app_code[:config_marker] + additions[section1_start:section1_end] + '\n\n' + app_code[config_marker:]

app_code = app_code + '\n\n' + additions[section3_start:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Backend injection completed.")
