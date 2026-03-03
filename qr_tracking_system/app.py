"""
QR Tracking System - Backend Completo
Versión: 2.7.3 - Analytics Avanzados + Dispositivos Únicos + UTM
Autor: Sistema QR Tracking
Fecha: 2024

Funcionalidades:
- Gestión completa de campañas
- Gestión de dispositivos físicos
- Tracking avanzado de escaneos
- Analytics en tiempo real
- Dashboard general con métricas
- Reportes por cliente
- APIs RESTful completas
- Servir archivos HTML estáticos
- Exportación de datos (JSON/CSV)
- Sistema de backups automáticos
- Logging avanzado con rotación de archivos
- Archivos estáticos (CSS/JS/Images)
- **GENERACIÓN DE CÓDIGOS QR COMPLETA**

Correcciones v2.7.1:
- Botón Eliminar en Campañas ahora elimina permanentemente (antes solo pausaba)
- Nuevo endpoint PUT /api/campaigns/{code}/pause para pausar/reanudar
- Nuevo endpoint GET /api/campaigns/{code}/tracking-url para copiar URL de tracking

Correcciones v2.7.2:
- NUEVO: Endpoint POST /api/qr/generate - Genera QR desde campañas registradas
- NUEVO: Endpoint POST /api/qr/generate-custom - Genera QR desde URL personalizada
- NUEVO: Frontend completo de generación de QR con preview en tiempo real
- NUEVO: Soporte para estilos de QR (cuadrado, redondeado, circular)
- NUEVO: Personalización de colores en códigos QR
- NUEVO: Descarga de QR en formato PNG
- Integración completa con biblioteca qrcode para generación de imágenes

Correcciones v2.7.3:
- NUEVO: Tracking de dispositivos únicos (unique_visitors) en dashboard
- NUEVO: Captura y almacenamiento de parámetros UTM (source, medium, campaign, term, content)
- NUEVO: Captura de CPU cores (navigator.hardwareConcurrency)
- NUEVO: Captura de Device Pixel Ratio (window.devicePixelRatio)
- CORREGIDO: Diferenciación correcta entre Total Escaneos y Escaneos Hoy (24h)
- NUEVO: Columnas de duración y estado de conexión en últimos escaneos
- MEJORADO: Analytics con datos de marketing (UTM) para efectividad de campañas
"""

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import base64
import io

try:
    from logos_base64 import CENTAURO_LOGO_BASE64, CENTAURO_BANNER_BASE64
except ImportError:
    CENTAURO_LOGO_BASE64 = None
    CENTAURO_BANNER_BASE64 = None

# ================================
# CONFIGURACIÓN PARA CLOUD (PostgreSQL/SQLite)
# ================================
import os
import re as regex_module

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://qr_admin:pass@localhost:5432/qr_database")

# Importar dependencias de PostgreSQL obligatorias
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("⚠️  ADVERTENCIA: psycopg2 no instalado. Ejecute: pip install psycopg2-binary")
    import sys
    sys.exit(1)

import json
import os
import shutil
import glob
import logging
from logging.handlers import RotatingFileHandler
import csv
import io
import base64
from datetime import datetime, timedelta
import uuid
from device_detector import DeviceDetector
import ipaddress
from urllib.parse import urlparse, parse_qs, unquote, urlencode, quote

# ================================
# IMPORTAR BIBLIOTECAS PARA QR
# ================================

# Intentar importar qrcode (necesario para generación de QR)
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    QR_LIBRARY_AVAILABLE = True
except ImportError:
    QR_LIBRARY_AVAILABLE = False
    print("⚠️  ADVERTENCIA: Biblioteca 'qrcode' no instalada.")
    print("   Ejecute: pip install qrcode[pil]")

# Intentar importar PIL para manipulación de imágenes
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  ADVERTENCIA: Biblioteca 'Pillow' no instalada.")
    print("   Ejecute: pip install Pillow")


# ================================
# CONFIGURACIÓN DE DIRECTORIOS
# ================================

