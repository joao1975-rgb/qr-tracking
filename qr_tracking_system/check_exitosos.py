import paramiko
import json
import warnings
warnings.filterwarnings('ignore')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/api/analytics/dashboard")
out = stdout.read().decode().strip()
client.close()

try:
    data = json.loads(out)
    print("TOTAL SCANS:", data['stats']['total_scans'])
    print("EXITOSOS:", data['stats']['completed_redirects'])
except Exception as e:
    print("Error:", e, "- RAW OUT:", out[:200])
