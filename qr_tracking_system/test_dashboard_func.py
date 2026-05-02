import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)

stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking | head -n 1")
container = stdout.read().decode().strip()

cmd = f"docker exec {container} python -c \"\n\
from app import get_dashboard_analytics\n\
import asyncio\n\
async def test():\n\
    try:\n\
        res = await get_dashboard_analytics()\n\
        print('SUCCESS:', res.get('success'), 'ERROR:', res.get('error'))\n\
        print('STATS:', res.get('stats'))\n\
        print('TARGETS:', res.get('targets'))\n\
    except Exception as e:\n\
        print('Crash calling func:', e)\n\
asyncio.run(test())\n\
\""
stdin, stdout, stderr = client.exec_command(cmd)
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
client.close()