# Directorios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Crear directorios si no existen
for directory in [LOGS_DIR, BACKUPS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Ruta de base de datos
DATABASE_PATH = DATABASE_URL

# ================================
# CONFIGURACIÓN DE LOGGING AVANZADO
# ================================

def setup_logging():
    """Configurar sistema de logging con rotación de archivos"""
    
    # Formato de logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    detailed_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    formatter = logging.Formatter(log_format)
    detailed_formatter = logging.Formatter(detailed_format)
    
    # Logger principal
    logger = logging.getLogger("qr_tracking")
    logger.setLevel(logging.DEBUG)
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo general (10MB, 5 backups)
    app_log_path = os.path.join(LOGS_DIR, "app.log")
    file_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para errores (5MB, 3 backups)
    error_log_path = os.path.join(LOGS_DIR, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Handler para scans/tracking (20MB, 10 backups)
    scans_log_path = os.path.join(LOGS_DIR, "scans.log")
    scans_handler = RotatingFileHandler(
        scans_log_path,
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10,
        encoding='utf-8'
    )
    scans_handler.setLevel(logging.INFO)
    scans_handler.setFormatter(formatter)
    
    # Logger específico para scans
    scans_logger = logging.getLogger("qr_tracking.scans")
    scans_logger.addHandler(scans_handler)
    
    # Handler para debug (solo en desarrollo)
    debug_log_path = os.path.join(LOGS_DIR, "debug.log")
    debug_handler = RotatingFileHandler(
        debug_log_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=2,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    logger.addHandler(debug_handler)
    
    return logger

# Inicializar logger
logger = setup_logging()
scans_logger = logging.getLogger("qr_tracking.scans")

# ================================
# SISTEMA DE BACKUPS
# ================================

def create_backup(backup_type: str = "auto") -> Optional[str]:
    """
    Crear backup de la base de datos
    
    Args:
        backup_type: "auto" para automático, "manual" para manual
    
    Returns:
        Ruta del backup creado o None si falla
        
    NOTA: En PostgreSQL (Cloud/Neon), los backups se manejan automáticamente.
    """
    # En PostgreSQL, los backups se manejan desde la infraestructura
    logger.info("Backups manejados por el servidor en modo PostgreSQL")
    return None
        
    try:
        if not os.path.exists(DATABASE_PATH):
            logger.warning("No existe base de datos para respaldar")
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"qr_tracking_{backup_type}_{timestamp}.db"
        backup_path = os.path.join(BACKUPS_DIR, backup_filename)
        
        # Copiar base de datos
        shutil.copy2(DATABASE_PATH, backup_path)
        
        # Obtener tamaño del backup
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = backup_size / (1024 * 1024)
        
        logger.info(f"Backup creado: {backup_filename} ({backup_size_mb:.2f} MB)")
        
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        return None

def cleanup_old_backups(keep_auto: int = 7, keep_manual: int = 30) -> Dict[str, int]:
    """
    Eliminar backups antiguos manteniendo los más recientes
    
    Args:
        keep_auto: Número de backups automáticos a mantener
        keep_manual: Número de backups manuales a mantener
    
    Returns:
        Diccionario con cantidad de backups eliminados por tipo
    """
    deleted = {"auto": 0, "manual": 0}
    
    try:
        # Obtener backups automáticos
        auto_backups = sorted(
            glob.glob(os.path.join(BACKUPS_DIR, "qr_tracking_auto_*.db")),
            key=os.path.getmtime,
            reverse=True
        )
        
        # Eliminar backups automáticos antiguos
        for old_backup in auto_backups[keep_auto:]:
            os.remove(old_backup)
            deleted["auto"] += 1
            logger.info(f"Backup automático eliminado: {os.path.basename(old_backup)}")
        
        # Obtener backups manuales
        manual_backups = sorted(
            glob.glob(os.path.join(BACKUPS_DIR, "qr_tracking_manual_*.db")),
            key=os.path.getmtime,
            reverse=True
        )
        
        # Eliminar backups manuales antiguos
        for old_backup in manual_backups[keep_manual:]:
            os.remove(old_backup)
            deleted["manual"] += 1
            logger.info(f"Backup manual eliminado: {os.path.basename(old_backup)}")
        
        if deleted["auto"] > 0 or deleted["manual"] > 0:
            logger.info(f"Limpieza de backups: {deleted['auto']} automáticos, {deleted['manual']} manuales eliminados")
        
        return deleted
        
    except Exception as e:
        logger.error(f"Error limpiando backups: {e}")
        return deleted

def get_backup_info() -> Dict[str, Any]:
    """Obtener información sobre los backups existentes"""
    try:
        backups = []
        total_size = 0
        
        for backup_file in glob.glob(os.path.join(BACKUPS_DIR, "*.db")):
            file_stat = os.stat(backup_file)
            file_size = file_stat.st_size
            total_size += file_size
            
            # Determinar tipo de backup
            filename = os.path.basename(backup_file)
            if "_auto_" in filename:
                backup_type = "auto"
            elif "_manual_" in filename:
                backup_type = "manual"
            else:
                backup_type = "unknown"
            
            backups.append({
                "filename": filename,
                "type": backup_type,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "path": backup_file
            })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backups": backups
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo info de backups: {e}")
        return {"total_backups": 0, "total_size_mb": 0, "backups": [], "error": str(e)}

def restore_backup(backup_filename: str) -> bool:
    """
    Restaurar un backup específico
    
    Args:
        backup_filename: Nombre del archivo de backup
    
    Returns:
        True si se restauró correctamente
    """
    try:
        backup_path = os.path.join(BACKUPS_DIR, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup no encontrado: {backup_filename}")
            return False
        
        # Crear backup de seguridad antes de restaurar
        create_backup("pre-restore")
        
        # Restaurar
        shutil.copy2(backup_path, DATABASE_PATH)
        logger.info(f"Backup restaurado: {backup_filename}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error restaurando backup: {e}")
        return False

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================

app = FastAPI(
    title="QR Tracking System",
    description="Sistema avanzado de tracking para códigos QR con dashboard, reportes, backups y logging",
    version="2.7.2"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Archivos estáticos montados en /static desde {STATIC_DIR}")

# ================================
# MODELOS PYDANTIC
# ================================

class CampaignCreate(BaseModel):
    campaign_code: str
    client: str
    destination: str
    description: Optional[str] = None
    active: bool = True

class CampaignUpdate(BaseModel):
    client: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

class DeviceCreate(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    description: Optional[str] = None
    active: bool = True

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

class ScanCreate(BaseModel):
    campaign_code: str
    client: Optional[str] = None
    destination: Optional[str] = None
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    session_id: Optional[str] = None

class DeviceDataUpdate(BaseModel):
    """Datos adicionales del dispositivo del usuario"""
    session_id: str
    screen_resolution: Optional[str] = None
    viewport_size: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    platform: Optional[str] = None
    user_agent: Optional[str] = None
    connection_type: Optional[str] = None
    cpu_cores: Optional[int] = None
    device_pixel_ratio: Optional[float] = None
    ua_brand: Optional[str] = None
    ua_model: Optional[str] = None

class QRGenerationLog(BaseModel):
    campaign_id: Optional[int] = None
    physical_device_id: Optional[int] = None
    qr_size: int = 256
    generated_by: Optional[str] = None

class QRGenerateRequest(BaseModel):
    """Solicitud de generación de QR desde campaña registrada"""
    campaign_code: str
    device_id: Optional[str] = None
    size: int = 300
    format: str = "png"  # png o svg
    style: str = "square"  # square, rounded, circle
    color_dark: str = "#000000"
    color_light: str = "#FFFFFF"
    include_logo: bool = False
    base_url: Optional[str] = None  # URL base del servidor (ej: http://192.168.1.100:8000)
    logo_mode: str = "default"
    brand_logo_base64: Optional[str] = None
    brand_banner_base64: Optional[str] = None

class QRCustomRequest(BaseModel):
    """Solicitud de generación de QR personalizado desde URL"""
    url: str
    size: int = 300
    format: str = "png"
    style: str = "square"
    color_dark: str = "#000000"
    color_light: str = "#FFFFFF"
    error_correction: str = "M"  # L, M, Q, H
    logo_mode: str = "default"
    brand_logo_base64: Optional[str] = None
    brand_banner_base64: Optional[str] = None

class LogoValidationRequest(BaseModel):
    image_base64: str
    filename: str

class BackupRequest(BaseModel):
    """Solicitud de backup manual"""
    description: Optional[str] = None

class RestoreRequest(BaseModel):
    """Solicitud de restauración de backup"""
    backup_filename: str
    confirm: bool = False

# ================================
# FUNCIONES DE BASE DE DATOS
# ================================

def init_database():
    """Inicializar la base de datos con el esquema"""
    try:
        with get_db_connection() as conn:
            # Crear esquema básico
            create_basic_schema(conn)
            # Verificar que las tablas existan
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            table_names = [t['table_name'] if isinstance(t, dict) else t[0] for t in tables]
            logger.info(f"Tablas en base de datos: {table_names}")
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")

def create_basic_schema(conn):
    """Crear esquema PostgreSQL"""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id SERIAL PRIMARY KEY,
            campaign_code TEXT NOT NULL UNIQUE,
            client TEXT NOT NULL,
            destination TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS physical_devices (
            id SERIAL PRIMARY KEY,
            device_id TEXT NOT NULL UNIQUE,
            device_name TEXT,
            device_type TEXT,
            location TEXT,
            venue TEXT,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id SERIAL PRIMARY KEY,
            campaign_code TEXT NOT NULL,
            client TEXT,
            destination TEXT,
            device_id TEXT,
            device_name TEXT,
            location TEXT,
            venue TEXT,
            user_device_type TEXT,
            browser TEXT,
            operating_system TEXT,
            screen_resolution TEXT,
            viewport_size TEXT,
            timezone TEXT,
            language TEXT,
            platform TEXT,
            connection_type TEXT,
            user_agent TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            session_id TEXT,
            scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            redirect_completed BOOLEAN DEFAULT FALSE,
            redirect_timestamp TIMESTAMP,
            duration_seconds REAL,
            campaign_id INTEGER,
            physical_device_id INTEGER,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            utm_term TEXT,
            utm_content TEXT,
            cpu_cores INTEGER,
            device_pixel_ratio REAL,
            device_brand TEXT,
            device_model TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_generations (
            id SERIAL PRIMARY KEY,
            campaign_id INTEGER,
            physical_device_id INTEGER,
            qr_size INTEGER,
            generated_by TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Crear índices
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_scans_campaign ON scans(campaign_code)",
        "CREATE INDEX IF NOT EXISTS idx_scans_device ON scans(device_id)",
        "CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(scan_timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_scans_session ON scans(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client)",
        "CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address)",
        "CREATE INDEX IF NOT EXISTS idx_scans_utm_source ON scans(utm_source)"
    ]
    for idx in indices:
        try:
            cursor.execute(idx)
        except:
            pass
    
    conn.commit()
    
    # Ejecutar migración para agregar columnas nuevas si no existen
    migrate_database(conn)

def migrate_database(conn):
    """Migrar base de datos agregando columnas nuevas si no existen"""
    cursor = conn.cursor()
    
    # Obtener columnas existentes en la tabla scans
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'scans'")
    existing_columns = [col['column_name'] if isinstance(col, dict) else col[0] for col in cursor.fetchall()]
    
    # Columnas nuevas a agregar (v2.7.3)
    new_columns = {
        'utm_source': 'TEXT',
        'utm_medium': 'TEXT',
        'utm_campaign': 'TEXT',
        'utm_term': 'TEXT',
        'utm_content': 'TEXT',
        'cpu_cores': 'INTEGER',
        'device_pixel_ratio': 'REAL',
        'device_brand': 'TEXT',
        'device_model': 'TEXT',
        'isp_carrier': 'TEXT'
    }
    
    # Agregar columnas que no existan
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                try:
                    cursor.execute(f"ALTER TABLE scans ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                except Exception:
                    pass
                logger.info(f"Columna '{column_name}' agregada a tabla scans")
            except Exception as e:
                # La columna ya existe (puede ocurrir en casos edge)
                logger.debug(f"Columna '{column_name}' ya existe o error: {e}")
    
    conn.commit()
    logger.info("Migración de base de datos completada")

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.DictCursor
    return conn

# ================================
# FUNCIONES DE UTILIDAD
# ================================

def detect_device_info(user_agent_string: str) -> Dict[str, str]:
    """Detectar información del dispositivo desde User-Agent usando device-detector"""
    try:
        device = DeviceDetector(user_agent_string).parse()
        
        # Determinar tipo de dispositivo
        device_type = device.device_type() if device.device_type() else "Unknown"
        device_brand = device.device_brand() if device.device_brand() else "Unknown"
        device_model = device.device_model() if device.device_model() else "Unknown"
        
        os_info = device.os_name()
        if device.os_version():
            os_info = f"{os_info} {device.os_version()}"
            
        client_info = device.client_name()
        if device.client_version():
            client_info = f"{client_info} {device.client_version()}"
            
        return {
            "device_type": device_type,
            "device_brand": device_brand,
            "device_model": device_model,
            "browser": client_info if client_info else "Unknown",
            "operating_system": os_info if os_info else "Unknown",
            "is_mobile": device_type in ["smartphone", "feature phone", "phablet"],
            "is_tablet": device_type == "tablet",
            "is_pc": device_type == "desktop"
        }
    except Exception as e:
        logger.warning(f"Error detectando dispositivo: {e}")
        return {
            "device_type": "Unknown",
            "device_brand": "Unknown",
            "device_model": "Unknown",
            "browser": "Unknown",
            "operating_system": "Unknown",
            "is_mobile": False,
            "is_tablet": False,
            "is_pc": False
        }

def get_client_ip(request: Request) -> str:
    """Obtener IP del cliente"""
    # Intentar obtener IP real detrás de proxies
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

def get_logs_info() -> Dict[str, Any]:
    """Obtener información sobre los archivos de log"""
    try:
        logs = []
        total_size = 0
        
        for log_file in glob.glob(os.path.join(LOGS_DIR, "*.log*")):
            file_stat = os.stat(log_file)
            file_size = file_stat.st_size
            total_size += file_size
            
            logs.append({
                "filename": os.path.basename(log_file),
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        # Ordenar por fecha de modificación
        logs.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return {
            "total_logs": len(logs),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo info de logs: {e}")
        return {"total_logs": 0, "total_size_mb": 0, "logs": [], "error": str(e)}

# ================================
# ENDPOINTS DE PÁGINAS HTML
# ================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal"""
    try:
        # Leer el archivo HTML del index
        index_path = os.path.join(TEMPLATES_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Reemplazar variables del template
        base_url = "http://localhost:8000"  # Cambiar según configuración
        html_content = html_content.replace("{{ base_url }}", base_url)
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>QR Tracking System</title>
            <link rel="stylesheet" href="/static/css/main.css">
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; }
                .container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; max-width: 600px; }
                h1 { color: #333; margin-bottom: 10px; }
                .version { color: #888; font-size: 14px; margin-bottom: 30px; }
                .nav-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 20px; }
                .nav-link { display: block; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; transition: transform 0.2s, box-shadow 0.2s; }
                .nav-link:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(102,126,234,0.4); }
                .status { margin-top: 30px; padding: 15px; background: #f0f9ff; border-radius: 10px; }
                .status-ok { color: #059669; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 QR Tracking System</h1>
                <p class="version">Versión 2.7.0</p>
                <p>Sistema de tracking avanzado para códigos QR</p>
                
                <div class="nav-grid">
                    <a href="/dashboard" class="nav-link">📊 Dashboard</a>
                    <a href="/reports" class="nav-link">📈 Reportes</a>
                    <a href="/admin/campaigns" class="nav-link">🎯 Campañas</a>
                    <a href="/devices" class="nav-link">📱 Dispositivos</a>
                    <a href="/generate-qr" class="nav-link">🔲 Generar QR</a>
                    <a href="/admin/system" class="nav-link">⚙️ Sistema</a>
                </div>
                
                <div class="status">
                    <span class="status-ok">✓</span> Sistema funcionando correctamente
                </div>
            </div>
        </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """Endpoint vital para que EasyPanel/Docker sepa que la app está viva"""
    return {"status": "ok", "version": "2.7.3", "timestamp": datetime.now().isoformat()}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard con analytics"""
    try:
        dashboard_path = os.path.join(TEMPLATES_DIR, "dashboard.html")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard</h1><p>Archivo dashboard.html no encontrado en /templates</p><a href='/'>← Volver</a>")

@app.get("/reports", response_class=HTMLResponse)
async def reports_page():
    """Página de reportes por cliente"""
    try:
        reports_path = os.path.join(TEMPLATES_DIR, "reports.html")
        with open(reports_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Reportes</h1><p>Archivo reports.html no encontrado en /templates</p><a href='/'>← Volver</a>")

@app.get("/tracking", response_class=HTMLResponse)
async def tracking_page():
    """Página de tracking mejorada"""
    try:
        tracking_path = os.path.join(TEMPLATES_DIR, "tracking.html")
        with open(tracking_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Tracking</h1><p>Archivo tracking.html no encontrado en /templates</p><a href='/'>← Volver</a>")

@app.get("/admin/campaigns", response_class=HTMLResponse)
async def admin_campaigns():
    """Panel de administración de campañas"""
    try:
        admin_path = os.path.join(TEMPLATES_DIR, "admin_campaigns.html")
        with open(admin_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Admin Campañas</h1><p>Archivo admin_campaigns.html no encontrado en /templates</p><a href='/'>← Volver</a>")

@app.get("/generate-qr", response_class=HTMLResponse)
async def generate_qr_page():
    """Generador de códigos QR - Página con frontend completo"""
    try:
        qr_path = os.path.join(TEMPLATES_DIR, "generate_qr.html")
        with open(qr_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Frontend completo embebido cuando no existe el archivo HTML
        return HTMLResponse("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generar QR - QR Tracking System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); min-height: 100vh; color: #1f2937; }
        
        .navbar { background: white; padding: 15px 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }
        .navbar-brand { font-size: 1.5rem; font-weight: 700; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; }
        .navbar-nav { display: flex; gap: 8px; list-style: none; flex-wrap: wrap; }
        .navbar-nav a { color: #6b7280; text-decoration: none; padding: 10px 16px; border-radius: 10px; transition: all 0.2s; font-weight: 500; font-size: 14px; }
        .navbar-nav a:hover { color: #667eea; background: rgba(102, 126, 234, 0.1); }
        .navbar-nav a.active { color: white; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }
        .page-header { margin-bottom: 30px; text-align: center; }
        .page-title { font-size: 2.2rem; font-weight: 700; color: #1f2937; margin-bottom: 8px; }
        .page-subtitle { color: #6b7280; font-size: 1.1rem; }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        @media (max-width: 1024px) { .grid { grid-template-columns: 1fr; } }
        
        .card { background: white; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 30px; }
        .card-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 25px; display: flex; align-items: center; gap: 12px; color: #1f2937; }
        
        .form-group { margin-bottom: 22px; }
        .form-label { display: block; font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 8px; }
        .form-input, .form-select { width: 100%; padding: 14px 18px; font-size: 15px; border: 2px solid #e5e7eb; border-radius: 12px; transition: all 0.2s; font-family: inherit; background: white; }
        .form-input:focus, .form-select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15); }
        
        .color-row { display: flex; gap: 20px; }
        .color-group { flex: 1; }
        .color-input { width: 100%; height: 50px; padding: 5px; border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; }
        .color-input:focus { border-color: #667eea; }
        
        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 16px 32px; font-size: 16px; font-weight: 600; border: none; border-radius: 12px; cursor: pointer; transition: all 0.3s; width: 100%; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4); }
        .btn-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .btn-success:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); }
        .btn-secondary { background: #f3f4f6; color: #374151; border: 2px solid #e5e7eb; }
        .btn-secondary:hover { background: #e5e7eb; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none !important; }
        
        .qr-preview { text-align: center; padding: 40px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 16px; min-height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px dashed #e2e8f0; }
        .qr-preview.has-qr { border-style: solid; border-color: #667eea; }
        .qr-preview img { max-width: 300px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.12); }
        .qr-placeholder { color: #9ca3af; }
        .qr-placeholder-icon { font-size: 80px; margin-bottom: 20px; opacity: 0.4; }
        
        .download-buttons { display: flex; gap: 12px; margin-top: 25px; width: 100%; max-width: 350px; }
        .download-buttons .btn { flex: 1; padding: 14px 20px; font-size: 14px; }
        
        .url-display { background: #f8fafc; padding: 15px 18px; border-radius: 12px; font-family: 'Courier New', monospace; font-size: 13px; word-break: break-all; margin-top: 20px; color: #475569; border: 1px solid #e2e8f0; max-width: 350px; }
        .url-display strong { color: #1f2937; display: block; margin-bottom: 8px; font-family: 'Plus Jakarta Sans', sans-serif; }
        
        .toast-container { position: fixed; bottom: 30px; right: 30px; z-index: 2000; }
        .toast { background: white; padding: 18px 24px; border-radius: 14px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.18); display: flex; align-items: center; gap: 14px; min-width: 320px; animation: slideIn 0.4s ease; margin-top: 12px; }
        @keyframes slideIn { from { transform: translateX(120%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .toast.success { border-left: 5px solid #10b981; }
        .toast.error { border-left: 5px solid #ef4444; }
        .toast.warning { border-left: 5px solid #f59e0b; }
        
        .loading { display: none; align-items: center; justify-content: center; gap: 12px; }
        .spinner { width: 22px; height: 22px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .tabs { display: flex; gap: 12px; margin-bottom: 30px; background: #f3f4f6; padding: 6px; border-radius: 14px; }
        .tab { flex: 1; padding: 14px 20px; background: transparent; border: none; border-radius: 10px; cursor: pointer; font-weight: 600; color: #6b7280; transition: all 0.3s; font-size: 15px; }
        .tab.active { background: white; color: #667eea; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .tab:hover:not(.active) { color: #374151; }
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status-badge.success { background: #d1fae5; color: #065f46; }
        .status-badge.error { background: #fee2e2; color: #991b1b; }
        
        .info-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 16px; margin-bottom: 20px; }
        .info-box p { color: #1e40af; font-size: 14px; line-height: 1.6; }
        
        @media (max-width: 768px) {
            .navbar { flex-direction: column; gap: 15px; padding: 15px; }
            .navbar-nav { justify-content: center; }
            .container { padding: 20px; }
            .page-title { font-size: 1.8rem; }
            .color-row { flex-direction: column; }
            .download-buttons { flex-direction: column; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="/" class="navbar-brand">🎯 QR Tracking System</a>
        <ul class="navbar-nav">
            <li><a href="/dashboard">📊 Dashboard</a></li>
            <li><a href="/admin/campaigns">🎯 Campañas</a></li>
            <li><a href="/devices">📱 Dispositivos</a></li>
            <li><a href="/reports">📈 Reportes</a></li>
            <li><a href="/generate-qr" class="active">🔲 Generar QR</a></li>
        </ul>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">🔲 Generador de Códigos QR</h1>
            <p class="page-subtitle">Genera códigos QR para tus campañas o cualquier URL personalizada</p>
            <div style="margin-top: 15px;">
                <span class="status-badge" id="qrStatus">⏳ Verificando...</span>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('campaign')">📋 Desde Campaña</button>
                    <button class="tab" onclick="switchTab('custom')">🔗 URL Personalizada</button>
                </div>
                
                <!-- Tab: Desde Campaña -->
                <div id="tab-campaign" class="tab-content active">
                    <h3 class="card-title">🎯 Generador de QR Avanzado</h3>
                    
                    <div class="info-box">
                        <p>💡 Seleccione una campaña activa para generar un código QR que rastree automáticamente los escaneos.</p>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Seleccionar Campaña *</label>
                        <select class="form-select" id="campaignSelect">
                            <option value="">⏳ Cargando campañas...</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Dispositivo Físico (opcional)</label>
                        <select class="form-select" id="deviceSelect">
                            <option value="">Sin dispositivo específico</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Tamaño del QR</label>
                        <select class="form-select" id="sizeSelect">
                            <option value="200">200 × 200 px (Pequeño)</option>
                            <option value="300" selected>300 × 300 px (Mediano)</option>
                            <option value="400">400 × 400 px (Grande)</option>
                            <option value="500">500 × 500 px (Extra Grande)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Colores del QR</label>
                        <div class="color-row">
                            <div class="color-group">
                                <label class="form-label" style="font-size: 12px;">Color Oscuro</label>
                                <input type="color" class="color-input" id="colorDark" value="#000000">
                            </div>
                            <div class="color-group">
                                <label class="form-label" style="font-size: 12px;">Color Claro (Fondo)</label>
                                <input type="color" class="color-input" id="colorLight" value="#FFFFFF">
                            </div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateCampaignQR()" id="btnGenerate">
                        <span id="btnText">🔲 Generar QR</span>
                        <span class="loading" id="btnLoading"><div class="spinner"></div> Generando...</span>
                    </button>
                </div>
                
                <!-- Tab: URL Personalizada -->
                <div id="tab-custom" class="tab-content">
                    <h3 class="card-title">🔗 QR Personalizado</h3>
                    
                    <div class="info-box">
                        <p>💡 Ingrese cualquier URL o texto para generar un código QR personalizado.</p>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">URL o Texto *</label>
                        <input type="text" class="form-input" id="customUrl" placeholder="https://ejemplo.com/mi-pagina">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Tamaño del QR</label>
                        <select class="form-select" id="customSize">
                            <option value="200">200 × 200 px</option>
                            <option value="300" selected>300 × 300 px</option>
                            <option value="400">400 × 400 px</option>
                            <option value="500">500 × 500 px</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Nivel de Corrección de Errores</label>
                        <select class="form-select" id="errorCorrection">
                            <option value="L">L - 7% (Menor tamaño)</option>
                            <option value="M" selected>M - 15% (Recomendado)</option>
                            <option value="Q">Q - 25% (Alta calidad)</option>
                            <option value="H">H - 30% (Máxima corrección)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Colores del QR</label>
                        <div class="color-row">
                            <div class="color-group">
                                <label class="form-label" style="font-size: 12px;">Color Oscuro</label>
                                <input type="color" class="color-input" id="customColorDark" value="#000000">
                            </div>
                            <div class="color-group">
                                <label class="form-label" style="font-size: 12px;">Color Claro (Fondo)</label>
                                <input type="color" class="color-input" id="customColorLight" value="#FFFFFF">
                            </div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateCustomQR()" id="btnGenerateCustom">
                        <span id="btnTextCustom">🔲 Generar QR Personalizado</span>
                        <span class="loading" id="btnLoadingCustom"><div class="spinner"></div> Generando...</span>
                    </button>
                </div>
            </div>
            
            <div class="card">
                <h3 class="card-title">👁️ Vista Previa del QR</h3>
                
                <div class="qr-preview" id="qrPreview">
                    <div class="qr-placeholder">
                        <div class="qr-placeholder-icon">🔲</div>
                        <p style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">El código QR aparecerá aquí</p>
                        <p style="font-size: 14px;">Seleccione una campaña o ingrese una URL para comenzar</p>
                    </div>
                </div>
                
                <div class="url-display" id="urlDisplay" style="display: none;">
                    <strong>🔗 URL codificada:</strong>
                    <span id="qrUrlText"></span>
                </div>
                
                <div class="download-buttons" id="downloadButtons" style="display: none;">
                    <button class="btn btn-success" onclick="downloadQR()">
                        📥 Descargar PNG
                    </button>
                    <button class="btn btn-secondary" onclick="copyQRUrl()">
                        📋 Copiar URL
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        let currentQRData = null;
        let currentQRUrl = null;
        
        // Verificar estado del sistema QR
        async function checkQRStatus() {
            try {
                const response = await fetch('/api/qr/status');
                const data = await response.json();
                const badge = document.getElementById('qrStatus');
                
                if (data.qr_library_available) {
                    badge.className = 'status-badge success';
                    badge.textContent = '✅ Sistema QR Operativo';
                } else {
                    badge.className = 'status-badge error';
                    badge.textContent = '❌ Biblioteca QR no instalada';
                    showToast('Instale: pip install qrcode[pil] Pillow', 'warning');
                }
            } catch (e) {
                console.error('Error verificando estado:', e);
            }
        }
        
        // Mostrar toast
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
            toast.innerHTML = '<span style="font-size: 20px;">' + (icons[type] || icons.info) + '</span><span>' + message + '</span>';
            container.appendChild(toast);
            setTimeout(() => { toast.style.animation = 'slideIn 0.3s ease reverse'; setTimeout(() => toast.remove(), 300); }, 4000);
        }
        
        // Cambiar tabs
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }
        
        // Cargar campañas
        async function loadCampaigns() {
            try {
                const response = await fetch('/api/campaigns');
                const data = await response.json();
                const select = document.getElementById('campaignSelect');
                
                if (data.success && data.campaigns && data.campaigns.length > 0) {
                    const activeCampaigns = data.campaigns.filter(c => c.active);
                    if (activeCampaigns.length > 0) {
                        select.innerHTML = '<option value="">-- Seleccionar campaña --</option>' +
                            activeCampaigns.map(c => 
                                '<option value="' + c.campaign_code + '">' + c.client + ' - ' + c.campaign_code + '</option>'
                            ).join('');
                    } else {
                        select.innerHTML = '<option value="">⚠️ No hay campañas activas</option>';
                    }
                } else {
                    select.innerHTML = '<option value="">⚠️ No hay campañas disponibles</option>';
                }
            } catch (e) {
                console.error('Error cargando campañas:', e);
                document.getElementById('campaignSelect').innerHTML = '<option value="">❌ Error cargando campañas</option>';
            }
        }
        
        // Cargar dispositivos
        async function loadDevices() {
            try {
                const response = await fetch('/api/devices');
                const data = await response.json();
                const select = document.getElementById('deviceSelect');
                
                if (data.success && data.devices && data.devices.length > 0) {
                    const activeDevices = data.devices.filter(d => d.active);
                    select.innerHTML = '<option value="">Sin dispositivo específico</option>' +
                        activeDevices.map(d => 
                            '<option value="' + d.device_id + '">' + d.device_name + ' - ' + (d.location || 'Sin ubicación') + '</option>'
                        ).join('');
                }
            } catch (e) {
                console.error('Error cargando dispositivos:', e);
            }
        }
        
        // Generar QR desde campaña
        async function generateCampaignQR() {
            const campaignCode = document.getElementById('campaignSelect').value;
            if (!campaignCode) {
                showToast('Seleccione una campaña', 'error');
                return;
            }
            
            const btn = document.getElementById('btnGenerate');
            const btnText = document.getElementById('btnText');
            const btnLoading = document.getElementById('btnLoading');
            
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
            
            try {
                const response = await fetch('/api/qr/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        campaign_code: campaignCode,
                        device_id: document.getElementById('deviceSelect').value || null,
                        size: parseInt(document.getElementById('sizeSelect').value),
                        color_dark: document.getElementById('colorDark').value,
                        color_light: document.getElementById('colorLight').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayQR(data.qr_image, data.tracking_url);
                    showToast('¡Código QR generado exitosamente!', 'success');
                } else {
                    showToast(data.error || 'Error generando QR', 'error');
                }
            } catch (e) {
                console.error('Error:', e);
                showToast('Error de conexión: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                btnText.style.display = 'inline-flex';
                btnLoading.style.display = 'none';
            }
        }
        
        // Generar QR personalizado
        async function generateCustomQR() {
            const url = document.getElementById('customUrl').value.trim();
            if (!url) {
                showToast('Ingrese una URL o texto', 'error');
                return;
            }
            
            const btn = document.getElementById('btnGenerateCustom');
            const btnText = document.getElementById('btnTextCustom');
            const btnLoading = document.getElementById('btnLoadingCustom');
            
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
            
            try {
                const response = await fetch('/api/qr/generate-custom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: url,
                        size: parseInt(document.getElementById('customSize').value),
                        error_correction: document.getElementById('errorCorrection').value,
                        color_dark: document.getElementById('customColorDark').value,
                        color_light: document.getElementById('customColorLight').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayQR(data.qr_image, url);
                    showToast('¡QR personalizado generado!', 'success');
                } else {
                    showToast(data.error || 'Error generando QR', 'error');
                }
            } catch (e) {
                console.error('Error:', e);
                showToast('Error de conexión: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                btnText.style.display = 'inline-flex';
                btnLoading.style.display = 'none';
            }
        }
        
        // Mostrar QR en preview
        function displayQR(base64Image, url) {
            currentQRData = base64Image;
            currentQRUrl = url;
            
            const preview = document.getElementById('qrPreview');
            preview.innerHTML = '<img src="data:image/png;base64,' + base64Image + '" alt="Código QR generado">';
            preview.classList.add('has-qr');
            
            document.getElementById('urlDisplay').style.display = 'block';
            document.getElementById('qrUrlText').textContent = url;
            document.getElementById('downloadButtons').style.display = 'flex';
        }
        
        // Descargar QR
        function downloadQR() {
            if (!currentQRData) {
                showToast('Primero genere un código QR', 'error');
                return;
            }
            
            const link = document.createElement('a');
            const timestamp = new Date().toISOString().slice(0, 10);
            link.download = 'qr_code_' + timestamp + '.png';
            link.href = 'data:image/png;base64,' + currentQRData;
            link.click();
            showToast('QR descargado exitosamente', 'success');
        }
        
        // Copiar URL
        function copyQRUrl() {
            if (!currentQRUrl) {
                showToast('No hay URL para copiar', 'error');
                return;
            }
            
            navigator.clipboard.writeText(currentQRUrl).then(() => {
                showToast('URL copiada al portapapeles', 'success');
            }).catch(() => {
                // Fallback
                const input = document.createElement('input');
                input.value = currentQRUrl;
                document.body.appendChild(input);
                input.select();
                document.execCommand('copy');
                document.body.removeChild(input);
                showToast('URL copiada', 'success');
            });
        }
        
        // Cargar parámetros de URL
        function loadUrlParams() {
            const params = new URLSearchParams(window.location.search);
            const campaign = params.get('campaign');
            if (campaign) {
                setTimeout(() => {
                    const select = document.getElementById('campaignSelect');
                    if (select) {
                        for (let option of select.options) {
                            if (option.value === campaign) {
                                select.value = campaign;
                                generateCampaignQR();
                                break;
                            }
                        }
                    }
                }, 800);
            }
        }
        
        // Inicializar
        document.addEventListener('DOMContentLoaded', () => {
            checkQRStatus();
            loadCampaigns();
            loadDevices();
            loadUrlParams();
        });
    </script>
</body>
</html>
        """)

@app.get("/devices", response_class=HTMLResponse)
async def devices_page():
    """Página de gestión de dispositivos"""
    try:
        devices_path = os.path.join(TEMPLATES_DIR, "devices.html")
        with open(devices_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>Dispositivos - QR Tracking</title></head>
        <body>
            <h1>Gestión de Dispositivos</h1>
            <p>Archivo devices.html no encontrado en /templates</p>
            <a href="/">← Volver al inicio</a>
        </body>
        </html>
        """)

@app.get("/admin/system", response_class=HTMLResponse)
async def admin_system():
    """Panel de administración del sistema (backups, logs)"""
    try:
        system_path = os.path.join(TEMPLATES_DIR, "admin_system.html")
        with open(system_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Página básica de administración del sistema
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Administración del Sistema - QR Tracking</title>
            <link rel="stylesheet" href="/static/css/main.css">
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; }
                .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .btn { display: inline-block; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; margin-right: 10px; }
                .btn:hover { background: #5a6fd6; }
                .btn-danger { background: #dc3545; }
                .btn-danger:hover { background: #c82333; }
                .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .info-item { background: #f8f9fa; padding: 15px; border-radius: 8px; }
                .info-item label { font-weight: bold; color: #666; }
                .info-item span { display: block; font-size: 24px; color: #333; }
                #result { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
                .success { background: #d4edda; color: #155724; }
                .error { background: #f8d7da; color: #721c24; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚙️ Administración del Sistema</h1>
                <p><a href="/">← Volver al inicio</a></p>
                
                <div class="card">
                    <h2>📦 Backups</h2>
                    <div class="info-grid" id="backupInfo">
                        <div class="info-item">
                            <label>Total Backups</label>
                            <span id="totalBackups">-</span>
                        </div>
                        <div class="info-item">
                            <label>Tamaño Total</label>
                            <span id="backupSize">-</span>
                        </div>
                    </div>
                    <br>
                    <button class="btn" onclick="createBackup()">💾 Crear Backup Manual</button>
                    <button class="btn" onclick="cleanupBackups()">🧹 Limpiar Backups Antiguos</button>
                    <button class="btn" onclick="loadBackups()">🔄 Actualizar Lista</button>
                    
                    <table id="backupTable">
                        <thead>
                            <tr>
                                <th>Archivo</th>
                                <th>Tipo</th>
                                <th>Tamaño</th>
                                <th>Fecha</th>
                            </tr>
                        </thead>
                        <tbody id="backupList"></tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>📋 Logs</h2>
                    <div class="info-grid" id="logsInfo">
                        <div class="info-item">
                            <label>Archivos de Log</label>
                            <span id="totalLogs">-</span>
                        </div>
                        <div class="info-item">
                            <label>Tamaño Total</label>
                            <span id="logsSize">-</span>
                        </div>
                    </div>
                    <br>
                    <button class="btn" onclick="loadLogs()">🔄 Actualizar Lista</button>
                    
                    <table id="logsTable">
                        <thead>
                            <tr>
                                <th>Archivo</th>
                                <th>Tamaño</th>
                                <th>Última Modificación</th>
                            </tr>
                        </thead>
                        <tbody id="logsList"></tbody>
                    </table>
                </div>
                
                <div id="result"></div>
            </div>
            
            <script>
                function showResult(message, isError = false) {
                    const result = document.getElementById('result');
                    result.textContent = message;
                    result.className = isError ? 'error' : 'success';
                    result.style.display = 'block';
                    setTimeout(() => result.style.display = 'none', 5000);
                }
                
                async function loadBackups() {
                    try {
                        const response = await fetch('/api/admin/backups');
                        const data = await response.json();
                        
                        document.getElementById('totalBackups').textContent = data.total_backups;
                        document.getElementById('backupSize').textContent = data.total_size_mb + ' MB';
                        
                        const tbody = document.getElementById('backupList');
                        tbody.innerHTML = data.backups.map(b => `
                            <tr>
                                <td>${b.filename}</td>
                                <td>${b.type}</td>
                                <td>${b.size_mb} MB</td>
                                <td>${new Date(b.created_at).toLocaleString()}</td>
                            </tr>
                        `).join('');
                    } catch (e) {
                        showResult('Error cargando backups: ' + e.message, true);
                    }
                }
                
                async function createBackup() {
                    try {
                        const response = await fetch('/api/admin/backups', { method: 'POST' });
                        const data = await response.json();
                        if (data.success) {
                            showResult('Backup creado: ' + data.backup_path);
                            loadBackups();
                        } else {
                            showResult('Error: ' + data.error, true);
                        }
                    } catch (e) {
                        showResult('Error creando backup: ' + e.message, true);
                    }
                }
                
                async function cleanupBackups() {
                    try {
                        const response = await fetch('/api/admin/backups/cleanup', { method: 'POST' });
                        const data = await response.json();
                        if (data.success) {
                            showResult(`Limpieza completada: ${data.deleted.auto} auto, ${data.deleted.manual} manuales eliminados`);
                            loadBackups();
                        } else {
                            showResult('Error: ' + data.error, true);
                        }
                    } catch (e) {
                        showResult('Error en limpieza: ' + e.message, true);
                    }
                }
                
                async function loadLogs() {
                    try {
                        const response = await fetch('/api/admin/logs');
                        const data = await response.json();
                        
                        document.getElementById('totalLogs').textContent = data.total_logs;
                        document.getElementById('logsSize').textContent = data.total_size_mb + ' MB';
                        
                        const tbody = document.getElementById('logsList');
                        tbody.innerHTML = data.logs.map(l => `
                            <tr>
                                <td>${l.filename}</td>
                                <td>${l.size_mb} MB</td>
                                <td>${new Date(l.modified_at).toLocaleString()}</td>
                            </tr>
                        `).join('');
                    } catch (e) {
                        showResult('Error cargando logs: ' + e.message, true);
                    }
                }
                
                // Cargar datos al iniciar
                loadBackups();
                loadLogs();
            </script>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Verificación de estado del sistema"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            campaigns_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM physical_devices")
            devices_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scans")
            scans_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT client) FROM campaigns")
            clients_count = cursor.fetchone()[0]
        
        # Info de backups y logs
        backup_info = get_backup_info()
        logs_info = get_logs_info()
        
        return {
            "status": "healthy",
            "version": "2.7.2",
            "database": "connected",
            "stats": {
                "campaigns": campaigns_count,
                "devices": devices_count,
                "scans": scans_count,
                "clients": clients_count
            },
            "backups": {
                "total": backup_info["total_backups"],
                "size_mb": backup_info["total_size_mb"]
            },
            "logs": {
                "total": logs_info["total_logs"],
                "size_mb": logs_info["total_size_mb"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# ================================
# ENDPOINT DE TRACKING PRINCIPAL
# ================================

@app.get("/track")
async def track_qr_scan(request: Request, background_tasks: BackgroundTasks):
    """Endpoint principal de tracking de QR"""
    try:
        # Obtener parámetros de la URL
        params = dict(request.query_params)
        
        # Parámetros requeridos
        campaign_code = params.get("campaign")
        if not campaign_code:
            raise HTTPException(status_code=400, detail="Parámetro 'campaign' requerido")
        
        # Parámetros opcionales
        client = params.get("client", "")
        destination = params.get("destination", "")
        device_id = params.get("device_id", "")
        device_name = params.get("device_name", "")
        location = params.get("location", "")
        venue = params.get("venue", "")
        
        # Capturar parámetros UTM para tracking de marketing
        utm_source = params.get("utm_source", "")
        utm_medium = params.get("utm_medium", "")
        utm_campaign = params.get("utm_campaign", "")
        utm_term = params.get("utm_term", "")
        utm_content = params.get("utm_content", "")
        
        # Generar session_id único
        session_id = str(uuid.uuid4())
        
        # Detectar información del dispositivo del usuario
        user_agent = request.headers.get("User-Agent", "")
        client_ip = get_client_ip(request)
        
        # Buscar información de la campaña en la base de datos
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT destination, client FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            result = cursor.fetchone()
            if result:
                if not destination:
                    destination = result["destination"]
                if not client:
                    client = result["client"]
        
        # Si aún no hay destino, usar uno por defecto
        if not destination:
            destination = f"https://google.com/search?q={campaign_code}"
        
        # Lanzar procesamiento analítico en segundo plano para no bloquear al usuario
        background_tasks.add_task(
            process_scan_background,
            campaign_code, client, destination, device_id, device_name,
            location, venue, user_agent, client_ip, session_id,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content
        )
        
        # Redirigir a la página de tracking intermedia para recolectar datos avanzados
        from urllib.parse import urlencode, quote
        tracking_params = {
            "campaign": campaign_code,
            "client": client,
            "destination": destination,
            "device_id": device_id,
            "device_name": device_name,
            "location": location,
            "venue": venue,
            "session_id": session_id
        }
        tracking_url = f"/tracking?{urlencode({k: v for k, v in tracking_params.items() if v}, quote_via=quote)}"
        
        return RedirectResponse(url=tracking_url, status_code=307)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en tracking: {e}")
        return RedirectResponse(url=f"https://google.com/search?q={campaign_code}", status_code=302)

def process_scan_background(campaign_code: str, client: str, destination: str, 
                          device_id: str, device_name: str, location: str, venue: str, 
                          user_agent: str, client_ip: str, session_id: str,
                          utm_source: str, utm_medium: str, utm_campaign: str, 
                          utm_term: str, utm_content: str):
    """
    Procesa y guarda los datos analíticos del escaneo en segundo plano (Zero Latency)
    """
    try:
        # Detectar información del dispositivo
        device_info = detect_device_info(user_agent)
        
        # Detectar operadora/ISP a través de ip-api
        isp_carrier = "Unknown"
        if client_ip and client_ip not in ("127.0.0.1", "::1", "localhost", ""):
            try:
                import httpx
                with httpx.Client(timeout=2.0) as http_client:
                    resp = http_client.get(f"http://ip-api.com/json/{client_ip}?fields=isp,org")
                    if resp.status_code == 200:
                        data = resp.json()
                        isp_carrier = data.get("isp") or data.get("org") or "Unknown"
            except Exception as e:
                logger.warning(f"Error detectando ISP: {e}")
        
        # Registrar el escaneo en la base de datos
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scans (
                    campaign_code, client, destination, device_id, device_name, 
                    location, venue, user_device_type, browser, operating_system, 
                    user_agent, ip_address, session_id, scan_timestamp,
                    utm_source, utm_medium, utm_campaign, utm_term, utm_content,
                    device_brand, device_model, isp_carrier
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                campaign_code, client, destination, device_id, device_name,
                location, venue, device_info["device_type"], device_info["browser"],
                device_info["operating_system"], user_agent, client_ip, session_id,
                datetime.now().isoformat(),
                utm_source, utm_medium, utm_campaign, utm_term, utm_content,
                device_info.get("device_brand", "Unknown"), device_info.get("device_model", "Unknown"),
                isp_carrier
            ))
            conn.commit()
            
        # Log del escaneo
        scans_logger.info(f"QR escaneado (Background): campaign={campaign_code}, client={client}, device={device_info['device_type']}, IP={client_ip}, session={session_id}")
        
    except Exception as e:
        logger.error(f"Error procesando escaneo en background: {e}")

# ================================
# APIs DE ADMINISTRACIÓN (BACKUPS/LOGS)
# ================================

@app.get("/api/admin/backups")
async def api_get_backups():
    """Obtener lista de backups"""
    return get_backup_info()

@app.post("/api/admin/backups")
async def api_create_backup(backup_request: Optional[BackupRequest] = None):
    """Crear backup manual"""
    try:
        backup_path = create_backup("manual")
        if backup_path:
            return {
                "success": True,
                "message": "Backup creado exitosamente",
                "backup_path": backup_path
            }
        else:
            return {"success": False, "error": "No se pudo crear el backup"}
    except Exception as e:
        logger.error(f"Error en API de backup: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/admin/backups/cleanup")
async def api_cleanup_backups():
    """Limpiar backups antiguos"""
    try:
        deleted = cleanup_old_backups()
        return {
            "success": True,
            "message": "Limpieza completada",
            "deleted": deleted
        }
    except Exception as e:
        logger.error(f"Error en limpieza de backups: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/admin/backups/restore")
async def api_restore_backup(restore_request: RestoreRequest):
    """Restaurar un backup"""
    try:
        if not restore_request.confirm:
            return {
                "success": False,
                "error": "Debe confirmar la restauración (confirm=true)"
            }
        
        if restore_backup(restore_request.backup_filename):
            return {
                "success": True,
                "message": f"Backup {restore_request.backup_filename} restaurado exitosamente"
            }
        else:
            return {"success": False, "error": "No se pudo restaurar el backup"}
    except Exception as e:
        logger.error(f"Error restaurando backup: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/admin/logs")
async def api_get_logs():
    """Obtener información de logs"""
    return get_logs_info()

@app.get("/api/admin/logs/{filename}")
async def api_get_log_content(filename: str, lines: int = 100):
    """Obtener las últimas líneas de un archivo de log"""
    try:
        log_path = os.path.join(LOGS_DIR, filename)
        
        if not os.path.exists(log_path):
            return {"success": False, "error": "Archivo no encontrado"}
        
        # Leer últimas líneas
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
        
        return {
            "success": True,
            "filename": filename,
            "total_lines": len(all_lines),
            "returned_lines": len(last_lines),
            "content": last_lines
        }
    except Exception as e:
        logger.error(f"Error leyendo log: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE CAMPAÑAS
# ================================

@app.get("/api/campaigns")
async def get_campaigns():
    """Obtener todas las campañas"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM campaigns 
                ORDER BY created_at DESC
            """)
            campaigns = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "campaigns": campaigns,
            "total": len(campaigns)
        }
    except Exception as e:
        logger.error(f"Error obteniendo campañas: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/campaigns")
async def create_campaign(campaign: CampaignCreate):
    """Crear nueva campaña"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO campaigns (campaign_code, client, destination, description, active)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                campaign.campaign_code, campaign.client, campaign.destination,
                campaign.description, campaign.active
            ))
            conn.commit()
            cursor.execute("SELECT lastval()")
            campaign_id = cursor.fetchone()['lastval']
            
            # Obtener la campaña creada
            cursor.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
            new_campaign = dict(cursor.fetchone())
        
        logger.info(f"Campaña creada: {campaign.campaign_code}")
        return {
            "success": True,
            "message": "Campaña creada exitosamente",
            "campaign": new_campaign
        }
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "duplicate" in str(e).lower() or "IntegrityError" in str(type(e)):
            return {"success": False, "error": "El código de campaña ya existe"}
        logger.error(f"Error creando campaña: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/campaigns/{campaign_code}")
async def update_campaign(campaign_code: str, campaign_update: CampaignUpdate):
    """Actualizar campaña existente"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la campaña existe
            cursor.execute("SELECT id FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            if not cursor.fetchone():
                return {"success": False, "error": "Campaña no encontrada"}
            
            # Construir query de actualización dinámicamente
            update_fields = []
            values = []
            
            if campaign_update.client is not None:
                update_fields.append("client = %s")
                values.append(campaign_update.client)
            if campaign_update.destination is not None:
                update_fields.append("destination = %s")
                values.append(campaign_update.destination)
            if campaign_update.description is not None:
                update_fields.append("description = %s")
                values.append(campaign_update.description)
            if campaign_update.active is not None:
                update_fields.append("active = %s")
                values.append(campaign_update.active)
            
            if not update_fields:
                return {"success": False, "error": "No hay campos para actualizar"}
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(campaign_code)
            
            query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE campaign_code = %s"
            cursor.execute(query, values)
            conn.commit()
        
        logger.info(f"Campaña actualizada: {campaign_code}")
        return {"success": True, "message": "Campaña actualizada exitosamente"}
    except Exception as e:
        logger.error(f"Error actualizando campaña: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/campaigns/{campaign_code}/pause")
async def pause_campaign(campaign_code: str):
    """Pausar o reanudar una campaña (toggle de estado active)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener estado actual
            cursor.execute("SELECT active, client FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            result = cursor.fetchone()
            
            if not result:
                return {"success": False, "error": "Campaña no encontrada"}
            
            current_active = result["active"]
            client = result["client"]
            new_active = 0 if current_active else 1
            
            # Cambiar estado
            cursor.execute("""
                UPDATE campaigns 
                SET active = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE campaign_code = %s
            """, (new_active, campaign_code))
            conn.commit()
        
        status = "reanudada" if new_active else "pausada"
        logger.info(f"Campaña {status}: {campaign_code}")
        return {
            "success": True, 
            "message": f"Campaña '{client}' {status} exitosamente",
            "active": bool(new_active)
        }
    except Exception as e:
        logger.error(f"Error pausando campaña: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/campaigns/{campaign_code}/tracking-url")
async def get_campaign_tracking_url(campaign_code: str, request: Request):
    """Obtener la URL de tracking completa para una campaña (para copiar o generar QR)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT campaign_code, client, destination, description 
                FROM campaigns 
                WHERE campaign_code = %s
            """, (campaign_code,))
            campaign = cursor.fetchone()
            
            if not campaign:
                return {"success": False, "error": "Campaña no encontrada"}
            
            campaign_data = dict(campaign)
        
        # Construir la URL base del servidor
        # Usar el host de la request para obtener la URL correcta
        scheme = request.headers.get("X-Forwarded-Proto", "http")
        host = request.headers.get("Host", "localhost:8000")
        base_url = f"{scheme}://{host}"
        
        # Construir la URL de tracking con todos los parámetros
        from urllib.parse import urlencode, quote
        
        params = {
            "campaign": campaign_data["campaign_code"],
            "client": campaign_data["client"] or "",
            "destination": campaign_data["destination"] or ""
        }
        
        # URL de tracking completa
        tracking_url = f"{base_url}/track?{urlencode(params, quote_via=quote)}"
        
        logger.info(f"URL de tracking generada para campaña: {campaign_code}")
        return {
            "success": True,
            "campaign_code": campaign_data["campaign_code"],
            "client": campaign_data["client"],
            "destination": campaign_data["destination"],
            "tracking_url": tracking_url,
            "base_url": base_url
        }
    except Exception as e:
        logger.error(f"Error obteniendo URL de tracking: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/campaigns/{campaign_code}")
async def delete_campaign(campaign_code: str):
    """Eliminar campaña completamente de la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la campaña existe y obtener información
            cursor.execute("SELECT client, description FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            campaign_row = cursor.fetchone()
            
            if not campaign_row:
                return {"success": False, "error": "Campaña no encontrada"}
            
            client = campaign_row["client"]
            
            # Eliminar la campaña completamente
            cursor.execute("DELETE FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "No se pudo eliminar la campaña"}
            
            conn.commit()
        
        logger.info(f"Campaña eliminada permanentemente: {campaign_code} - {client}")
        return {
            "success": True, 
            "message": f"Campaña '{client}' eliminada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error eliminando campaña: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE DISPOSITIVOS
# ================================

@app.get("/api/devices")
async def get_devices():
    """Obtener todos los dispositivos"""
    try:
        logger.info("Obteniendo dispositivos...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM physical_devices 
                ORDER BY created_at DESC
            """)
            devices = [dict(row) for row in cursor.fetchall()]
        
        logger.info(f"Dispositivos obtenidos: {len(devices)}")
        return {
            "success": True,
            "devices": devices,
            "total": len(devices)
        }
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Obtener un dispositivo específico"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = %s", (device_id,))
            device_row = cursor.fetchone()
            
            if not device_row:
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            device = dict(device_row)
        
        return {
            "success": True,
            "device": device
        }
    except Exception as e:
        logger.error(f"Error obteniendo dispositivo: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/devices")
async def create_device(device: DeviceCreate):
    """Crear nuevo dispositivo"""
    try:
        logger.info(f"Creando dispositivo: {device}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el device_id no exista ya
            cursor.execute("SELECT id FROM physical_devices WHERE device_id = %s", (device.device_id,))
            if cursor.fetchone():
                logger.warning(f"Dispositivo ya existe: {device.device_id}")
                return {"success": False, "error": "El ID del dispositivo ya existe"}
            
            cursor.execute("""
                INSERT INTO physical_devices (device_id, device_name, device_type, location, venue, description, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                device.device_id, device.device_name, device.device_type,
                device.location, device.venue, device.description, device.active
            ))
            conn.commit()
            cursor.execute("SELECT lastval()")
            device_pk_id = cursor.fetchone()['lastval']
            
            # Obtener el dispositivo creado
            cursor.execute("SELECT * FROM physical_devices WHERE id = %s", (device_pk_id,))
            new_device = dict(cursor.fetchone())
        
        logger.info(f"Dispositivo creado exitosamente: {device.device_id}")
        return {
            "success": True,
            "message": "Dispositivo creado exitosamente",
            "device": new_device
        }
    except Exception as e:
        # Check if it's an integrity error from psycopg2 or sqlite3
        if "IntegrityError" in type(e).__name__:
            logger.error(f"Error de integridad: {e}")
            return {"success": False, "error": "El ID del dispositivo ya existe"}
            
        logger.error(f"Error creando dispositivo: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/devices/{device_id}")
async def update_device(device_id: str, device_update: DeviceUpdate):
    """Actualizar dispositivo existente"""
    try:
        logger.info(f"Actualizando dispositivo: {device_id} con datos: {device_update}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el dispositivo existe
            cursor.execute("SELECT id FROM physical_devices WHERE device_id = %s", (device_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            # Construir query de actualización dinámicamente
            update_fields = []
            values = []
            
            if device_update.device_name is not None:
                update_fields.append("device_name = %s")
                values.append(device_update.device_name)
            if device_update.device_type is not None:
                update_fields.append("device_type = %s")
                values.append(device_update.device_type)
            if device_update.location is not None:
                update_fields.append("location = %s")
                values.append(device_update.location)
            if device_update.venue is not None:
                update_fields.append("venue = %s")
                values.append(device_update.venue)
            if device_update.description is not None:
                update_fields.append("description = %s")
                values.append(device_update.description)
            if device_update.active is not None:
                update_fields.append("active = %s")
                values.append(device_update.active)
            
            if not update_fields:
                return {"success": False, "error": "No hay campos para actualizar"}
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(device_id)
            
            query = f"UPDATE physical_devices SET {', '.join(update_fields)} WHERE device_id = %s"
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "No se pudo actualizar el dispositivo"}
            
            # Obtener el dispositivo actualizado
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = %s", (device_id,))
            updated_device = dict(cursor.fetchone())
        
        logger.info(f"Dispositivo actualizado: {device_id}")
        return {
            "success": True, 
            "message": "Dispositivo actualizado exitosamente",
            "device": updated_device
        }
    except Exception as e:
        logger.error(f"Error actualizando dispositivo: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str):
    """Eliminar dispositivo completamente"""
    try:
        logger.info(f"Eliminando dispositivo: {device_id}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el dispositivo existe y obtener información
            cursor.execute("SELECT device_name FROM physical_devices WHERE device_id = %s", (device_id,))
            device_row = cursor.fetchone()
            if not device_row:
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            device_name = device_row["device_name"]
            
            # Eliminar el dispositivo completamente
            cursor.execute("DELETE FROM physical_devices WHERE device_id = %s", (device_id,))
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "No se pudo eliminar el dispositivo"}
            
            conn.commit()
        
        logger.info(f"Dispositivo eliminado: {device_id} - {device_name}")
        return {
            "success": True, 
            "message": f"Dispositivo '{device_name}' eliminado exitosamente"
        }
    except Exception as e:
        logger.error(f"Error eliminando dispositivo: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE CLIENTES
# ================================

@app.get("/api/clients")
async def get_clients():
    """Obtener lista de clientes únicos con sus estadísticas"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.client,
                    COUNT(DISTINCT c.id) as campaigns_count,
                    COALESCE(SUM(scan_counts.scan_count), 0) as scans_count,
                    MAX(scan_counts.last_scan) as last_scan
                FROM campaigns c
                LEFT JOIN (
                    SELECT campaign_code, COUNT(*) as scan_count, MAX(scan_timestamp) as last_scan
                    FROM scans
                    GROUP BY campaign_code
                ) scan_counts ON c.campaign_code = scan_counts.campaign_code
                WHERE c.client IS NOT NULL AND c.client != ''
                GROUP BY c.client
                ORDER BY scans_count DESC
            """)
            clients = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "clients": clients,
            "total": len(clients)
        }
    except Exception as e:
        logger.error(f"Error obteniendo clientes: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/client/{client_name}")
async def get_client_analytics(client_name: str):
    """Obtener analytics completos de un cliente específico"""
    try:
        # Decodificar nombre del cliente (puede venir URL-encoded)
        client_name = unquote(client_name)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el cliente existe
            cursor.execute("SELECT COUNT(*) FROM campaigns WHERE client = %s", (client_name,))
            if cursor.fetchone()[0] == 0:
                return {"success": False, "error": "Cliente no encontrado"}
            
            # Estadísticas generales del cliente
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT c.id) as total_campaigns,
                    COUNT(DISTINCT CASE WHEN c.active = TRUE THEN c.id END) as active_campaigns,
                    COALESCE(COUNT(s.id), 0) as total_scans,
                    COALESCE(COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END), 0) as completed_redirects,
                    ROUND(COALESCE(AVG(s.duration_seconds), 0)::numeric, 2) as avg_duration,
                    COUNT(DISTINCT s.ip_address) as unique_visitors,
                    COUNT(DISTINCT s.device_id) as unique_devices,
                    MIN(s.scan_timestamp) as first_scan,
                    MAX(s.scan_timestamp) as last_scan
                FROM campaigns c
                LEFT JOIN scans s ON c.campaign_code = s.campaign_code
                WHERE c.client = %s
            """, (client_name,))
            stats = dict(cursor.fetchone())
            
            # Calcular tasa de conversión
            if stats["total_scans"] > 0:
                stats["conversion_rate"] = round((stats["completed_redirects"] / stats["total_scans"]) * 100, 2)
            else:
                stats["conversion_rate"] = 0
            
            # Campañas del cliente con sus estadísticas
            cursor.execute("""
                SELECT 
                    c.campaign_code,
                    c.destination,
                    c.description,
                    c.active,
                    c.created_at,
                    COUNT(s.id) as scans,
                    COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds)::numeric, 2) as avg_duration
                FROM campaigns c
                LEFT JOIN scans s ON c.campaign_code = s.campaign_code
                WHERE c.client = %s
                GROUP BY c.id
                ORDER BY scans DESC
            """, (client_name,))
            campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por día (últimos 30 días)
            cursor.execute("""
                SELECT 
                    CAST(s.scan_timestamp AS DATE) as date,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END) as completions
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s AND s.scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
                GROUP BY CAST(s.scan_timestamp AS DATE)
                ORDER BY date
            """, (client_name,))
            daily_activity = [dict(row) for row in cursor.fetchall()]
            
            # Top dispositivos físicos
            cursor.execute("""
                SELECT 
                    s.device_id,
                    s.device_name,
                    s.location,
                    s.venue,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END) as completions
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s AND s.device_id IS NOT NULL AND s.device_id != ''
                GROUP BY s.device_id, s.device_name, s.location, s.venue
                ORDER BY scans DESC
                LIMIT 10
            """, (client_name,))
            devices = [dict(row) for row in cursor.fetchall()]
            
            # Distribución de tipos de dispositivos de usuarios
            cursor.execute("""
                SELECT 
                    s.user_device_type as device_type,
                    COUNT(*) as count
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s
                GROUP BY s.user_device_type
                ORDER BY count DESC
            """, (client_name,))
            device_types = [dict(row) for row in cursor.fetchall()]

            # Distribución de marcas
            cursor.execute("""
                SELECT 
                    COALESCE(NULLIF(s.device_brand, ''), 'Desconocida') as brand,
                    COUNT(*) as count
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s
                GROUP BY COALESCE(NULLIF(s.device_brand, ''), 'Desconocida')
                ORDER BY count DESC
            """, (client_name,))
            device_brands = [dict(row) for row in cursor.fetchall()]

            # Distribución de navegadores
            cursor.execute("""
                SELECT 
                    COALESCE(NULLIF(s.browser, ''), 'Desconocido') as browser,
                    COUNT(*) as count
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s
                GROUP BY COALESCE(NULLIF(s.browser, ''), 'Desconocido')
                ORDER BY count DESC
            """, (client_name,))
            browsers = [dict(row) for row in cursor.fetchall()]

            # Sedes / Venues
            cursor.execute("""
                SELECT 
                    COALESCE(NULLIF(s.venue, ''), NULLIF(s.location, ''), 'Desconocida') as venue,
                    COUNT(*) as scans,
                    COUNT(DISTINCT s.ip_address) as unique_visitors
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s
                GROUP BY COALESCE(NULLIF(s.venue, ''), NULLIF(s.location, ''), 'Desconocida')
                ORDER BY scans DESC
            """, (client_name,))
            venues = [dict(row) for row in cursor.fetchall()]

            # Últimos escaneos
            cursor.execute("""
                SELECT 
                    s.scan_timestamp, s.campaign_code, s.device_id, s.device_name, 
                    s.location, s.venue, s.user_device_type, s.browser, s.operating_system, 
                    s.duration_seconds, s.redirect_completed, s.device_brand, s.device_model
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = %s
                ORDER BY s.scan_timestamp DESC
                LIMIT 500
            """, (client_name,))
            recent_scans = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "client": client_name,
            "stats": stats,
            "campaigns": campaigns,
            "daily_activity": daily_activity,
            "devices": devices,
            "device_types": device_types,
            "device_brands": device_brands,
            "browsers": browsers,
            "venues": venues,
            "recent_scans": recent_scans
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics de cliente: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE TRACKING
# ================================

@app.post("/api/track/device-data")
async def track_device_data(device_data: DeviceDataUpdate):
    """Registrar datos adicionales del dispositivo del usuario"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scans SET
                    screen_resolution = COALESCE(%s, screen_resolution),
                    viewport_size = COALESCE(%s, viewport_size),
                    timezone = COALESCE(%s, timezone),
                    language = COALESCE(%s, language),
                    platform = COALESCE(%s, platform),
                    connection_type = COALESCE(%s, connection_type),
                    cpu_cores = COALESCE(%s, cpu_cores),
                    device_pixel_ratio = COALESCE(%s, device_pixel_ratio),
                    device_brand = COALESCE(NULLIF(%s, ''), device_brand),
                    device_model = COALESCE(NULLIF(%s, ''), device_model)
                WHERE session_id = %s
            """, (
                device_data.screen_resolution,
                device_data.viewport_size,
                device_data.timezone,
                device_data.language,
                device_data.platform,
                device_data.connection_type,
                device_data.cpu_cores,
                device_data.device_pixel_ratio,
                device_data.ua_brand,
                device_data.ua_model,
                device_data.session_id
            ))
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "Session no encontrada"}
        
        scans_logger.info(f"Datos de dispositivo actualizados: session={device_data.session_id}, cores={device_data.cpu_cores}, dpr={device_data.device_pixel_ratio}")
        return {"success": True, "message": "Datos actualizados"}
    except Exception as e:
        logger.error(f"Error actualizando datos del dispositivo: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/track/complete")
async def complete_tracking(request: Request):
    """Marcar tracking como completado"""
    try:
        try:
            data = await request.json()
        except:
            # Fallback for navigator.sendBeacon returning plain text stringified JSON
            import json
            raw_body = await request.body()
            data = json.loads(raw_body.decode('utf-8'))
            
        session_id = data.get("session_id")
        completion_time = data.get("completion_time")
        
        if not session_id:
            return {"success": False, "error": "session_id requerido"}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Calcular duración si es posible
            cursor.execute("""
                SELECT id, scan_timestamp FROM scans 
                WHERE session_id = %s
                ORDER BY scan_timestamp DESC LIMIT 1
            """, (session_id,))
            result = cursor.fetchone()
            
            duration = None
            if result and completion_time:
                try:
                    start_time = datetime.fromisoformat(result["scan_timestamp"].replace("Z", "+00:00"))
                    end_time = datetime.fromisoformat(completion_time.replace("Z", "+00:00"))
                    duration = (end_time - start_time).total_seconds()
                except:
                    pass
            
            # Actualizar el registro
            if result:
                scan_id = result["id"]
                cursor.execute("""
                    UPDATE scans 
                    SET redirect_completed = TRUE, 
                        redirect_timestamp = CURRENT_TIMESTAMP,
                        duration_seconds = %s
                    WHERE id = %s AND session_id = %s
                """, (duration, scan_id, session_id))
                conn.commit()
                scans_logger.info(f"Tracking completado: session={session_id}, duration={duration}s")
            else:
                return {"success": False, "error": "Session no encontrada"}
        
        return {"success": True, "message": "Tracking completado"}
    except Exception as e:
        logger.error(f"Error completando tracking: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE ANALYTICS
# ================================

@app.get("/api/analytics/device-hierarchy")
async def get_device_hierarchy():
    """Obtener jerarquía de dispositivos (Tipo -> Marca -> Modelo -> Navegador)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COALESCE(user_device_type, 'Unknown') as device_type,
                    COALESCE(device_brand, 'Unknown') as device_brand,
                    COALESCE(device_model, 'Unknown') as device_model,
                    COALESCE(browser, 'Unknown') as browser,
                    COUNT(*) as count
                FROM scans
                GROUP BY user_device_type, device_brand, device_model, browser
                ORDER BY count DESC
            """)
            
            rows = cursor.fetchall()
            
            hierarchy = {}
            for row in rows:
                dtype = row["device_type"]
                brand = row["device_brand"]
                model = row["device_model"]
                browser = row["browser"]
                count = row["count"]
                
                if dtype not in hierarchy:
                    hierarchy[dtype] = {"name": dtype, "count": 0, "brands": {}}
                hierarchy[dtype]["count"] += count
                
                if brand not in hierarchy[dtype]["brands"]:
                    hierarchy[dtype]["brands"][brand] = {"name": brand, "count": 0, "models": {}}
                hierarchy[dtype]["brands"][brand]["count"] += count
                
                if model not in hierarchy[dtype]["brands"][brand]["models"]:
                    hierarchy[dtype]["brands"][brand]["models"][model] = {"name": model, "count": 0, "browsers": {}}
                hierarchy[dtype]["brands"][brand]["models"][model]["count"] += count
                
                if browser not in hierarchy[dtype]["brands"][brand]["models"][model]["browsers"]:
                    hierarchy[dtype]["brands"][brand]["models"][model]["browsers"][browser] = {"name": browser, "count": 0}
                hierarchy[dtype]["brands"][brand]["models"][model]["browsers"][browser]["count"] += count
            
            def dict_to_sorted_list(d, children_key=None):
                result = list(d.values())
                result.sort(key=lambda x: x["count"], reverse=True)
                if children_key:
                    for item in result:
                        if children_key in item:
                            next_key = "models" if children_key == "brands" else ("browsers" if children_key == "models" else None)
                            item[children_key] = dict_to_sorted_list(item[children_key], next_key)
                return result
                
            sorted_hierarchy = dict_to_sorted_list(hierarchy, "brands")
            
            return {
                "success": True,
                "hierarchy": sorted_hierarchy
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo jerarquía de dispositivos: {e}")
        return {"success": False, "error": str(e)}
@app.get("/api/analytics/device-hierarchy/client/{client_name}")
async def get_client_device_hierarchy(client_name: str):
    """Obtener jerarquía de dispositivos para un cliente específico"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COALESCE(user_device_type, 'Unknown') as device_type,
                    COALESCE(device_brand, 'Unknown') as device_brand,
                    COALESCE(device_model, 'Unknown') as device_model,
                    COALESCE(browser, 'Unknown') as browser,
                    COUNT(*) as count
                FROM scans
                WHERE client = %s
                GROUP BY user_device_type, device_brand, device_model, browser
                ORDER BY count DESC
            """, (client_name,))
            
            rows = cursor.fetchall()
            
            hierarchy = {}
            for row in rows:
                dtype = row["device_type"]
                brand = row["device_brand"]
                model = row["device_model"]
                browser = row["browser"]
                count = row["count"]
                
                if dtype not in hierarchy:
                    hierarchy[dtype] = {"name": dtype, "count": 0, "brands": {}}
                hierarchy[dtype]["count"] += count
                
                if brand not in hierarchy[dtype]["brands"]:
                    hierarchy[dtype]["brands"][brand] = {"name": brand, "count": 0, "models": {}}
                hierarchy[dtype]["brands"][brand]["count"] += count
                
                if model not in hierarchy[dtype]["brands"][brand]["models"]:
                    hierarchy[dtype]["brands"][brand]["models"][model] = {"name": model, "count": 0, "browsers": {}}
                hierarchy[dtype]["brands"][brand]["models"][model]["count"] += count
                
                if browser not in hierarchy[dtype]["brands"][brand]["models"][model]["browsers"]:
                    hierarchy[dtype]["brands"][brand]["models"][model]["browsers"][browser] = {"name": browser, "count": 0}
                hierarchy[dtype]["brands"][brand]["models"][model]["browsers"][browser]["count"] += count
            
            def dict_to_sorted_list(d, children_key=None):
                result = list(d.values())
                result.sort(key=lambda x: x["count"], reverse=True)
                if children_key:
                    for item in result:
                        if children_key in item:
                            next_key = "models" if children_key == "brands" else ("browsers" if children_key == "models" else None)
                            item[children_key] = dict_to_sorted_list(item[children_key], next_key)
                return result
                
            sorted_hierarchy = dict_to_sorted_list(hierarchy, "brands")
            
            return {
                "success": True,
                "client": client_name,
                "hierarchy": sorted_hierarchy
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo jerarquía de dispositivos por cliente: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Obtener datos completos para el dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales mejoradas
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM campaigns WHERE active = TRUE) as active_campaigns,
                    (SELECT COUNT(*) FROM physical_devices WHERE active = TRUE) as active_devices,
                    (SELECT COUNT(*) FROM scans) as total_scans,
                    (SELECT COUNT(*) FROM scans WHERE redirect_completed = TRUE) as completed_redirects,
                    (SELECT COUNT(DISTINCT client) FROM campaigns WHERE client != '') as total_clients,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours') as scans_24h,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days') as scans_7d,
                    (SELECT COUNT(DISTINCT ip_address) FROM scans) as unique_visitors
            """)
            stats = dict(cursor.fetchone())
            
            # Estadísticas por campaña
            cursor.execute("""
                SELECT 
                    s.campaign_code as campaign,
                    s.client,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds)::numeric, 2) as avg_duration,
                    MAX(s.scan_timestamp) as last_scan
                FROM scans s
                GROUP BY s.campaign_code, s.client
                ORDER BY scans DESC
                LIMIT 10
            """)
            campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Dispositivos de usuarios con porcentaje
            cursor.execute("""
                SELECT user_device_type as device_type, browser, operating_system, COUNT(*) as count
                FROM scans 
                WHERE user_device_type IS NOT NULL
                GROUP BY user_device_type, browser, operating_system
                ORDER BY count DESC
                LIMIT 10
            """)
            user_devices = [dict(row) for row in cursor.fetchall()]
            
            # Calcular porcentajes
            total_device_scans = sum(d["count"] for d in user_devices)
            for device in user_devices:
                device["percentage"] = round((device["count"] / total_device_scans * 100), 1) if total_device_scans > 0 else 0
            
            # Dispositivos físicos
            cursor.execute("""
                SELECT 
                    pd.device_id,
                    pd.device_name,
                    pd.location,
                    pd.venue,
                    pd.device_type,
                    COUNT(s.id) as scans,
                    COUNT(CASE WHEN s.redirect_completed = TRUE THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds)::numeric, 2) as avg_duration
                FROM physical_devices pd
                LEFT JOIN scans s ON pd.device_id = s.device_id
                WHERE pd.active = TRUE
                GROUP BY pd.id
                ORDER BY scans DESC
                LIMIT 10
            """)
            physical_devices = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por horas (últimas 24 horas)
            cursor.execute("""
                SELECT 
                    EXTRACT(HOUR FROM scan_timestamp)::INTEGER as hour,
                    COUNT(*) as scans
                FROM scans
                WHERE scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                GROUP BY EXTRACT(HOUR FROM scan_timestamp)
                ORDER BY hour
            """)
            hourly = [dict(row) for row in cursor.fetchall()]
            
            # Top venues
            cursor.execute("""
                SELECT 
                    venue,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN redirect_completed = TRUE THEN 1 END) as completions,
                    COUNT(DISTINCT device_id) as devices_count
                FROM scans 
                WHERE venue IS NOT NULL AND venue != ''
                GROUP BY venue
                ORDER BY scans DESC
                LIMIT 5
            """)
            venues = [dict(row) for row in cursor.fetchall()]
            
            # Top browsers
            cursor.execute("""
                SELECT browser, COUNT(*) as count
                FROM scans 
                WHERE browser IS NOT NULL AND browser != 'Unknown'
                GROUP BY browser
                ORDER BY count DESC
                LIMIT 5
            """)
            browsers = [dict(row) for row in cursor.fetchall()]
            
            # Top operating systems
            cursor.execute("""
                SELECT operating_system, COUNT(*) as count
                FROM scans 
                WHERE operating_system IS NOT NULL AND operating_system != 'Unknown'
                GROUP BY operating_system
                ORDER BY count DESC
                LIMIT 5
            """)
            operating_systems = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "stats": stats,
            "campaigns": campaigns,
            "user_devices": user_devices,
            "physical_devices": physical_devices,
            "hourly": hourly,
            "venues": venues,
            "browsers": browsers,
            "operating_systems": operating_systems
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/analytics/qr-generated")
async def log_qr_generation(qr_log: QRGenerationLog, request: Request):
    """Registrar generación de QR para analytics"""
    try:
        generated_by = qr_log.generated_by or get_client_ip(request)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO qr_generations (campaign_id, physical_device_id, qr_size, generated_by)
                VALUES (%s, %s, %s, %s)
            """, (
                qr_log.campaign_id, qr_log.physical_device_id, 
                qr_log.qr_size, generated_by
            ))
            conn.commit()
        
        return {"success": True, "message": "Generación de QR registrada"}
    except Exception as e:
        logger.error(f"Error registrando generación de QR: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE GENERACIÓN DE CÓDIGOS QR
# ================================

def generate_qr_image(data: str, size: int = 300, error_correction: str = "M", 
                      color_dark: str = "#000000", color_light: str = "#FFFFFF",
                      logo_mode: str = "default",
                      brand_logo_base64: Optional[str] = None) -> Optional[str]:
    """
    Genera una imagen QR y la devuelve como base64
    
    Args:
        data: URL o texto a codificar en el QR
        size: Tamaño en píxeles (ancho y alto)
        error_correction: Nivel de corrección de errores (L, M, Q, H)
        color_dark: Color de los módulos oscuros (hex)
        color_light: Color del fondo (hex)
        logo_mode: Modo de logo
        brand_logo_base64: Base64 subido por el usuario
    
    Returns:
        Imagen en formato base64 o None si hay error
    """
    if not QR_LIBRARY_AVAILABLE:
        logger.error("Biblioteca qrcode no disponible")
        return None
    
    try:
        # Forzar alta corrección si se usará logo central
        if logo_mode in ["default", "brand_only", "brand_full"]:
            error_correction = "H"
            
        error_levels = {
            "L": ERROR_CORRECT_L,  # ~7% corrección
            "M": ERROR_CORRECT_M,  # ~15% corrección
            "Q": ERROR_CORRECT_Q,  # ~25% corrección
            "H": ERROR_CORRECT_H   # ~30% corrección
        }
        error_level = error_levels.get(error_correction.upper(), ERROR_CORRECT_M)
        
        qr = qrcode.QRCode(
            version=None,
            error_correction=error_level,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        fill_color = hex_to_rgb(color_dark)
        back_color = hex_to_rgb(color_light)
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        if img.size[0] != size:
            img = img.resize((size, size), Image.LANCZOS if PIL_AVAILABLE else Image.NEAREST)
            
        # Determinar qué base64 usar
        center_logo_b64 = None
        banner_b64 = None
        if logo_mode == "default":
            center_logo_b64 = CENTAURO_LOGO_BASE64
        elif logo_mode == "brand_only":
            center_logo_b64 = brand_logo_base64
        elif logo_mode == "brand_full":
            center_logo_b64 = brand_logo_base64
            banner_b64 = CENTAURO_BANNER_BASE64
            
        if center_logo_b64 and PIL_AVAILABLE:
            try:
                if ',' in center_logo_b64:
                    center_logo_b64 = center_logo_b64.split(',')[1]
                
                logo_bytes = base64.b64decode(center_logo_b64)
                logo_img = Image.open(io.BytesIO(logo_bytes))
                
                if logo_img.mode != 'RGBA':
                    logo_img = logo_img.convert('RGBA')
                
                qr_width, qr_height = img.size
                logo_max_size = int(min(qr_width, qr_height) * 0.3)
                
                logo_width, logo_height = logo_img.size
                ratio = min(logo_max_size / logo_width, logo_max_size / logo_height)
                new_size = (int(logo_width * ratio), int(logo_height * ratio))
                
                logo_img = logo_img.resize(new_size, Image.LANCZOS)
                
                pos_x = (qr_width - new_size[0]) // 2
                pos_y = (qr_height - new_size[1]) // 2
                
                # Crear un fondo blanco con un pequeño margen para el logo
                padding = 10
                bg_size = (new_size[0] + padding * 2, new_size[1] + padding * 2)
                bg_pos_x = pos_x - padding
                bg_pos_y = pos_y - padding
                
                img = img.convert('RGBA')
                
                # Dibujar rectángulo blanco
                draw = ImageDraw.Draw(img)
                draw.rectangle(
                    [bg_pos_x, bg_pos_y, bg_pos_x + bg_size[0], bg_pos_y + bg_size[1]],
                    fill=(255, 255, 255, 255)
                )
                
                img.paste(logo_img, (pos_x, pos_y), logo_img)
            except Exception as e:
                logger.error(f"Error superponiendo logo en QR: {str(e)}")

        if banner_b64 and PIL_AVAILABLE:
            try:
                if ',' in banner_b64:
                    banner_b64 = banner_b64.split(',')[1]
                
                banner_bytes = base64.b64decode(banner_b64)
                banner_img = Image.open(io.BytesIO(banner_bytes))
                
                if banner_img.mode != 'RGBA':
                    banner_img = banner_img.convert('RGBA')
                
                qr_width, qr_height = img.size
                
                banner_width, banner_height = banner_img.size
                ratio = qr_width / banner_width
                new_banner_size = (int(banner_width * ratio), int(banner_height * ratio))
                banner_img = banner_img.resize(new_banner_size, Image.LANCZOS)
                
                padding_y = 10
                final_height = qr_height + new_banner_size[1] + padding_y
                
                final_img = Image.new('RGB', (qr_width, final_height), hex_to_rgb(color_light))
                
                img = img.convert('RGBA')
                final_img.paste(img, (0, 0), img)
                final_img.paste(banner_img, (0, qr_height + padding_y), banner_img)
                
                img = final_img
            except Exception as e:
                logger.error(f"Error superponiendo banner en QR: {str(e)}")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error generando imagen QR: {e}")
        return None

@app.post("/api/qr/generate")
async def generate_qr_from_campaign(qr_request: QRGenerateRequest, request: Request):
    """
    Generar código QR desde una campaña registrada
    
    Este endpoint genera un código QR que apunta a la URL de tracking
    de la campaña especificada.
    """
    try:
        # Verificar que la biblioteca está disponible
        if not QR_LIBRARY_AVAILABLE:
            return {
                "success": False, 
                "error": "Biblioteca de generación de QR no disponible. Instale: pip install qrcode[pil]"
            }
        
        # Obtener datos de la campaña
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, campaign_code, client, destination, active 
                FROM campaigns 
                WHERE campaign_code = %s
            """, (qr_request.campaign_code,))
            campaign = cursor.fetchone()
            
            if not campaign:
                return {"success": False, "error": f"Campaña '{qr_request.campaign_code}' no encontrada"}
            
            campaign_data = dict(campaign)
            
            if not campaign_data["active"]:
                return {"success": False, "error": "La campaña está pausada. Active la campaña para generar QR."}
            
            # Obtener datos del dispositivo si se especificó
            device_data = None
            if qr_request.device_id:
                cursor.execute("""
                    SELECT id, device_id, device_name, location, venue 
                    FROM physical_devices 
                    WHERE device_id = %s
                """, (qr_request.device_id,))
                device = cursor.fetchone()
                if device:
                    device_data = dict(device)
        
        # Construir URL de tracking
        # Usar base_url proporcionada o detectar desde headers
        if qr_request.base_url:
            # Limpiar la URL base (quitar trailing slash si existe)
            base_url = qr_request.base_url.rstrip('/')
        else:
            scheme = request.headers.get("X-Forwarded-Proto", "http")
            host = request.headers.get("Host", "localhost:8000")
            base_url = f"{scheme}://{host}"
        
        # Parámetros de la URL de tracking
        params = {
            "campaign": campaign_data["campaign_code"],
            "client": campaign_data["client"] or "",
            "destination": campaign_data["destination"] or ""
        }
        
        # Agregar parámetros del dispositivo si existe
        if device_data:
            params["device_id"] = device_data["device_id"]
            params["device_name"] = device_data.get("device_name", "")
            params["location"] = device_data.get("location", "")
            params["venue"] = device_data.get("venue", "")
        
        tracking_url = f"{base_url}/track?{urlencode(params, quote_via=quote)}"
        
        # Forzar alta corrección si hay logo
        error_correction = "M"
        if qr_request.brand_logo_base64:
            error_correction = "H"
            
        # Generar imagen QR
        qr_image = generate_qr_image(
            data=tracking_url,
            size=qr_request.size,
            error_correction=error_correction,
            color_dark=qr_request.color_dark,
            color_light=qr_request.color_light,
            logo_mode=qr_request.logo_mode,
            brand_logo_base64=qr_request.brand_logo_base64
        )
        
        if not qr_image:
            return {"success": False, "error": "Error generando imagen QR"}
        
        # Registrar generación para analytics
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qr_generations (campaign_id, physical_device_id, qr_size, generated_by)
                    VALUES (%s, %s, %s, %s)
                """, (
                    campaign_data["id"],
                    device_data["id"] if device_data else None,
                    qr_request.size,
                    get_client_ip(request)
                ))
                conn.commit()
        except Exception as log_error:
            logger.warning(f"No se pudo registrar generación de QR: {log_error}")
        
        logger.info(f"QR generado para campaña: {qr_request.campaign_code}, tamaño: {qr_request.size}px")
        
        return {
            "success": True,
            "qr_image": qr_image,
            "tracking_url": tracking_url,
            "campaign": {
                "code": campaign_data["campaign_code"],
                "client": campaign_data["client"],
                "destination": campaign_data["destination"]
            },
            "device": device_data,
            "size": qr_request.size,
            "format": qr_request.format,
            "logo_mode": qr_request.logo_mode,
            "filename_suffix": "_" + qr_request.logo_mode[:2].upper()
        }
        
    except Exception as e:
        logger.error(f"Error generando QR desde campaña: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/qr/generate-custom")
async def generate_custom_qr(qr_request: QRCustomRequest, request: Request):
    """
    Generar código QR personalizado desde una URL o texto
    
    Este endpoint genera un código QR para cualquier URL o texto
    proporcionado por el usuario.
    """
    try:
        # Verificar que la biblioteca está disponible
        if not QR_LIBRARY_AVAILABLE:
            return {
                "success": False, 
                "error": "Biblioteca de generación de QR no disponible. Instale: pip install qrcode[pil]"
            }
        
        # Validar URL/texto
        if not qr_request.url or len(qr_request.url.strip()) == 0:
            return {"success": False, "error": "URL o texto requerido"}
        
        url = qr_request.url.strip()
        
        # Validar tamaño
        if qr_request.size < 100 or qr_request.size > 1000:
            return {"success": False, "error": "El tamaño debe estar entre 100 y 1000 píxeles"}
        
        # Validar nivel de corrección de errores
        valid_error_levels = ["L", "M", "Q", "H"]
        error_correction = qr_request.error_correction.upper()
        if error_correction not in valid_error_levels:
            error_correction = "M"
            
        # Forzar alta corrección si hay logo
        if qr_request.brand_logo_base64:
            error_correction = "H"
        
        # Generar imagen QR
        qr_image = generate_qr_image(
            data=url,
            size=qr_request.size,
            error_correction=error_correction,
            color_dark=qr_request.color_dark,
            color_light=qr_request.color_light,
            logo_mode=qr_request.logo_mode,
            brand_logo_base64=qr_request.brand_logo_base64
        )
        
        if not qr_image:
            return {"success": False, "error": "Error generando imagen QR"}
        
        # Registrar generación para analytics (sin campaña asociada)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qr_generations (campaign_id, physical_device_id, qr_size, generated_by)
                    VALUES (%s, %s, %s, %s)
                """, (None, None, qr_request.size, get_client_ip(request)))
                conn.commit()
        except Exception as log_error:
            logger.warning(f"No se pudo registrar generación de QR personalizado: {log_error}")
        
        logger.info(f"QR personalizado generado, URL: {url[:50]}..., tamaño: {qr_request.size}px")
        
        return {
            "success": True,
            "qr_image": qr_image,
            "url": url,
            "size": qr_request.size,
            "error_correction": error_correction,
            "format": qr_request.format,
            "logo_mode": qr_request.logo_mode,
            "filename_suffix": "_" + qr_request.logo_mode[:2].upper()
        }
        
    except Exception as e:
        logger.error(f"Error generando QR personalizado: {e}")
        return {"success": False, "error": str(e)}

class QRGenerateWithLogoRequest(BaseModel):
    data: str
    size: int = 300
    color_dark: str = "#000000"
    color_light: str = "#FFFFFF"
    logo_mode: str = "default"
    brand_logo_base64: Optional[str] = None
    brand_banner_base64: Optional[str] = None
    error_correction: str = "H"

@app.post("/api/qr/generate-with-logo")
async def generate_qr_with_logo(request: QRGenerateWithLogoRequest):
    """Endpoint simplificado para generar un QR con el logo solicitado"""
    try:
        qr_image = generate_qr_image(
            data=request.data,
            size=request.size,
            error_correction=request.error_correction,
            color_dark=request.color_dark,
            color_light=request.color_light,
            logo_mode=request.logo_mode,
            brand_logo_base64=request.brand_logo_base64
        )
        if not qr_image:
            return {"success": False, "error": "Error generando imagen QR"}
        return {"success": True, "qr_image": qr_image}
    except Exception as e:
        logger.error(f"Error al regenerar logo QR: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/qr/validate-logo")
async def validate_logo(request: LogoValidationRequest):
    """Valida una imagen subida como logo para QR"""
    try:
        # Extraer base64
        base64_data = request.image_base64
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
            
        image_bytes = base64.b64decode(base64_data)
        
        # Calcular tamaño
        file_size_kb = len(image_bytes) / 1024
        
        # Leer imagen con Pillow
        if not PIL_AVAILABLE:
            return {"can_proceed": False, "score": 0.0, "errors": ["La biblioteca Pillow no está instalada"]}
            
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        result = {
            "can_proceed": True,
            "score": 1.0,
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        # Validar dimensiones
        if width < 100 or height < 100:
            result["checks"]["dimensions"] = {"passed": False, "optimal": False, "message": f"Dimensiones muy pequeñas ({width}x{height}px). Mínimo 100x100px."}
            result["errors"].append("La imagen es demasiado pequeña para asegurar buena calidad al escanear.")
            result["can_proceed"] = False
            result["score"] -= 0.5
        elif width > 1024 or height > 1024:
            result["checks"]["dimensions"] = {"passed": True, "optimal": False, "message": f"Dimensiones grandes ({width}x{height}px). Será redimensionada."}
            result["warnings"].append("La resolución es alta; la imagen será comprimida y redimensionada durante la generación.")
            result["score"] -= 0.1
        else:
            result["checks"]["dimensions"] = {"passed": True, "optimal": True, "message": f"Dimensiones óptimas ({width}x{height}px)."}
            
        # Validar tamaño archivo (ejemplo: max 2MB)
        if file_size_kb > 2048:
            result["checks"]["file_size"] = {"passed": False, "optimal": False, "message": f"Archivo muy pesado ({file_size_kb:.1f} KB). Máximo 2MB."}
            result["errors"].append("El tamaño del archivo supera el límite de 2MB.")
            result["can_proceed"] = False
            result["score"] -= 0.5
        elif file_size_kb > 500:
            result["checks"]["file_size"] = {"passed": True, "optimal": False, "message": f"Archivo algo pesado ({file_size_kb:.1f} KB)."}
            result["warnings"].append("El archivo pesa más de 500KB.")
            result["score"] -= 0.1
        else:
            result["checks"]["file_size"] = {"passed": True, "optimal": True, "message": f"Tamaño de archivo adecuado ({file_size_kb:.1f} KB)."}
            
        # Validar ratio (cuadrado ideal para QR)
        ratio = max(width, height) / min(width, height)
        if ratio > 2.0:
            result["checks"]["aspect_ratio"] = {"passed": True, "optimal": False, "message": "Proporción alargada. Para mejores resultados use imágenes cuadradas o circulares."}
            result["warnings"].append("La imagen es muy alargada y podría reducir la legibilidad del código QR.")
            result["score"] -= 0.2
        else:
            result["checks"]["aspect_ratio"] = {"passed": True, "optimal": True, "message": "Proporción adecuada."}
            
        # Validar formato con transparencia
        if img.mode not in ('RGBA', 'LA') and 'transparency' not in img.info:
            result["checks"]["transparency"] = {"passed": True, "optimal": False, "message": "Sin fondo transparente. Ocultará más bloques del QR."}
            result["warnings"].append("Se recomienda usar imágenes PNG con fondo transparente para no obstruir el QR.")
            result["score"] -= 0.1
        else:
            result["checks"]["transparency"] = {"passed": True, "optimal": True, "message": "Fondo transparente detectado (o soportado)."}
            
        result["score"] = max(0.0, result["score"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error procesando logo para validación: {str(e)}")
        return {
            "can_proceed": False,
            "score": 0.0,
            "errors": [f"El archivo no es una imagen válida o está dañado: {str(e)}"]
        }

@app.get("/api/qr/status")
async def get_qr_status():
    """Verificar estado del sistema de generación de QR"""
    return {
        "success": True,
        "qr_library_available": QR_LIBRARY_AVAILABLE,
        "pil_available": PIL_AVAILABLE,
        "message": "Sistema de generación de QR operativo" if QR_LIBRARY_AVAILABLE else "Instale: pip install qrcode[pil] Pillow"
    }

# ================================
# APIs ADICIONALES ÚTILES
# ================================

@app.get("/api/scans")
async def get_scans(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    campaign_code: Optional[str] = None,
    device_id: Optional[str] = None,
    client: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Obtener escaneos con filtros opcionales"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Construir query con filtros
            query = "SELECT * FROM scans WHERE 1=1"
            params = []
            
            if campaign_code:
                query += " AND campaign_code = %s"
                params.append(campaign_code)
            
            if device_id:
                query += " AND device_id = %s"
                params.append(device_id)
            
            if client:
                query += " AND client = %s"
                params.append(client)
            
            if start_date:
                query += " AND scan_timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND scan_timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY scan_timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            scans = [dict(row) for row in cursor.fetchall()]
            
            # Contar total de registros
            count_query = query.replace("SELECT *", "SELECT COUNT(*)").split("ORDER BY")[0]
            cursor.execute(count_query, params[:-2])  # Sin limit y offset
            row = cursor.fetchone()
            total = list(row.values())[0] if row else 0
        
        return {
            "success": True,
            "scans": scans,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error obteniendo escaneos: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/campaigns/{campaign_code}/stats")
async def get_campaign_stats(campaign_code: str):
    """Obtener estadísticas específicas de una campaña"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la campaña existe
            cursor.execute("SELECT * FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            campaign = cursor.fetchone()
            if not campaign:
                return {"success": False, "error": "Campaña no encontrada"}
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN redirect_completed = TRUE THEN 1 END) as completed_redirects,
                    ROUND(AVG(duration_seconds)::numeric, 2) as avg_duration,
                    MIN(scan_timestamp) as first_scan,
                    MAX(scan_timestamp) as last_scan,
                    COUNT(DISTINCT ip_address) as unique_visitors,
                    COUNT(DISTINCT device_id) as unique_devices
                FROM scans 
                WHERE campaign_code = %s
            """, (campaign_code,))
            stats = dict(cursor.fetchone())
            
            # Dispositivos más utilizados
            cursor.execute("""
                SELECT device_id, device_name, location, venue, COUNT(*) as scans
                FROM scans 
                WHERE campaign_code = %s AND device_id IS NOT NULL
                GROUP BY device_id, device_name, location, venue
                ORDER BY scans DESC
                LIMIT 5
            """, (campaign_code,))
            top_devices = [dict(row) for row in cursor.fetchall()]
            
            # Tipos de dispositivos de usuarios
            cursor.execute("""
                SELECT user_device_type, COUNT(*) as count
                FROM scans 
                WHERE campaign_code = %s
                GROUP BY user_device_type
                ORDER BY count DESC
            """, (campaign_code,))
            device_types = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por día (últimos 30 días)
            cursor.execute("""
                SELECT 
                    CAST(scan_timestamp AS DATE) as date,
                    COUNT(*) as scans
                FROM scans
                WHERE campaign_code = %s AND scan_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
                GROUP BY CAST(scan_timestamp AS DATE)
                ORDER BY date
            """, (campaign_code,))
            daily_activity = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "campaign": dict(campaign),
            "stats": stats,
            "top_devices": top_devices,
            "device_types": device_types,
            "daily_activity": daily_activity
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de campaña: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/devices/{device_id}/stats")
async def get_device_stats(device_id: str):
    """Obtener estadísticas específicas de un dispositivo"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el dispositivo existe
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = %s", (device_id,))
            device = cursor.fetchone()
            if not device:
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN redirect_completed = TRUE THEN 1 END) as completed_redirects,
                    ROUND(AVG(duration_seconds)::numeric, 2) as avg_duration,
                    MIN(scan_timestamp) as first_scan,
                    MAX(scan_timestamp) as last_scan,
                    COUNT(DISTINCT ip_address) as unique_visitors,
                    COUNT(DISTINCT campaign_code) as unique_campaigns
                FROM scans 
                WHERE device_id = %s
            """, (device_id,))
            stats = dict(cursor.fetchone())
            
            # Campañas más escaneadas en este dispositivo
            cursor.execute("""
                SELECT campaign_code, client, COUNT(*) as scans
                FROM scans 
                WHERE device_id = %s
                GROUP BY campaign_code, client
                ORDER BY scans DESC
                LIMIT 5
            """, (device_id,))
            top_campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por hora del día
            cursor.execute("""
                SELECT 
                    EXTRACT(HOUR FROM scan_timestamp)::INTEGER as hour,
                    COUNT(*) as scans
                FROM scans
                WHERE device_id = %s
                GROUP BY EXTRACT(HOUR FROM scan_timestamp)
                ORDER BY hour
            """, (device_id,))
            hourly_activity = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "device": dict(device),
            "stats": stats,
            "top_campaigns": top_campaigns,
            "hourly_activity": hourly_activity
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de dispositivo: {e}")
        return {"success": False, "error": str(e)}

# ================================
# ENDPOINT PARA EXPORTAR DATOS
# ================================

@app.get("/api/export/scans")
async def export_scans(
    format: str = "json",  # json, csv
    campaign_code: Optional[str] = None,
    device_id: Optional[str] = None,
    client: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Exportar datos de escaneos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Construir query con filtros
            query = """
                SELECT 
                    s.*,
                    c.client as campaign_client,
                    c.description as campaign_description,
                    pd.device_name,
                    pd.location as device_location,
                    pd.venue as device_venue
                FROM scans s
                LEFT JOIN campaigns c ON s.campaign_code = c.campaign_code
                LEFT JOIN physical_devices pd ON s.device_id = pd.device_id
                WHERE 1=1
            """
            params = []
            
            if campaign_code:
                query += " AND s.campaign_code = %s"
                params.append(campaign_code)
            
            if device_id:
                query += " AND s.device_id = %s"
                params.append(device_id)
            
            if client:
                query += " AND (s.client = %s OR c.client = %s)"
                params.extend([client, client])
            
            if start_date:
                query += " AND s.scan_timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND s.scan_timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY s.scan_timestamp DESC"
            
            cursor.execute(query, params)
            scans = [dict(row) for row in cursor.fetchall()]
        
        if format.lower() == "csv":
            output = io.StringIO()
            # BOM para UTF-8 (compatibilidad con Excel)
            output.write('\ufeff')
            
            if scans:
                writer = csv.DictWriter(output, fieldnames=scans[0].keys())
                writer.writeheader()
                writer.writerows(scans)
            
            def iter_csv():
                output.seek(0)
                yield output.read()
            
            return StreamingResponse(
                iter_csv(),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=qr_scans_export.csv"}
            )
        
        return {
            "success": True,
            "data": scans,
            "total": len(scans),
            "export_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exportando datos: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/export/client/{client_name}")
async def export_client_data(client_name: str, format: str = "json"):
    """Exportar todos los datos de un cliente"""
    try:
        client_name = unquote(client_name)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    s.*,
                    c.description as campaign_description,
                    pd.device_name as physical_device_name,
                    pd.location as physical_device_location,
                    pd.venue as physical_device_venue
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                LEFT JOIN physical_devices pd ON s.device_id = pd.device_id
                WHERE c.client = %s
                ORDER BY s.scan_timestamp DESC
            """, (client_name,))
            scans = [dict(row) for row in cursor.fetchall()]
        
        if format.lower() == "csv":
            output = io.StringIO()
            output.write('\ufeff')  # BOM UTF-8
            
            if scans:
                writer = csv.DictWriter(output, fieldnames=scans[0].keys())
                writer.writeheader()
                writer.writerows(scans)
            
            # Sanitizar nombre del cliente para el archivo
            safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
            
            def iter_csv():
                output.seek(0)
                yield output.read()
            
            return StreamingResponse(
                iter_csv(),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename=export_{safe_client_name}.csv"}
            )
        
        return {
            "success": True,
            "client": client_name,
            "data": scans,
            "total": len(scans),
            "export_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exportando datos de cliente: {e}")
        return {"success": False, "error": str(e)}

