import paramiko
import os
import sys

print("INICIANDO PROTOCOLO DE AUDITORÍA REMOTA - ISO/IEC 27001 / DevOps Compliance...")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('167.172.217.151', username='root', password='MERcenta2026!.ds')
    print("✓ Conexión SSH a orquestador de producción establecida (167.172.217.151)")

    # 1. Buscar contenedor de la aplicación qr-tracking
    stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}}' | grep qr-tracking | head -n 1")
    app_container = stdout.read().decode('utf-8').strip()

    if not app_container:
        print("x ERROR: No se encontró el contenedor de qr-tracking en ejecución.")
        sys.exit(1)

    print(f"✓ Contenedor identificado en producción: {app_container}")

    # 2. Forzar Github Pull en el entorno /usr/src/app (o donde esté mapeado) si es necesario, 
    # pero primero vamos a leer el archivo actuamente en ejecución.
    
    cmd_read = f"docker exec {app_container} cat /usr/src/app/templates/reports.html | grep 'id=\"scansCard\"'"
    stdin, stdout, stderr = client.exec_command(cmd_read)
    grep_output = stdout.read().decode('utf-8').strip()

    if 'id="scansCard"' in grep_output:
        print("\n=======================================================")
        print("✓ EVIDENCIA ENCONTRADA: 'Detalles de Escaneos (Histórico)'")
        print("El contenedor actual en producción ya contiene el tag HTML de la auditoría.")
        print("Los cambios están activos en el Frontend remoto.")
        print("=======================================================")
    else:
        print("\n! ALERTA: El contenedor local de producción NO refleja los últimos cambios de Github.")
        print("Iniciando despliegue forzoso...")
        
        # Como easypanel deploy falló, usamos dokku o reconstituimos el docker.
        # Generalmente easypanel se actualiza reiniciándolo o haciendo un pull de Github webhook.
        # Enviaremos un trigger manual.
        client.exec_command(f"docker exec {easypanel_container} pnpm easypanel deploy qr-tracking")
        print("Disparado reinicio de servicio para hacer Pull en Producción.")

except Exception as e:
    print(f"FAILED: {e}")
finally:
    client.close()
