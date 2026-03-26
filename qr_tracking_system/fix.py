with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fix = '''                <p>Sistema de tracking avanzado para códigos QR</p>
                
                <div class="nav-grid">
                    <a href="/dashboard" class="nav-link">📊 Dashboard</a>
                    <a href="/reports" class="nav-link">📈 Reportes</a>
                    <a href="/admin/campaigns" class="nav-link">🎯 Campañas</a>
'''

# Delete lines 886 to 892 (indices 885 to 891 inclusive)
del lines[885:892]

# Insert the fix at index 885
lines.insert(885, fix)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