# ================================
# INICIALIZACIÓN
# ================================

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la aplicación"""
    logger.info("=" * 60)
    logger.info("Iniciando QR Tracking System v2.7.2")
    logger.info("=" * 60)
    
    # Inicializar base de datos
    init_database()
    
    # Crear backup automático al iniciar
    create_backup("auto")
    
    # Limpiar backups antiguos
    cleanup_old_backups()
    
    logger.info(f"Directorio de logs: {LOGS_DIR}")
    logger.info(f"Directorio de backups: {BACKUPS_DIR}")
    logger.info(f"Directorio de archivos estáticos: {STATIC_DIR}")
    logger.info("Sistema iniciado correctamente")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("Cerrando QR Tracking System")
    # Crear backup al cerrar
    create_backup("auto")
    logger.info("Sistema cerrado correctamente")

# ================================
# EJECUTAR APLICACIÓN
# ================================

if __name__ == "__main__":
    import uvicorn
    
    # Crear datos de ejemplo si la base de datos está vacía
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            if cursor.fetchone()[0] == 0:
                logger.info("Creando datos de ejemplo...")
                
                # Campañas de ejemplo
                example_campaigns = [
                    ("promo_verano_2024", "Nike", "https://instagram.com/nike", "Promoción de verano 2024"),
                    ("black_friday_tech", "Samsung", "https://www.samsung.com/ve/promociones", "Black Friday Tech 2024"),
                    ("nuevos_productos", "Coca Cola", "https://instagram.com/cocacola", "Lanzamiento nuevos productos"),
                ]
                
                for campaign_code, client, destination, description in example_campaigns:
                    cursor.execute("""
                        INSERT INTO campaigns (campaign_code, client, destination, description)
                        VALUES (%s, %s, %s, %s)
                    """, (campaign_code, client, destination, description))
                
                # Dispositivos de ejemplo
                example_devices = [
                    ("totem_centro_comercial_01", "Totem Principal Entrada", "Totem Interactivo", 
                     "Entrada Principal - Planta Baja", "Centro Comercial Plaza Venezuela"),
                    ("pantalla_food_court", "Pantalla Food Court", "Pantalla LED", 
                     "Área de Comidas", "Centro Comercial Plaza Venezuela"),
                    ("kiosco_metro_plaza_vzla", "Kiosco Metro Plaza Venezuela", "Kiosco Digital", 
                     "Estación Metro Plaza Venezuela", "Metro de Caracas"),
                ]
                
                for device_id, device_name, device_type, location, venue in example_devices:
                    cursor.execute("""
                        INSERT INTO physical_devices (device_id, device_name, device_type, location, venue)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (device_id, device_name, device_type, location, venue))
                
                conn.commit()
                logger.info("Datos de ejemplo creados")
    except Exception as e:
        logger.error(f"Error creando datos de ejemplo: {e}")
    
    # Ejecutar servidor
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )
