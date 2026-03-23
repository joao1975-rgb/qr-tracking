import re
from device_detector import DeviceDetector

print("="*60)
print("[SIMULACION: SAMSUNG GALAXY Y APPLE IPHONE]")
print("="*60)

# ==========================================
# PRUEBA 1: SAMSUNG GALAXY S24/S25 ULTRA
# ==========================================
print("\n--- PRUEBA 1: SAMSUNG GALAXY ULTRA ---")
# Codigo de hardware filtrado por el navegador (Client Hints)
# SM-S928B = S24 Ultra | SM-S938B = S25 Ultra
samsung_hash = "SM-S928B" # Simular el modelo de hardware extraido por JS
raw_android_ua = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"

injected_samsung_ua = re.sub(r'(Android [^;]+;)\s*[^)]+', rf'\1 {samsung_hash}', raw_android_ua)
print(f"User-Agent Inyectado: {injected_samsung_ua}")

device_samsung = DeviceDetector(injected_samsung_ua).parse()
print(f"-> Marca  : {device_samsung.device_brand()}")
print(f"-> Modelo : {device_samsung.device_model()}")

samsung_hash2 = "SM-S938B"
print(f"\nCaso: Galaxy S25 Ultra detectado como: {samsung_hash2}")
injected_samsung_ua2 = re.sub(r'(Android [^;]+;)\s*[^)]+', rf'\1 {samsung_hash2}', raw_android_ua)
device_samsung2 = DeviceDetector(injected_samsung_ua2).parse()
print(f"-> Marca  : {device_samsung2.device_brand()}")
print(f"-> Modelo : {device_samsung2.device_model()}")

# ==========================================
# PRUEBA 2: APPLE iPHONE (Ej: iPhone 15/16/17 Pro)
# ==========================================
print("\n--- PRUEBA 2: APPLE iPHONE ---")
# En el ecosistema Apple, Safari NO bloquea la palabra "iPhone".
apple_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

device_apple = DeviceDetector(apple_ua).parse()
print(f" User-Agent Nativo: {apple_ua}")
print(f"-> Marca  : {device_apple.device_brand()}")
print(f"-> Modelo : {device_apple.device_model()}")
