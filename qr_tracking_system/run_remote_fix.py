import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')

with open('fix_redirect_analytics.py', 'r', encoding='utf-8') as f:
    script_content = f.read()

cmd = "docker exec -i e81549cc2d65 python -c \"import sys; exec(sys.stdin.read())\""
stdin, stdout, stderr = client.exec_command(cmd)
stdin.write("import sys\n")
stdin.write(script_content)
stdin.channel.shutdown_write()

print(stdout.read().decode())
print('ERRORS:', stderr.read().decode())
client.close()
