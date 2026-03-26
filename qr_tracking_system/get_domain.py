import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}}' --filter name=qr-tracking | head -n 1")
cont_id = stdout.read().decode('utf-8').strip()

if cont_id:
    stdin, stdout, stderr = client.exec_command(f"docker inspect {cont_id}")
    data = json.loads(stdout.read().decode('utf-8'))
    if data and len(data) > 0:
        labels = data[0]['Config']['Labels']
        for k, v in labels.items():
            if 'traefik.http.routers.' in k and '.rule' in k:
                print(f"Traefik Rule: {v}")
client.close()
