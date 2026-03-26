import paramiko

def execute_remote_sql():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
        
        sql_script = """
        INSERT INTO campaigns (
            campaign_code, client, total_scans, is_active, start_date, end_date, planned_duration_days
        ) VALUES (
            'CENTAURO_Q1_2026', 'Centauro ADS', 59, true, NOW() - INTERVAL '60 days', NOW() + INTERVAL '30 days', 90
        ) ON CONFLICT (campaign_code) DO NOTHING;
        """
        
        sftp = client.open_sftp()
        with sftp.file('/tmp/inject_camp.sql', 'w') as f:
            f.write(sql_script)
        sftp.close()
        
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep postgres-qr")
        container_name = stdout.read().decode().strip()
        
        if container_name:
            cmd = f"cat /tmp/inject_camp.sql | docker exec -i {container_name} psql -U qr_admin -d qr_database"
            stdin, stdout, stderr = client.exec_command(cmd)
            print("OUT:", stdout.read().decode())
            print("ERR:", stderr.read().decode())
            
    finally:
        client.close()

if __name__ == '__main__':
    execute_remote_sql()
