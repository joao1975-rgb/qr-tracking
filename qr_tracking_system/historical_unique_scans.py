import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("Iniciando Barrido Histórico por Huella de Hardware (Brand/Model)...")

sql = """
-- 1. Restaurar todos a FALSE para limpiar el barrido por IP anterior
UPDATE scans SET is_unique = FALSE;

-- 2. Marcar como único el primer escaneo basándonos RIGUROSAMENTE en el modelo físico del dispositivo
UPDATE scans
SET is_unique = TRUE
WHERE id IN (
    SELECT MIN(id)
    FROM scans
    GROUP BY campaign_code, COALESCE(device_brand, 'Desconocido'), COALESCE(device_model, 'Desconocido')
);

-- 3. Verificar los resultados
SELECT 
    COUNT(*) as total_scans, 
    COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors 
FROM scans;

-- 4. Detalle de los Dispositivos Únicos Detectados
SELECT device_brand, device_model
FROM scans
WHERE is_unique = TRUE
ORDER BY device_brand;
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
    print("\n--- Resultados de la Re-Asignación Histórica ---")
    print(out)
    
    client.close()
    
except Exception as e:
    print(f"Error crítico ejecutando el barrido por modelo: {e}")
