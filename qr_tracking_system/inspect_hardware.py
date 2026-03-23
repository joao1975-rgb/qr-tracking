import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Inspeccionando Huellas de Dispositivos Históricos...")

sql = """
-- Listar las combinaciones únicas de hardware registradas
SELECT 
    COUNT(id) as scans,
    COALESCE(device_brand, 'Desconocido') as brand, 
    COALESCE(device_model, 'Desconocido') as model, 
    COALESCE(operating_system, 'Desconocido') as os,
    COALESCE(ip_address, 'Sin IP') as ip
FROM scans
GROUP BY brand, model, os, ip
ORDER BY scans DESC;
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}}' --filter 'name=postgres-qr'")
    container_id = stdout.read().decode('utf-8').strip().split('\n')[0]
        
    cmd = f'docker exec -i {container_id} psql -U qr_admin -d qr_database'
    stdin, stdout, stderr = client.exec_command(cmd)
    
    stdin.write(sql.encode('utf-8'))
    stdin.channel.shutdown_write()
    
    out = stdout.read().decode('utf-8')
    print(out)
    
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
