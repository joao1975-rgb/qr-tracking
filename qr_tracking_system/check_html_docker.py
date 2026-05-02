from paramiko import SSHClient, AutoAddPolicy
client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().splitlines()
container = next((c for c in containers if 'qr-tracking' in c), None)

cmd = f"docker exec {container} python -c \"\n\
with open('/app/templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:\n\
    text = f.read()\n\
if 'AISLAMIENTO' in text:\n\
    print('YES IT WAS MODIFIED IN CONTAINER')\n\
else:\n\
    idx = text.find('loadLiveStats')\n\
    print('NO IT WAS NOT MODIFIED IN CONTAINER', text[idx:idx+200])\n\
\""
stdin, stdout, stderr = client.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
client.close()
