import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}'")
containers = stdout.read().decode().strip().split('\n')
container = next((c for c in containers if 'qr-tracking' in c), None)

cmd = f"docker exec {container} python -c \"\n\
import urllib.request as urllib2\n\
try:\n\
    with urllib2.urlopen('http://localhost:80/api/analytics/dashboard?campaign_code=DEMO_COMPLETA') as response:\n\
        print(response.read().decode()[:1500])\n\
except Exception as e:\n\
    try:\n\
        with urllib2.urlopen('http://localhost:8000/api/analytics/dashboard?campaign_code=DEMO_COMPLETA') as response:\n\
            print(response.read().decode()[:1500])\n\
    except Exception as e2:\n\
        print(e, e2)\n\
\""
stdin, stdout, stderr = client.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
client.close()
