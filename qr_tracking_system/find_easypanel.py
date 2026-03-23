import paramiko
import json
import re

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

print("Buscando meta.json de qr-tracking...")
stdin, stdout, stderr = client.exec_command('find /etc/easypanel -name "meta.json"')
files = stdout.read().decode('utf-8').strip().split('\n')

for f in files:
    if not f: continue
    stdin, out, err = client.exec_command(f'cat {f}')
    content = out.read().decode('utf-8')
    if 'qr' in content.lower():
        print(f"--- Archivo: {f} ---")
        try:
            data = json.loads(content)
            # Find deployWebhookUrl if it exists
            if 'source' in data and 'deployWebhookUrl' in data['source']:
                webhook = data['source']['deployWebhookUrl']
                print(f"Webhook URL encontrado: {webhook}")
                # trigger it!
                print("Disparando webhook...")
                client.exec_command(f'curl -X POST "{webhook}"')
                print("Webhook disparado!")
        except Exception as e:
            print(f"Error parseando: {e}")

client.close()
