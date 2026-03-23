import paramiko

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command('docker ps --filter name=qr-tracking --format "{{.ID}}"')
    cont_id = stdout.read().decode('utf-8').strip()
    
    if cont_id:
        print(f"Generating logs for container {cont_id}")
        stdin, stdout, stderr = ssh.exec_command(f'docker logs --tail 50 {cont_id}')
        logs = stdout.read().decode('utf-8')
        errs = stderr.read().decode('utf-8')
        print("OUT:", logs)
        print("ERR:", errs)
    else:
        print("Container not found via docker ps.")
        
    ssh.close()
except Exception as e:
    print("Exception occurred:", e)
