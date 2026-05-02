import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("167.172.217.151", username="root", password="MERcenta2026!.ds", timeout=10)

# get container name
stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
container = next((c for c in containers if 'qr-tracking' in c), None)

if container:
    cmd = f"docker exec {container} curl -s http://localhost:8000/api/analytics/dashboard"
    stdin, stdout, stderr = client.exec_command(cmd)
    try:
        resp = json.loads(stdout.read().decode())
        if 'daily_scans' in resp:
            print("SUCCESS! daily_scans found. Length:", len(resp['daily_scans']))
            print(resp['daily_scans'])
        else:
            print("FAILED! Resp keys:", resp.keys())
            if 'error' in resp:
                print("SERVER ERROR:", resp['error'])
    except Exception as e:
        print("JSON parse error:", e, stdout.read().decode()[:1000])
else:
    print("Container not found")

client.close()
