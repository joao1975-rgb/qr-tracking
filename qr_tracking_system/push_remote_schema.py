import paramiko

sql = ""
with open("migration_campaigns_v280.sql", "r", encoding="utf-8") as f:
    sql = f.read()

sql += "\nALTER TABLE scans ADD COLUMN IF NOT EXISTS is_unique BOOLEAN DEFAULT FALSE;\n"

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
    
    cmd = f'docker exec -i {container_id} psql -U qr_admin -d qr_database'
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Pipe the raw SQL directly
    stdin.write(sql.encode('utf-8'))
    stdin.channel.shutdown_write()  # Send EOF to psql so it computes and returns
    
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
    print(f"Error executing remote push: {e}")
