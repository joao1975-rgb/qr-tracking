import paramiko

def trigger_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("Conectando al servidor por SSH...")
        client.connect('137.184.2.148', username='root', password='MERcenta2026!.ds')
        
        print("Disparando pipeline de despliegue en EasyPanel...")
        stdin, stdout, stderr = client.exec_command('docker exec easypanel easypanel deploy qr-tracking')
        
        # Read the stream in real time until EOF
        print(stdout.read().decode())
        
        err = stderr.read().decode()
        if err:
            print(f"Errores (si aplica): {err}")
            
    except Exception as e:
        print(f"Falló la conexión o ejecución: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    trigger_deploy()
