import re

with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

# We need to find the erroneous block that starts with:
# # ─────────────────────────────────────────────────────────────
# # SECCIÓN 5: ENDPOINTS NUEVOS (agregar al router de app.py)
# and ends right before:
# class ScanCreate(BaseModel):

start_bad = app_code.find('# SECCIÓN 5: ENDPOINTS NUEVOS (agregar')
end_bad = app_code.find('class ScanCreate(BaseModel):')

if start_bad != -1 and end_bad != -1 and start_bad < end_bad:
    # We should delete from start_bad backwards a bit to remove the hr line too
    true_start = app_code.rfind('# ──', 0, start_bad)
    if true_start == -1: true_start = start_bad
    
    app_code = app_code[:true_start] + '\\n\\n' + app_code[end_bad:]
    
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_code)
    print("Excised broken endpoints successfully.")
else:
    print("Could not find boundaries to excise.")
