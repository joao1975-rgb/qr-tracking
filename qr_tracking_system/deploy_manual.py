import paramiko

def force_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Conectando al servidor...")
        client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds', timeout=15)
        
        commands = [
            "cd /tmp/qr_build/qr_tracking_system && docker build -t easypanel/project/qr-tracking:latest . > build.log 2>&1",
            "docker service update --image easypanel/project/qr-tracking:latest --force project_qr-tracking",
        ]
        
        for cmd in commands:
            print(f"Exec: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out: print("OUT:", out)
            if err: print("ERR:", err)
            if exit_status != 0:
                print(f"Error executing. Aborting.")
                break
                
        print("Done.")
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    force_deploy()
