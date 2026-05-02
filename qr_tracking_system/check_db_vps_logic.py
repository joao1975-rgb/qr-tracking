import paramiko
code = '''
from database import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    
    # 1. Total Escaneos
    cur.execute("SELECT COUNT(*) FROM scans")
    total_scans = cur.fetchone()[0]
    
    # 2. Escaneos Exitosos
    cur.execute("SELECT COUNT(*) FROM scans WHERE redirect_completed = true")
    success_scans = cur.fetchone()[0]
    
    # 3. Escaneos Fallidos
    cur.execute("SELECT COUNT(*) FROM scans WHERE redirect_completed = false")
    failed_scans = cur.fetchone()[0]
    
    # 4. Escaneos exitosos, dispositivos con un solo escaneo
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT ip_address FROM scans 
            WHERE redirect_completed = true 
            GROUP BY ip_address 
            HAVING count(*) = 1
        ) as t
    """)
    single_success = cur.fetchone()[0]
    
    # 5. Escaneo exitoso, dispositivos con mas de un escaneo
    cur.execute("""
        SELECT SUM(cnt) FROM (
            SELECT COUNT(*) as cnt FROM scans 
            WHERE redirect_completed = true 
            GROUP BY ip_address 
            HAVING count(*) > 1
        ) as t
    """)
    res = cur.fetchone()[0]
    multi_success = res if res else 0
    
    # 6. Cantidad de dispositivos unicos con escaneos exitosos
    cur.execute("SELECT COUNT(DISTINCT ip_address) FROM scans WHERE redirect_completed = true")
    unique_success_dev = cur.fetchone()[0]
    
    # 7. Cantidad de dispositivos unicos con escaneos no exitosos
    cur.execute("SELECT COUNT(DISTINCT ip_address) FROM scans WHERE redirect_completed = false")
    unique_failed_dev = cur.fetchone()[0]

    out = {
        "Total Escaneos": total_scans,
        "Escaneos Exitosos": success_scans,
        "Escaneos Fallidos": failed_scans,
        "Exitosos - Dispositivos con 1 escaneo": single_success,
        "Exitosos - Escaneos de Dispositivos Multi": multi_success,
        "Dispositivos unicos (Exitosos)": unique_success_dev,
        "Dispositivos unicos (Fallidos)": unique_failed_dev
    }
    
    for k, v in out.items():
        print(f"{k}: {v}")
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
stdin, stdout, stderr = client.exec_command('docker ps -q -f name=project_qr-tracking.1 | head -n 1')
cid = stdout.read().decode().strip().split('\n')[0]

sftp = client.open_sftp()
with sftp.file('/tmp/check_logic.py', 'w') as f:
    f.write(code)
sftp.close()

stdin, stdout, stderr = client.exec_command(f'docker cp /tmp/check_logic.py {cid}:/app/check_logic.py && docker exec {cid} python /app/check_logic.py')
print('OUT:\\n', stdout.read().decode())
print('ERR:\\n', stderr.read().decode())
client.close()
