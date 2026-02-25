#!/usr/bin/env python3
"""
QR Tracking System - Script de Migración
=========================================
Este script modifica el archivo app.py original para hacerlo compatible
con PostgreSQL mientras mantiene compatibilidad con SQLite.

Uso:
    python migrate_app.py app.py
    
Esto generará: app_cloud.py (versión para Cloud Run)
"""

import re
import sys
import os

def migrate_app(input_file: str, output_file: str = None):
    """
    Migrar app.py para soportar PostgreSQL
    """
    if not output_file:
        output_file = input_file.replace('.py', '_cloud.py')
    
    print(f"Migrando {input_file} → {output_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # =====================================================
    # 1. Modificar imports
    # =====================================================
    
    # Agregar imports necesarios después de los imports existentes
    new_imports = '''
# ================================
# IMPORTACIONES PARA CLOUD (PostgreSQL)
# ================================
from config import (
    DATABASE_URL, IS_POSTGRES, PORT, HOST, 
    ENVIRONMENT, BASE_URL, ENABLE_BACKUPS, LOG_LEVEL
)
from database import (
    get_db_connection, init_database as init_db_schema,
    adapt_query, check_connection, IS_POSTGRES
)

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
'''
    
    # Insertar después de los imports de sqlite3
    content = re.sub(
        r'(import sqlite3\n)',
        r'\1' + new_imports,
        content
    )
    
    # =====================================================
    # 2. Modificar DATABASE_PATH para usar config
    # =====================================================
    
    content = re.sub(
        r'DATABASE_PATH = os\.path\.join\(BASE_DIR, "qr_tracking\.db"\)',
        'DATABASE_PATH = DATABASE_URL if IS_POSTGRES else os.path.join(BASE_DIR, "qr_tracking.db")',
        content
    )
    
    # =====================================================
    # 3. Reemplazar sqlite3.connect con nuestra función
    # =====================================================
    
    # No necesitamos reemplazar porque ya usamos get_db_connection()
    # Pero necesitamos asegurarnos de que use nuestra versión
    
    # =====================================================
    # 4. Modificar init_database() para usar el módulo
    # =====================================================
    
    # Reemplazar la función init_database completa
    old_init_db = r'''def init_database\(\):
    """Inicializar la base de datos con el esquema"""
    try:
        with sqlite3\.connect\(DATABASE_PATH\) as conn:
            # Crear esquema básico
            create_basic_schema\(conn\)
            # Verificar que las tablas existan
            cursor = conn\.cursor\(\)
            cursor\.execute\("SELECT name FROM sqlite_master WHERE type='table';"\)
            tables = cursor\.fetchall\(\)
            logger\.info\(f"Tablas en base de datos: \{[^}]+\}"\)
        logger\.info\("Base de datos inicializada correctamente"\)
    except Exception as e:
        logger\.error\(f"Error inicializando base de datos: \{e\}"\)'''
    
    new_init_db = '''def init_database():
    """Inicializar la base de datos con el esquema"""
    try:
        # Usar el módulo database para inicializar
        init_db_schema()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")'''
    
    # Usar una expresión más flexible
    content = re.sub(
        r'def init_database\(\):\s+"""Inicializar la base de datos con el esquema"""\s+try:\s+with sqlite3\.connect\(DATABASE_PATH\) as conn:[^}]+logger\.info\("Base de datos inicializada correctamente"\)\s+except Exception as e:\s+logger\.error\(f"Error inicializando base de datos: \{e\}"\)',
        new_init_db,
        content,
        flags=re.DOTALL
    )
    
    # =====================================================
    # 5. Modificar get_db_connection si existe localmente
    # =====================================================
    
    # Comentar la función local get_db_connection ya que usamos la del módulo
    content = re.sub(
        r'(def get_db_connection\(\):\s+"""Obtener conexión a la base de datos"""\s+conn = sqlite3\.connect\(DATABASE_PATH\)\s+conn\.row_factory = sqlite3\.Row[^}]+return conn)',
        r'''# Función movida a database.py - usar import
# \1''',
        content,
        flags=re.DOTALL
    )
    
    # =====================================================
    # 6. Cambiar placeholders ? por %s para PostgreSQL
    # =====================================================
    
    # Esto se maneja dinámicamente en adapt_query(), no necesitamos cambiar el código
    
    # =====================================================
    # 7. Modificar funciones de fecha SQLite
    # =====================================================
    
    # datetime('now', '-24 hours') → adapt_query lo maneja
    # Pero podemos hacer algunas sustituciones directas para mayor compatibilidad
    
    # =====================================================
    # 8. Modificar el puerto para Cloud Run
    # =====================================================
    
    # Cambiar puerto por defecto a 8080 y usar variables de entorno
    content = re.sub(
        r'port=8000',
        'port=int(os.getenv("PORT", 8080))',
        content
    )
    
    # =====================================================
    # 9. Modificar el host para Cloud Run
    # =====================================================
    
    content = re.sub(
        r'host="0\.0\.0\.0"',
        'host=os.getenv("HOST", "0.0.0.0")',
        content
    )
    
    # =====================================================
    # 10. Manejar IntegrityError para PostgreSQL
    # =====================================================
    
    content = re.sub(
        r'except sqlite3\.IntegrityError:',
        'except (sqlite3.IntegrityError, Exception) as e:\n        if "UNIQUE" in str(e) or "duplicate" in str(e).lower():',
        content
    )
    
    # =====================================================
    # 11. Modificar backup para que no falle en Cloud Run
    # =====================================================
    
    # Envolver funciones de backup con verificación
    backup_check = '''
    # Verificar si backups están habilitados (no en Cloud Run con PostgreSQL)
    if IS_POSTGRES:
        logger.info("Backups deshabilitados en modo PostgreSQL (usar backups de Neon)")
        return None
    '''
    
    content = re.sub(
        r'(def create_backup\(backup_type: str = "auto"\)[^:]+:)\s+"""',
        r'\1\n    """\n' + backup_check,
        content
    )
    
    # =====================================================
    # 12. Modificar migrate_database para PostgreSQL
    # =====================================================
    
    # PRAGMA no existe en PostgreSQL, necesitamos adaptar
    content = re.sub(
        r'cursor\.execute\("PRAGMA table_info\(scans\)"\)',
        '''# Obtener columnas existentes (compatible con SQLite y PostgreSQL)
        if IS_POSTGRES:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'scans'
            """)
            existing_columns = [col[0] if isinstance(col, tuple) else list(col.values())[0] for col in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(scans)")
            existing_columns = [col[1] for col in cursor.fetchall()]''',
        content
    )
    
    # =====================================================
    # 13. Deshabilitar reload en producción
    # =====================================================
    
    content = re.sub(
        r'reload=True',
        'reload=os.getenv("ENVIRONMENT", "development") == "development"',
        content
    )
    
    # =====================================================
    # 14. Agregar endpoint de health check mejorado
    # =====================================================
    
    # Ya existe /api/health, pero podemos mejorarlo
    
    # =====================================================
    # Guardar archivo modificado
    # =====================================================
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Migración completada: {output_file}")
    print("")
    print("Próximos pasos:")
    print("1. Revisa el archivo generado")
    print("2. Copia config.py y database.py al mismo directorio")
    print("3. Crea el archivo .env con tus credenciales")
    print("4. Ejecuta: python app_cloud.py")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Uso: python migrate_app.py <archivo_app.py>")
        print("Ejemplo: python migrate_app.py app.py")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Archivo '{input_file}' no encontrado")
        sys.exit(1)
    
    migrate_app(input_file, output_file)


if __name__ == "__main__":
    main()
