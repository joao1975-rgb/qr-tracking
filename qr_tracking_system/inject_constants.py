import sys

with open("app.py", "r", encoding="utf-8") as f:
    c = f.read()

with open("app_additions_v280_1.py", "r", encoding="utf-8") as f:
    adds = f.read()

t_start = adds.find('# SECCIÓN 1: CONSTANTES Y TAXONOMÍAS')
t_end = adds.find('# SECCIÓN 2: MODELO PYDANTIC ACTUALIZADO')
tax = adds[t_start:t_end].strip()

base_idx = c.find('import base64')
idx = c.find('\\n', base_idx) + 1
c = c[:idx] + '\\n\\n' + tax + '\\n\\n' + c[idx:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Injected taxonomies successfully.")
