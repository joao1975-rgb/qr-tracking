import sys
import os

# Simularemos entorno para no cargar DB
os.environ["DATABASE_URL"] = "none"
os.environ["TESTING"] = "true"

try:
    from app import generate_qr_image
    print("app.py importado correctamente.")
    
    # Prueba 1: Generación Básica
    print("Probando generación básica (sin logo)...")
    res1 = generate_qr_image("https://example.com/test", 500, "M", "#000000", "#FFFFFF", "none", None)
    if res1 and len(res1) > 100:
        print("OK: QR Básico generado. Len B64:", len(res1))
    else:
        print("FALLO: QR básico vacío o muy corto")

    # Prueba 2: Generación Default (asume que CENTAURO_LOGO_BASE64 en app.py cargará o al menos fallará limpio no reventará el app)
    print("Probando generación con logo default...")
    res2 = generate_qr_image("https://example.com/test_logo", 500, "M", "#000000", "#FFFFFF", "default", None)
    if res2 and len(res2) > 100:
        print("OK: QR Logo generado. Len B64:", len(res2))
    else:
        print("FALLO: QR Logo vacío o con error")

except Exception as e:
    print(f"ERROR durante las pruebas: {e}")
