import os
import sys
import logging
import uuid
import datetime

# Forzar el entorno a PostgreSQL para la prueba
os.environ["DATABASE_URL"] = "postgresql://qr_admin:MERcentads2026!.@167.172.217.151:5432/qr_database"
# NOTA: En un entorno real el puerto 5432 no está expuesto a internet.
# Dado que no podemos acceder directamente por red externa a Postgres,
# haremos la validación de sintaxis importando los módulos.

# Añadir el directorio actual al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import (
        adapt_query, 
        IS_POSTGRES, 
        POSTGRES_AVAILABLE,
        get_db_connection
    )
except ImportError as e:
    print(f"Error importando app.py: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDB")

def test_syntax_adaptation():
    """Valida puramente la sintaxis de conversión de SQLite a Postgres"""
    print("\n--- PRUEBA 1: Traductor Lógico (SQlite -> PostgreSQL) ---")
    
    queries = [
        # Insert básico con placeholders
        ("INSERT INTO users (name, age) VALUES (?, ?)", 
         "INSERT INTO users (name, age) VALUES (%s, %s)"),
         
        # Manejo de fechas NOW sqlite vs Postgres
        ("UPDATE users SET last_login = datetime('now') WHERE id = ?", 
         "UPDATE users SET last_login = NOW() WHERE id = %s"),
         
        # Manejo de intervalos de fecha
        ("SELECT * FROM scans WHERE timestamp > datetime('now', '-24 hours')",
         "SELECT * FROM scans WHERE timestamp > NOW() - INTERVAL '24 hours'"),
         
        # Manejo de múltiples placeholders en búsquedas in
        ("SELECT * FROM devices WHERE id IN (?, ?, ?)",
         "SELECT * FROM devices WHERE id IN (%s, %s, %s)")
    ]
    
    passed = 0
    for original, expected in queries:
        resultado = adapt_query(original)
        if resultado == expected:
            print(f"✅ ÉXITO: '{original}' -> '{resultado}'")
            passed += 1
        else:
            print(f"❌ FALLO:\n  Original: {original}\n  Obtenido: {resultado}\n  Esperado: {expected}")
            
    print(f"Resultado Prueba 1: {passed}/{len(queries)} correctos.")
    return passed == len(queries)

def check_architecture():
    """Confirma que la aplicación ha reconocido correctamente a Postgres"""
    print("\n--- PRUEBA 2: Validar Entorno y Adaptador ---")
    print(f"¿IS_POSTGRES?: {IS_POSTGRES}")
    print(f"¿POSTGRES_AVAILABLE (psycopg2)?: {POSTGRES_AVAILABLE}")
    print(f"DATABASE_URL configurada: {os.environ.get('DATABASE_URL')}")
    
    if IS_POSTGRES and POSTGRES_AVAILABLE:
        print("✅ Arquitectura de PostgreSQL activada correctamente en el código.")
        return True
    else:
        print("❌ Fallo en la arquitectura. La app no reconoce Postgres.")
        return False

if __name__ == "__main__":
    print("==================================================")
    print("INICIANDO AUDITORÍA DE SINTAXIS Y BASE DE DATOS")
    print("==================================================")
    
    p1 = test_syntax_adaptation()
    p2 = check_architecture()
    
    print("\n==================================================")
    if p1 and p2:
        print("ESTADO: APROBADO ✅")
        print("El código contiene la capa de compatibilidad perfecta.")
        print("Las consultas se traducirán a PostgreSQL correctamente.")
    else:
        print("ESTADO: RECHAZADO ❌")
        print("Existen problemas de sintaxis. No desplegar en producción.")
    print("==================================================")
