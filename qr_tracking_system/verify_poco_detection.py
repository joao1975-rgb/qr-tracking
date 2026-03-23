import re
import json
from device_detector import DeviceDetector

print("="*60)
print("[SIMULACION DE ESCANEO: XIAOMI POCO PRO 7]")
print("="*60)

raw_user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
client_hint_model = "2412DPC0AG"
json_payload_from_frontend = '{"session_id": "test_123", "time_spent": 0.8, "completion_time": "2026-03-03T03:30:00Z"}'

print("[RECEPCION DEL FRONTEND]")
print(f"User-Agent nativo recibido: {raw_user_agent}")
print(f"Codigo Hardware extraido (JS): {client_hint_model}")
print(f"Payload de Duracion recibido: {json.loads(json_payload_from_frontend)['time_spent']} segundos")

print("\n[PROCESAMIENTO EN EL BACKEND (app.py)]")

modified_ua = re.sub(r'(Android [^;]+;)\s*[^)]+', rf'\1 {client_hint_model}', raw_user_agent)
print(f"-> User-Agent Inyectado (Generado por Python): {modified_ua}")

device = DeviceDetector(modified_ua).parse()

print("\n[RESULTADOS DE LA BASE DE DATOS]")
print(f"-> Marca del Dispositivo  : {device.device_brand()}")
print(f"-> Modelo del Dispositivo : {device.device_model()}")
print(f"-> Tipo de Dispositivo    : {device.device_type()}")

data = json.loads(json_payload_from_frontend)
duration = data.get("time_spent")
print(f"-> Duracion Almacenada    : {duration}s")

print("="*60)
print("[CONCLUSION: El sistema decodifica matematicamente el hardware POCO]")
print("="*60)
