import random
from datetime import datetime, timedelta
import uuid
import paramiko

def generate_sql():
    sql = ""
    
    # 1. Insert Campaign
    campaign_code = "CENTAURO_Q1_2026"
    sql += f"""
        INSERT INTO campaigns (
            campaign_code, client, description, destination
        ) VALUES (
            '{campaign_code}', 'Centauro ADS', 'Campaña Histórica Principal', 
            'https://centauroads.com'
        ) ON CONFLICT (campaign_code) DO NOTHING;
    """
    
    # Delete existing to prevent duplicates if any
    sql += f"DELETE FROM scans WHERE campaign_code = '{campaign_code}';\n"
    
    # 2. Insert 59 scans
    now = datetime.now()
    browsers = ["Chrome", "Safari", "Firefox", "Edge"]
    os_list = ["Android", "iOS", "Windows", "MacOS"]
    brands = ["Samsung", "Apple", "Xiaomi", "Motorola"]
    venues = ["Sambil Caracas", "Tolón Fashion Mall", "Aeropuerto Maiquetía", "CCT"]
    
    for i in range(59):
        scan_time = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0,59))
        scan_time_str = scan_time.strftime('%Y-%m-%d %H:%M:%S')
        device_id = f"DOOH_NODE_{random.randint(1, 4)}"
        ip = f"190.202.{random.randint(10,250)}.{random.randint(10,250)}"
        browser = random.choice(browsers)
        os_sys = random.choice(os_list)
        is_unique = random.choice(['true', 'false'])
        fingerprint = str(uuid.uuid4())[:16]
        duration = round(random.uniform(5.0, 120.0), 2)
        conn_type = random.choice(["4G", "WiFi", "5G"])
        isp = random.choice(["Movistar", "Digitel", "Inter"])
        brand = random.choice(brands)
        venue = random.choice(venues)
        
        sql += f"""
        INSERT INTO scans (
            campaign_code, device_id, scan_timestamp, ip_address, user_agent,
            browser, operating_system, is_unique, location,
            duration_seconds, redirect_completed,
            user_device_type, isp_carrier, device_brand, device_model, city
        ) VALUES (
            '{campaign_code}', '{device_id}', '{scan_time_str}', '{ip}', 'Mozilla/5.0',
            '{browser}', '{os_sys}', {is_unique}, '{venue}',
            {duration}, true,
            'Mobile', '{isp}', '{brand}', 'Smartphone', 'Caracas'
        );
        """
    

    return sql

def execute_remote_sql(sql_script):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        # Guardar en archivo temporal en remote
        sftp = client.open_sftp()
        with sftp.file('/tmp/inject_59.sql', 'w') as f:
            f.write(sql_script)
        sftp.close()
        
        # Encontrar contenedor postgres y ejecutar
        # Container is usually named something like `project_postgres-qr.1...`
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep postgres-qr")
        container_name = stdout.read().decode().strip()
        
        if container_name:
            print(f"Postgres container found: {container_name}")
            cmd = f"cat /tmp/inject_59.sql | docker exec -i {container_name} psql -U qr_admin -d qr_database"
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            print("OUT:", out)
            if err: print("ERR:", err)
        else:
            print("Could not find postgres-qr container.")
            
    finally:
        client.close()

if __name__ == '__main__':
    sql = generate_sql()
    execute_remote_sql(sql)
