import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
container = next((c for c in containers if 'qr-tracking-db' in c or 'postgres' in c), None)

if container:
    script = "SELECT user_device_type, operating_system, COUNT(*) as total_scans, COUNT(DISTINCT ip_address) as unique_ips FROM scans GROUP BY user_device_type, operating_system"
    cmd = f"docker exec {container} psql -U postgres -d postgres -t -c \"{script}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode().strip())
    print("ERR:", stderr.read().decode())
client.close()
