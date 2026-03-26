import paramiko

ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("🔍 Generando Datos Semilla Históricos e Industriales en EasyPanel...")

script_docker = """
import logging
import database
import random
from datetime import datetime, timedelta
import uuid

logging.basicConfig(level=logging.INFO)

try:
    with database.get_db_connection() as c:
        cursor = c.cursor()
        
        # 1. Obtener la campaña existente (para saber el cliente)
        cursor.execute("SELECT * FROM campaigns LIMIT 1")
        base_campaign = cursor.fetchone()
        
        if not base_campaign:
            client_name = "Cliente Demo"
        else:
            client_name = dict(base_campaign).get('client', 'Cliente Demo') or "Cliente Demo"
            
        print(f"Utilizando cliente base: {client_name}")
        
        # Generar fechas
        now = datetime.now()
        
        # --- CREAR CAMPAÑAS HISTÓRICAS DEL MISMO CLIENTE ---
        past_campaigns = [
            {
                "code": "HIST-01-2025",
                "desc": "Campaña Histórica Q4 2025 (Exitosa)",
                "created": now - timedelta(days=90),
                "industry": "retail",
                "industry_sub": "moda",
                "campaign_type": "branding",
                "geo_country": "CL",
                "bg": "BG_RETAIL_BRANDING"
            },
            {
                "code": "HIST-02-2025",
                "desc": "Campaña Verano 2025",
                "created": now - timedelta(days=150),
                "industry": "retail",
                "industry_sub": "moda",
                "campaign_type": "promocion",
                "geo_country": "CL",
                "bg": "BG_RETAIL_PROMO"
            }
        ]
        
        # --- CREAR CAMPAÑAS DE OTROS CLIENTES (BENCHMARK INDUSTRIA) ---
        benchmark_campaigns = [
            {
                "code": "BENCH-RETAIL-01",
                "desc": "Competidor Retail A",
                "client": "Competidor A",
                "created": now - timedelta(days=60),
                "industry": "retail",
                "campaign_type": "branding",
                "bg": "BG_RETAIL_BRANDING"
            },
            {
                "code": "BENCH-RETAIL-02",
                "desc": "Competidor Retail B",
                "client": "Competidor B",
                "created": now - timedelta(days=45),
                "industry": "retail",
                "campaign_type": "promocion",
                "bg": "BG_RETAIL_PROMO"
            }
        ]
        
        all_new_c = []
        for c_data in past_campaigns:
            all_new_c.append((
                c_data["code"], client_name, c_data["desc"], "https://example.com", 
                True, c_data["created"], "completed", c_data["industry"], 
                c_data["campaign_type"], c_data.get("geo_country", "CL"), 
                c_data["bg"], True
            ))
            
        for c_data in benchmark_campaigns:
            all_new_c.append((
                c_data["code"], c_data["client"], c_data["desc"], "https://example.com/b", 
                True, c_data["created"], "completed", c_data["industry"], 
                c_data["campaign_type"], c_data.get("geo_country", "CL"), 
                c_data["bg"], True
            ))
            
        insert_c_query = '''
            INSERT INTO campaigns (
                campaign_code, client, description, destination, active, 
                created_at, campaign_status, industry, campaign_type, 
                geo_country, benchmark_group, is_benchmark_eligible
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (campaign_code) DO NOTHING
        '''
        
        cursor.executemany(insert_c_query, all_new_c)
        
        # --- CREAR SCANS PARA ESTAS CAMPAÑAS ---
        scans = []
        import random
        # Generar 120 scans para HIST-01
        for _ in range(120):
            t = (now - timedelta(days=random.randint(60, 90))).isoformat()
            scans.append(("HIST-01-2025", 'DEVICE-X', '192.168.1.1', 'Santiago', t, True, random.choice([True, False]), round(random.uniform(1.0, 15.0), 2)))
            
        # Generar 85 scans para HIST-02
        for _ in range(85):
            t = (now - timedelta(days=random.randint(120, 150))).isoformat()
            scans.append(("HIST-02-2025", 'DEVICE-Y', '192.168.1.2', 'Santiago', t, True, random.choice([True, False]), round(random.uniform(1.0, 10.0), 2)))

        # Generar 200 scans para Competidor A
        for _ in range(200):
            t = (now - timedelta(days=random.randint(10, 60))).isoformat()
            scans.append(("BENCH-RETAIL-01", 'DEVICE-Z', '192.168.1.3', 'Bogota', t, True, True, round(random.uniform(2.0, 12.0), 2)))
            
        # Generar 150 scans para Competidor B
        for _ in range(150):
            t = (now - timedelta(days=random.randint(5, 45))).isoformat()
            scans.append(("BENCH-RETAIL-02", 'DEVICE-W', '192.168.1.4', 'Lima', t, True, True, round(random.uniform(5.0, 25.0), 2)))
        
        insert_s_query = '''
            INSERT INTO scans (
                campaign_code, device_id, ip_address, location, scan_timestamp, 
                is_unique, redirect_completed, duration_seconds
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.executemany(insert_s_query, scans)
        
        c.commit()
        print("✅ Base de datos poblada con mock data histórico exitosamente.")
        
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        print("TOTAL CAMPAIGNS AHORA:", cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM scans")
        print("TOTAL SCANS AHORA:", cursor.fetchone()[0])
        
except Exception as e:
    import traceback
    traceback.print_exc()
"""

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Names}}' | grep qr-tracking")
    containers = stdout.read().decode('utf-8').strip()
    container_name = containers.split(' ')[1] if containers else None
    
    if container_name:
        cmd = f"docker exec -i {container_name} python"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.write(script_docker)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        print(stdout.read().decode('utf-8'))
        print(stderr.read().decode('utf-8'))
        
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
