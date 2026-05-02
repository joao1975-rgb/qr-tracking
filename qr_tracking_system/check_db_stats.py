import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.172.217.151", username="root", password="MERcenta2026!.ds", timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
container = next((c for c in containers if 'qr-tracking-db' in c or 'postgres' in c), None)

if container:
    cmds = [
        "SELECT COUNT(*) FROM scans;",
        "SELECT COUNT(DISTINCT ip_address) FROM scans;",
        "SELECT COUNT(DISTINCT session_id) FROM scans;",
        "SELECT COUNT(DISTINCT user_agent) FROM scans;",
        "SELECT operating_system, COUNT(DISTINCT ip_address) as unique_ips, COUNT(DISTINCT session_id) as unique_sessions FROM scans GROUP BY operating_system;"
    ]
    for q in cmds:
        cmd = f"docker exec {container} psql -U postgres -d postgres -t -c \"{q}\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"--- QUERY: {q}\nRESPONSE:\n{stdout.read().decode().strip()}\nERR: {stderr.read().decode().strip()}")
client.close()
