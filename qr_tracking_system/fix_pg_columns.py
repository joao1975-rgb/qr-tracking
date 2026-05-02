import paramiko

sql = """
ALTER TABLE scans ADD COLUMN IF NOT EXISTS cpu_cores INTEGER;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS device_pixel_ratio REAL;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS device_brand VARCHAR(50);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS device_model VARCHAR(50);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS utm_source VARCHAR(100);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(100);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(100);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS utm_term VARCHAR(100);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS utm_content VARCHAR(100);
"""
ip = "167.172.217.151"
user = "root"
password = "MERcenta2026!.ds"

print("Uploading schema adjustments into DigitalOcean PostgreSQL Database...")
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password, timeout=10)
    
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}}' --filter 'name=postgres-qr'")
    container_id = stdout.read().decode('utf-8').strip().split('\n')[0]
    
    cmd = f"docker exec -i {container_id} psql -U qr_admin -d qr_database"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    stdin.write(sql.encode('utf-8'))
    stdin.channel.shutdown_write()
    
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    print("\n--- Output ---")
    print(out)
    if err:
        print("\n--- Errors ---")
        print(err)

    print("Migration pushed successfully.")
    client.close()
except Exception as e:
    print(f"Error: {e}")
