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

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
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
import user_agents
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

# Base de datos
DATABASE_PATH = os.path.join(BASE_DIR, "qr_tracking.db")

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
    """
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

class QRCustomRequest(BaseModel):
    """Solicitud de generación de QR personalizado desde URL"""
    url: str
    size: int = 300
    format: str = "png"
    style: str = "square"
    color_dark: str = "#000000"
    color_light: str = "#FFFFFF"
    error_correction: str = "M"  # L, M, Q, H

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
        with sqlite3.connect(DATABASE_PATH) as conn:
            # Crear esquema básico
            create_basic_schema(conn)
            # Verificar que las tablas existan
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"Tablas en base de datos: {[table[0] for table in tables]}")
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")

def create_basic_schema(conn):
    """Crear esquema básico si no existe el archivo SQL"""
    cursor = conn.cursor()
    
    # Crear tabla campaigns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_code TEXT NOT NULL UNIQUE,
            client TEXT NOT NULL,
            destination TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Crear tabla physical_devices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS physical_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL UNIQUE,
            device_name TEXT,
            device_type TEXT,
            location TEXT,
            venue TEXT,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Crear tabla scans (con campos adicionales para datos del dispositivo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            redirect_completed BOOLEAN DEFAULT 0,
            redirect_timestamp DATETIME,
            duration_seconds REAL,
            campaign_id INTEGER,
            physical_device_id INTEGER,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            utm_term TEXT,
            utm_content TEXT,
            cpu_cores INTEGER,
            device_pixel_ratio REAL
        );
    """)
    
    # Crear tabla qr_generations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            physical_device_id INTEGER,
            qr_size INTEGER,
            generated_by TEXT,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Crear índices para mejor rendimiento
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_campaign ON scans(campaign_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_device ON scans(device_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(scan_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_session ON scans(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_utm_source ON scans(utm_source);")
    
    conn.commit()
    
    # Ejecutar migración para agregar columnas nuevas si no existen
    migrate_database(conn)

def migrate_database(conn):
    """Migrar base de datos agregando columnas nuevas si no existen"""
    cursor = conn.cursor()
    
    # Obtener columnas existentes en la tabla scans
    cursor.execute("PRAGMA table_info(scans)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Columnas nuevas a agregar (v2.7.3)
    new_columns = {
        'utm_source': 'TEXT',
        'utm_medium': 'TEXT',
        'utm_campaign': 'TEXT',
        'utm_term': 'TEXT',
        'utm_content': 'TEXT',
        'cpu_cores': 'INTEGER',
        'device_pixel_ratio': 'REAL'
    }
    
    # Agregar columnas que no existan
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE scans ADD COLUMN {column_name} {column_type}")
                logger.info(f"Columna '{column_name}' agregada a tabla scans")
            except sqlite3.OperationalError as e:
                # La columna ya existe (puede ocurrir en casos edge)
                logger.debug(f"Columna '{column_name}' ya existe o error: {e}")
    
    conn.commit()
    logger.info("Migración de base de datos completada")

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

# ================================
# FUNCIONES DE UTILIDAD
# ================================

def detect_device_info(user_agent_string: str) -> Dict[str, str]:
    """Detectar información del dispositivo desde User-Agent"""
    try:
        user_agent = user_agents.parse(user_agent_string)
        
        # Determinar tipo de dispositivo
        if user_agent.is_mobile:
            device_type = "Mobile"
        elif user_agent.is_tablet:
            device_type = "Tablet"
        elif user_agent.is_pc:
            device_type = "Desktop"
        else:
            device_type = "Unknown"
        
        return {
            "device_type": device_type,
            "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
            "operating_system": f"{user_agent.os.family} {user_agent.os.version_string}",
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc
        }
    except Exception as e:
        logger.warning(f"Error detectando dispositivo: {e}")
        return {
            "device_type": "Unknown",
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
        reports_path = os.path.join(TEMPLATES_DIR, "client_reports.html")
        with open(reports_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Reportes</h1><p>Archivo client_reports.html no encontrado en /templates</p><a href='/'>← Volver</a>")

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
async def track_qr_scan(request: Request):
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
        device_info = detect_device_info(user_agent)
        client_ip = get_client_ip(request)
        
        # Buscar información de la campaña en la base de datos
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT destination, client FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            result = cursor.fetchone()
            if result:
                if not destination:
                    destination = result["destination"]
                if not client:
                    client = result["client"]
        
        # Si aún no hay destino, usar uno por defecto
        if not destination:
            destination = f"https://google.com/search?q={campaign_code}"
        
        # Registrar el escaneo en la base de datos (incluyendo UTM)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scans (
                    campaign_code, client, destination, device_id, device_name, 
                    location, venue, user_device_type, browser, operating_system, 
                    user_agent, ip_address, session_id, scan_timestamp,
                    utm_source, utm_medium, utm_campaign, utm_term, utm_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_code, client, destination, device_id, device_name,
                location, venue, device_info["device_type"], device_info["browser"],
                device_info["operating_system"], user_agent, client_ip, session_id,
                datetime.now().isoformat(),
                utm_source, utm_medium, utm_campaign, utm_term, utm_content
            ))
            conn.commit()
            scan_id = cursor.lastrowid
        
        # Log del escaneo (logger específico para scans)
        scans_logger.info(f"QR escaneado: campaign={campaign_code}, client={client}, device={device_info['device_type']}, IP={client_ip}, session={session_id}")
        
        # Crear respuesta HTML con redirección automática mejorada
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Redirigiendo...</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="/static/css/main.css">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Plus Jakarta Sans', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 50px 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(15px);
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 400px;
                    width: 90%;
                }}
                h1 {{ font-size: 28px; margin-bottom: 10px; }}
                .countdown {{
                    font-size: 72px;
                    font-weight: 700;
                    margin: 30px 0;
                    text-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }}
                .progress-bar {{
                    width: 100%;
                    height: 6px;
                    background: rgba(255,255,255,0.2);
                    border-radius: 3px;
                    overflow: hidden;
                    margin: 20px 0;
                }}
                .progress {{
                    height: 100%;
                    background: white;
                    border-radius: 3px;
                    animation: shrink 3s linear forwards;
                }}
                @keyframes shrink {{
                    from {{ width: 100%; }}
                    to {{ width: 0%; }}
                }}
                .client-name {{ font-size: 18px; opacity: 0.9; margin-bottom: 5px; }}
                .campaign-code {{ font-size: 12px; opacity: 0.6; }}
                .manual-link {{
                    display: inline-block;
                    margin-top: 25px;
                    color: white;
                    opacity: 0.8;
                    text-decoration: none;
                    font-size: 14px;
                    padding: 10px 20px;
                    border: 1px solid rgba(255,255,255,0.3);
                    border-radius: 25px;
                    transition: all 0.3s;
                }}
                .manual-link:hover {{
                    opacity: 1;
                    background: rgba(255,255,255,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 QR Tracking</h1>
                <div class="countdown" id="countdown">3</div>
                <div class="progress-bar"><div class="progress"></div></div>
                <p class="client-name">Redirigiendo a {client or 'destino'}...</p>
                <p class="campaign-code">Campaña: {campaign_code}</p>
                <a href="{destination}" class="manual-link">Ir manualmente →</a>
            </div>
            <script>
                const sessionId = '{session_id}';
                const scanId = {scan_id};
                const destination = '{destination}';
                
                // Capturar datos adicionales del dispositivo (incluyendo CPU cores y DPR)
                const deviceData = {{
                    session_id: sessionId,
                    screen_resolution: screen.width + 'x' + screen.height,
                    viewport_size: window.innerWidth + 'x' + window.innerHeight,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    language: navigator.language,
                    platform: navigator.platform,
                    connection_type: navigator.connection ? navigator.connection.effectiveType : 'unknown',
                    cpu_cores: navigator.hardwareConcurrency || null,
                    device_pixel_ratio: window.devicePixelRatio || null
                }};
                
                // Enviar datos adicionales
                fetch('/api/track/device-data', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(deviceData)
                }}).catch(console.error);
                
                // Countdown visual
                let count = 3;
                const countdownEl = document.getElementById('countdown');
                const interval = setInterval(() => {{
                    count--;
                    if (count > 0) {{
                        countdownEl.textContent = count;
                    }} else {{
                        clearInterval(interval);
                        countdownEl.textContent = '✓';
                    }}
                }}, 1000);
                
                // Redirigir después de 3 segundos
                setTimeout(() => {{
                    // Registrar completado
                    fetch('/api/track/complete', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            session_id: sessionId,
                            scan_id: scanId,
                            completion_time: new Date().toISOString()
                        }})
                    }}).catch(console.error);
                    
                    window.location.href = destination;
                }}, 3000);
                
                // Beacon al salir
                window.addEventListener('beforeunload', () => {{
                    navigator.sendBeacon('/api/track/complete', JSON.stringify({{
                        session_id: sessionId,
                        scan_id: scanId,
                        completion_time: new Date().toISOString()
                    }}));
                }});
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

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
                VALUES (?, ?, ?, ?, ?)
            """, (
                campaign.campaign_code, campaign.client, campaign.destination,
                campaign.description, campaign.active
            ))
            conn.commit()
            campaign_id = cursor.lastrowid
            
            # Obtener la campaña creada
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            new_campaign = dict(cursor.fetchone())
        
        logger.info(f"Campaña creada: {campaign.campaign_code}")
        return {
            "success": True,
            "message": "Campaña creada exitosamente",
            "campaign": new_campaign
        }
    except sqlite3.IntegrityError:
        return {"success": False, "error": "El código de campaña ya existe"}
    except Exception as e:
        logger.error(f"Error creando campaña: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/campaigns/{campaign_code}")
async def update_campaign(campaign_code: str, campaign_update: CampaignUpdate):
    """Actualizar campaña existente"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la campaña existe
            cursor.execute("SELECT id FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            if not cursor.fetchone():
                return {"success": False, "error": "Campaña no encontrada"}
            
            # Construir query de actualización dinámicamente
            update_fields = []
            values = []
            
            if campaign_update.client is not None:
                update_fields.append("client = ?")
                values.append(campaign_update.client)
            if campaign_update.destination is not None:
                update_fields.append("destination = ?")
                values.append(campaign_update.destination)
            if campaign_update.description is not None:
                update_fields.append("description = ?")
                values.append(campaign_update.description)
            if campaign_update.active is not None:
                update_fields.append("active = ?")
                values.append(campaign_update.active)
            
            if not update_fields:
                return {"success": False, "error": "No hay campos para actualizar"}
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(campaign_code)
            
            query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE campaign_code = ?"
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
            cursor.execute("SELECT active, client FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            result = cursor.fetchone()
            
            if not result:
                return {"success": False, "error": "Campaña no encontrada"}
            
            current_active = result["active"]
            client = result["client"]
            new_active = 0 if current_active else 1
            
            # Cambiar estado
            cursor.execute("""
                UPDATE campaigns 
                SET active = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE campaign_code = ?
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
                WHERE campaign_code = ?
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
            cursor.execute("SELECT client, description FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            campaign_row = cursor.fetchone()
            
            if not campaign_row:
                return {"success": False, "error": "Campaña no encontrada"}
            
            client = campaign_row["client"]
            
            # Eliminar la campaña completamente
            cursor.execute("DELETE FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            
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
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = ?", (device_id,))
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
            cursor.execute("SELECT id FROM physical_devices WHERE device_id = ?", (device.device_id,))
            if cursor.fetchone():
                logger.warning(f"Dispositivo ya existe: {device.device_id}")
                return {"success": False, "error": "El ID del dispositivo ya existe"}
            
            cursor.execute("""
                INSERT INTO physical_devices (device_id, device_name, device_type, location, venue, description, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                device.device_id, device.device_name, device.device_type,
                device.location, device.venue, device.description, device.active
            ))
            conn.commit()
            device_pk_id = cursor.lastrowid
            
            # Obtener el dispositivo creado
            cursor.execute("SELECT * FROM physical_devices WHERE id = ?", (device_pk_id,))
            new_device = dict(cursor.fetchone())
        
        logger.info(f"Dispositivo creado exitosamente: {device.device_id}")
        return {
            "success": True,
            "message": "Dispositivo creado exitosamente",
            "device": new_device
        }
    except sqlite3.IntegrityError as e:
        logger.error(f"Error de integridad: {e}")
        return {"success": False, "error": "El ID del dispositivo ya existe"}
    except Exception as e:
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
            cursor.execute("SELECT id FROM physical_devices WHERE device_id = ?", (device_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            # Construir query de actualización dinámicamente
            update_fields = []
            values = []
            
            if device_update.device_name is not None:
                update_fields.append("device_name = ?")
                values.append(device_update.device_name)
            if device_update.device_type is not None:
                update_fields.append("device_type = ?")
                values.append(device_update.device_type)
            if device_update.location is not None:
                update_fields.append("location = ?")
                values.append(device_update.location)
            if device_update.venue is not None:
                update_fields.append("venue = ?")
                values.append(device_update.venue)
            if device_update.description is not None:
                update_fields.append("description = ?")
                values.append(device_update.description)
            if device_update.active is not None:
                update_fields.append("active = ?")
                values.append(device_update.active)
            
            if not update_fields:
                return {"success": False, "error": "No hay campos para actualizar"}
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(device_id)
            
            query = f"UPDATE physical_devices SET {', '.join(update_fields)} WHERE device_id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "No se pudo actualizar el dispositivo"}
            
            # Obtener el dispositivo actualizado
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = ?", (device_id,))
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
            cursor.execute("SELECT device_name FROM physical_devices WHERE device_id = ?", (device_id,))
            device_row = cursor.fetchone()
            if not device_row:
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            device_name = device_row["device_name"]
            
            # Eliminar el dispositivo completamente
            cursor.execute("DELETE FROM physical_devices WHERE device_id = ?", (device_id,))
            
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
            cursor.execute("SELECT COUNT(*) FROM campaigns WHERE client = ?", (client_name,))
            if cursor.fetchone()[0] == 0:
                return {"success": False, "error": "Cliente no encontrado"}
            
            # Estadísticas generales del cliente
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT c.id) as total_campaigns,
                    COUNT(DISTINCT CASE WHEN c.active = 1 THEN c.id END) as active_campaigns,
                    COALESCE(COUNT(s.id), 0) as total_scans,
                    COALESCE(COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END), 0) as completed_redirects,
                    ROUND(COALESCE(AVG(s.duration_seconds), 0), 2) as avg_duration,
                    COUNT(DISTINCT s.ip_address) as unique_visitors,
                    COUNT(DISTINCT s.device_id) as unique_devices,
                    MIN(s.scan_timestamp) as first_scan,
                    MAX(s.scan_timestamp) as last_scan
                FROM campaigns c
                LEFT JOIN scans s ON c.campaign_code = s.campaign_code
                WHERE c.client = ?
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
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds), 2) as avg_duration
                FROM campaigns c
                LEFT JOIN scans s ON c.campaign_code = s.campaign_code
                WHERE c.client = ?
                GROUP BY c.id
                ORDER BY scans DESC
            """, (client_name,))
            campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por día (últimos 30 días)
            cursor.execute("""
                SELECT 
                    DATE(s.scan_timestamp) as date,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = ? AND s.scan_timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(s.scan_timestamp)
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
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = ? AND s.device_id IS NOT NULL AND s.device_id != ''
                GROUP BY s.device_id
                ORDER BY scans DESC
                LIMIT 10
            """, (client_name,))
            top_devices = [dict(row) for row in cursor.fetchall()]
            
            # Distribución de tipos de dispositivos de usuarios
            cursor.execute("""
                SELECT 
                    s.user_device_type as device_type,
                    COUNT(*) as count
                FROM scans s
                JOIN campaigns c ON s.campaign_code = c.campaign_code
                WHERE c.client = ?
                GROUP BY s.user_device_type
                ORDER BY count DESC
            """, (client_name,))
            device_types = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "client": client_name,
            "stats": stats,
            "campaigns": campaigns,
            "daily_activity": daily_activity,
            "top_devices": top_devices,
            "device_types": device_types
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
                    screen_resolution = ?,
                    viewport_size = ?,
                    timezone = ?,
                    language = ?,
                    platform = ?,
                    connection_type = ?,
                    cpu_cores = ?,
                    device_pixel_ratio = ?
                WHERE session_id = ?
            """, (
                device_data.screen_resolution,
                device_data.viewport_size,
                device_data.timezone,
                device_data.language,
                device_data.platform,
                device_data.connection_type,
                device_data.cpu_cores,
                device_data.device_pixel_ratio,
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
        data = await request.json()
        session_id = data.get("session_id")
        scan_id = data.get("scan_id")
        completion_time = data.get("completion_time")
        
        if not session_id or not scan_id:
            return {"success": False, "error": "session_id y scan_id requeridos"}
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Calcular duración si es posible
            cursor.execute("""
                SELECT scan_timestamp FROM scans 
                WHERE id = ? AND session_id = ?
            """, (scan_id, session_id))
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
            cursor.execute("""
                UPDATE scans 
                SET redirect_completed = 1, 
                    redirect_timestamp = CURRENT_TIMESTAMP,
                    duration_seconds = ?
                WHERE id = ? AND session_id = ?
            """, (duration, scan_id, session_id))
            conn.commit()
        
        scans_logger.info(f"Tracking completado: scan_id={scan_id}, duration={duration}s")
        return {"success": True, "message": "Tracking completado"}
    except Exception as e:
        logger.error(f"Error completando tracking: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE ANALYTICS
# ================================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Obtener datos completos para el dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales mejoradas
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM campaigns WHERE active = 1) as active_campaigns,
                    (SELECT COUNT(*) FROM physical_devices WHERE active = 1) as active_devices,
                    (SELECT COUNT(*) FROM scans) as total_scans,
                    (SELECT COUNT(*) FROM scans WHERE redirect_completed = 1) as completed_redirects,
                    (SELECT COUNT(DISTINCT client) FROM campaigns WHERE client != '') as total_clients,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= datetime('now', '-24 hours')) as scans_24h,
                    (SELECT COUNT(*) FROM scans WHERE scan_timestamp >= datetime('now', '-7 days')) as scans_7d,
                    (SELECT COUNT(DISTINCT ip_address) FROM scans) as unique_visitors
            """)
            stats = dict(cursor.fetchone())
            
            # Estadísticas por campaña
            cursor.execute("""
                SELECT 
                    s.campaign_code as campaign,
                    s.client,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds), 2) as avg_duration,
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
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds), 2) as avg_duration
                FROM physical_devices pd
                LEFT JOIN scans s ON pd.device_id = s.device_id
                WHERE pd.active = 1
                GROUP BY pd.id
                ORDER BY scans DESC
                LIMIT 10
            """)
            physical_devices = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por horas (últimas 24 horas)
            cursor.execute("""
                SELECT 
                    CAST(strftime('%H', scan_timestamp) AS INTEGER) as hour,
                    COUNT(*) as scans
                FROM scans
                WHERE scan_timestamp >= datetime('now', '-24 hours')
                GROUP BY strftime('%H', scan_timestamp)
                ORDER BY hour
            """)
            hourly = [dict(row) for row in cursor.fetchall()]
            
            # Top venues
            cursor.execute("""
                SELECT 
                    venue,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN redirect_completed = 1 THEN 1 END) as completions,
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
                VALUES (?, ?, ?, ?)
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
                      color_dark: str = "#000000", color_light: str = "#FFFFFF") -> Optional[str]:
    """
    Genera una imagen QR y la devuelve como base64
    
    Args:
        data: URL o texto a codificar en el QR
        size: Tamaño en píxeles (ancho y alto)
        error_correction: Nivel de corrección de errores (L, M, Q, H)
        color_dark: Color de los módulos oscuros (hex)
        color_light: Color del fondo (hex)
    
    Returns:
        Imagen en formato base64 o None si hay error
    """
    if not QR_LIBRARY_AVAILABLE:
        logger.error("Biblioteca qrcode no disponible")
        return None
    
    try:
        # Mapear nivel de corrección de errores
        error_levels = {
            "L": ERROR_CORRECT_L,  # ~7% corrección
            "M": ERROR_CORRECT_M,  # ~15% corrección
            "Q": ERROR_CORRECT_Q,  # ~25% corrección
            "H": ERROR_CORRECT_H   # ~30% corrección
        }
        error_level = error_levels.get(error_correction.upper(), ERROR_CORRECT_M)
        
        # Crear código QR
        qr = qrcode.QRCode(
            version=None,  # Auto-determinar versión
            error_correction=error_level,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Convertir colores hex a RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        fill_color = hex_to_rgb(color_dark)
        back_color = hex_to_rgb(color_light)
        
        # Crear imagen
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Redimensionar si es necesario
        if img.size[0] != size:
            img = img.resize((size, size), Image.LANCZOS if PIL_AVAILABLE else Image.NEAREST)
        
        # Convertir a base64
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
                WHERE campaign_code = ?
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
                    WHERE device_id = ?
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
        
        # Generar imagen QR
        qr_image = generate_qr_image(
            data=tracking_url,
            size=qr_request.size,
            error_correction="M",
            color_dark=qr_request.color_dark,
            color_light=qr_request.color_light
        )
        
        if not qr_image:
            return {"success": False, "error": "Error generando imagen QR"}
        
        # Registrar generación para analytics
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qr_generations (campaign_id, physical_device_id, qr_size, generated_by)
                    VALUES (?, ?, ?, ?)
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
            "format": qr_request.format
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
        
        # Generar imagen QR
        qr_image = generate_qr_image(
            data=url,
            size=qr_request.size,
            error_correction=error_correction,
            color_dark=qr_request.color_dark,
            color_light=qr_request.color_light
        )
        
        if not qr_image:
            return {"success": False, "error": "Error generando imagen QR"}
        
        # Registrar generación para analytics (sin campaña asociada)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qr_generations (campaign_id, physical_device_id, qr_size, generated_by)
                    VALUES (?, ?, ?, ?)
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
            "format": qr_request.format
        }
        
    except Exception as e:
        logger.error(f"Error generando QR personalizado: {e}")
        return {"success": False, "error": str(e)}

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
                query += " AND campaign_code = ?"
                params.append(campaign_code)
            
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            
            if client:
                query += " AND client = ?"
                params.append(client)
            
            if start_date:
                query += " AND scan_timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND scan_timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY scan_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            scans = [dict(row) for row in cursor.fetchall()]
            
            # Contar total de registros
            count_query = query.replace("SELECT *", "SELECT COUNT(*)").split("ORDER BY")[0]
            cursor.execute(count_query, params[:-2])  # Sin limit y offset
            total = cursor.fetchone()[0]
        
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
            cursor.execute("SELECT * FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            campaign = cursor.fetchone()
            if not campaign:
                return {"success": False, "error": "Campaña no encontrada"}
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN redirect_completed = 1 THEN 1 END) as completed_redirects,
                    ROUND(AVG(duration_seconds), 2) as avg_duration,
                    MIN(scan_timestamp) as first_scan,
                    MAX(scan_timestamp) as last_scan,
                    COUNT(DISTINCT ip_address) as unique_visitors,
                    COUNT(DISTINCT device_id) as unique_devices
                FROM scans 
                WHERE campaign_code = ?
            """, (campaign_code,))
            stats = dict(cursor.fetchone())
            
            # Dispositivos más utilizados
            cursor.execute("""
                SELECT device_id, device_name, location, venue, COUNT(*) as scans
                FROM scans 
                WHERE campaign_code = ? AND device_id IS NOT NULL
                GROUP BY device_id
                ORDER BY scans DESC
                LIMIT 5
            """, (campaign_code,))
            top_devices = [dict(row) for row in cursor.fetchall()]
            
            # Tipos de dispositivos de usuarios
            cursor.execute("""
                SELECT user_device_type, COUNT(*) as count
                FROM scans 
                WHERE campaign_code = ?
                GROUP BY user_device_type
                ORDER BY count DESC
            """, (campaign_code,))
            device_types = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por día (últimos 30 días)
            cursor.execute("""
                SELECT 
                    DATE(scan_timestamp) as date,
                    COUNT(*) as scans
                FROM scans
                WHERE campaign_code = ? AND scan_timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(scan_timestamp)
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
            cursor.execute("SELECT * FROM physical_devices WHERE device_id = ?", (device_id,))
            device = cursor.fetchone()
            if not device:
                return {"success": False, "error": "Dispositivo no encontrado"}
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN redirect_completed = 1 THEN 1 END) as completed_redirects,
                    ROUND(AVG(duration_seconds), 2) as avg_duration,
                    MIN(scan_timestamp) as first_scan,
                    MAX(scan_timestamp) as last_scan,
                    COUNT(DISTINCT ip_address) as unique_visitors,
                    COUNT(DISTINCT campaign_code) as unique_campaigns
                FROM scans 
                WHERE device_id = ?
            """, (device_id,))
            stats = dict(cursor.fetchone())
            
            # Campañas más escaneadas en este dispositivo
            cursor.execute("""
                SELECT campaign_code, client, COUNT(*) as scans
                FROM scans 
                WHERE device_id = ?
                GROUP BY campaign_code
                ORDER BY scans DESC
                LIMIT 5
            """, (device_id,))
            top_campaigns = [dict(row) for row in cursor.fetchall()]
            
            # Actividad por hora del día
            cursor.execute("""
                SELECT 
                    CAST(strftime('%H', scan_timestamp) AS INTEGER) as hour,
                    COUNT(*) as scans
                FROM scans
                WHERE device_id = ?
                GROUP BY strftime('%H', scan_timestamp)
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
                query += " AND s.campaign_code = ?"
                params.append(campaign_code)
            
            if device_id:
                query += " AND s.device_id = ?"
                params.append(device_id)
            
            if client:
                query += " AND (s.client = ? OR c.client = ?)"
                params.extend([client, client])
            
            if start_date:
                query += " AND s.scan_timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND s.scan_timestamp <= ?"
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
                WHERE c.client = ?
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
                        VALUES (?, ?, ?, ?)
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
                        VALUES (?, ?, ?, ?, ?)
                    """, (device_id, device_name, device_type, location, venue))
                
                conn.commit()
                logger.info("Datos de ejemplo creados")
    except Exception as e:
        logger.error(f"Error creando datos de ejemplo: {e}")
    
    # Ejecutar servidor
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
