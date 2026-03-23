import re

with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix floats erroneously string-replaced by device_pixel_ratio and cpu_cores
c = re.sub(r':\s*device_pixel_ratio', ': 1.0', c)
c = re.sub(r':\s*cpu_cores', ': 1.0', c)

# Fix any stray standalone overrides in dictionary values
c = c.replace('"scan_rate": device_pixel_ratio', '"scan_rate": 1.0')
c = c.replace('"scan_rate": cpu_cores', '"scan_rate": 1.0')
c = c.replace('"bench_weight": device_pixel_ratio', '"bench_weight": 1.0')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("App syntactic floats recompiled!")
