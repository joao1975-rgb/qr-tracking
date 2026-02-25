
"""
QR Tracking System - Backend Completo
Versión: 2.5.1 - Corregido para dispositivos
Autor: Sistema QR Tracking
Fecha: 2024

Funcionalidades:
- Gestión completa de campañas
- Gestión de dispositivos físicos (CORREGIDA)
- Tracking avanzado de escaneos
- Analytics en tiempo real
- APIs RESTful completas
- Servir archivos HTML estáticos
"""

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta
import uuid
from device_detector import DeviceDetector
import ipaddress
import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import urlparse, parse_qs
import urllib.parse

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================

app = FastAPI(
    title="QR Tracking System",
    description="Sistema avanzado de tracking para códigos QR",
    version="2.5.1"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos
DATABASE_URL = os.environ.get("DATABASE_URL")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "qr_tracking.db")

def is_postgres():
    return DATABASE_URL is not None and DATABASE_URL.startswith("postgres")


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

class QRGenerationLog(BaseModel):
    campaign_id: Optional[int] = None
    physical_device_id: Optional[int] = None
    qr_size: int = 256
    generated_by: Optional[str] = None

# ================================
# FUNCIONES DE BASE DE DATOS
# ================================

def init_database():
    """Inicializar la base de datos con el esquema"""
    try:
        conn = get_db_connection()
        create_basic_schema(conn)
        
        cursor = conn.cursor()
        if is_postgres():
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
        tables = cursor.fetchall()
        logger.info(f"Tablas creadas: {[table[0] for table in tables]}")
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")

def create_basic_schema(conn):
    """Crear esquema básico si no existe el archivo SQL"""
    cursor = conn.cursor()
    
    # Determinar tipo de dato para ids auto-incrementables
    pk_type = "SERIAL" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    boolean_type = "BOOLEAN" if is_postgres() else "BOOLEAN"
    
    # Crear tabla campaigns
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS campaigns (
            id {pk_type},
            campaign_code TEXT NOT NULL UNIQUE,
            client TEXT NOT NULL,
            destination TEXT NOT NULL,
            description TEXT,
            active {boolean_type} DEFAULT {'TRUE' if is_postgres() else '1'},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            {', PRIMARY KEY (id)' if is_postgres() else ''}
        );
    """)
    
    # Crear tabla physical_devices
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS physical_devices (
            id {pk_type},
            device_id TEXT NOT NULL UNIQUE,
            device_name TEXT,
            device_type TEXT,
            location TEXT,
            venue TEXT,
            description TEXT,
            active {boolean_type} DEFAULT {'TRUE' if is_postgres() else '1'},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            {', PRIMARY KEY (id)' if is_postgres() else ''}
        );
    """)
    
    # Crear tabla scans
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS scans (
            id {pk_type},
            campaign_code TEXT NOT NULL,
            client TEXT,
            destination TEXT,
            device_id TEXT,
            device_name TEXT,
            location TEXT,
            venue TEXT,
            user_device_type TEXT,
            device_brand TEXT,
            device_model TEXT,
            browser TEXT,
            operating_system TEXT,
            screen_resolution TEXT,
            user_agent TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            session_id TEXT,
            scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            redirect_completed {boolean_type} DEFAULT {'FALSE' if is_postgres() else '0'},
            redirect_timestamp TIMESTAMP,
            duration_seconds REAL,
            campaign_id INTEGER,
            physical_device_id INTEGER
            {', PRIMARY KEY (id)' if is_postgres() else ''}
        );
    """)
    
    # Crear tabla qr_generations
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS qr_generations (
            id {pk_type},
            campaign_id INTEGER,
            physical_device_id INTEGER,
            qr_size INTEGER,
            generated_by TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            {', PRIMARY KEY (id)' if is_postgres() else ''}
        );
    """)
    
    conn.commit()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    if is_postgres():
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            cursor_factory=DictCursor
        )
        return conn
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
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

# ================================
# ENDPOINTS DE PÁGINAS HTML
# ================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal"""
    try:
        # Leer el archivo HTML del index
        with open(os.path.join(os.path.dirname(__file__), "templates", "index.html"), "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Reemplazar variables del template
        base_url = "http://localhost:8000"  # Cambiar según configuración
        html_content = html_content.replace("{{ base_url }}", base_url)
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>QR Tracking System</title></head>
        <body>
            <h1>QR Tracking System v2.5.1</h1>
            <p>Sistema funcionando. Archivos HTML no encontrados.</p>
            <ul>
                <li><a href="/dashboard">Dashboard</a></li>
                <li><a href="/admin/campaigns">Admin Campañas</a></li>
                <li><a href="/devices">Gestión de Dispositivos</a></li>
                <li><a href="/generate-qr">Generar QR</a></li>
                <li><a href="/health">Estado del Sistema</a></li>
            </ul>
        </body>
        </html>
        """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard con analytics"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "dashboard.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard</h1><p>Archivo dashboard.html no encontrado</p>")

@app.get("/admin/campaigns", response_class=HTMLResponse)
async def admin_campaigns():
    """Panel de administración de campañas"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "admin_campaigns.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Admin Campañas</h1><p>Archivo admin_campaigns.html no encontrado</p>")

@app.get("/generate-qr", response_class=HTMLResponse)
async def generate_qr():
    """Generador de códigos QR"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "generate_qr.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Generar QR</h1><p>Archivo generate_qr.html no encontrado</p>")

@app.get("/devices", response_class=HTMLResponse)
async def devices_page():
    """Página de gestión de dispositivos"""
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "devices.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>Dispositivos - QR Tracking</title></head>
        <body>
            <h1>Gestión de Dispositivos</h1>
            <p>Archivo devices.html no encontrado</p>
            <a href="/">← Volver al inicio</a>
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
        
        return {
            "status": "healthy",
            "version": "2.5.1",
            "database": "connected",
            "stats": {
                "campaigns": campaigns_count,
                "devices": devices_count,
                "scans": scans_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
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

def process_scan_background(campaign_code: str, params: dict, user_agent_string: str, client_ip: str, session_id: str, destination: str):
    """Procesar el escaneo en segundo plano para no bloquear la redirección"""
    try:
        device_info = detect_device_info(user_agent_string)
        
        # Registrar el escaneo en la base de datos
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scans (
                    campaign_code, client, destination, device_id, device_name, 
                    location, venue, user_device_type, device_brand, device_model,
                    browser, operating_system, 
                    user_agent, ip_address, session_id, scan_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_code, 
                params.get("client", ""), 
                destination, 
                params.get("device_id", ""), 
                params.get("device_name", ""),
                params.get("location", ""), 
                params.get("venue", ""), 
                device_info["device_type"], 
                device_info["device_brand"],
                device_info["device_model"], 
                device_info["browser"],
                device_info["operating_system"], 
                user_agent_string, 
                client_ip, 
                session_id,
                datetime.now().isoformat()
            ))
            conn.commit()
            
        logger.info(f"QR procesado en background: {campaign_code} desde {device_info['device_brand']} {device_info['device_model']} - IP: {client_ip}")
    except Exception as e:
        logger.error(f"Error procesando tracking asíncrono: {e}")

@app.get("/track")
async def track_qr_scan(request: Request, background_tasks: BackgroundTasks):
    """Endpoint principal hiper-rápido de tracking de QR"""
    try:
        # Obtener parámetros de la URL
        params = dict(request.query_params)
        
        # Parámetros requeridos
        campaign_code = params.get("campaign")
        if not campaign_code:
            raise HTTPException(status_code=400, detail="Parámetro 'campaign' requerido")
            
        destination = params.get("destination", "")
        session_id = str(uuid.uuid4())
        
        # Si no se proporciona destino explícito en params, buscar en la base de datos
        if not destination and campaign_code:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT destination FROM campaigns WHERE campaign_code = ?", (campaign_code,))
                result = cursor.fetchone()
                if result:
                    destination = result["destination"]
        
        # Si aún no hay destino, usar uno por defecto preventivo
        if not destination:
            destination = f"https://google.com/search?q={campaign_code}"
            
        # Detectar la cabecera User-Agent (rápido)
        user_agent = request.headers.get("User-Agent", "")
        client_ip = get_client_ip(request)
        
        # Enviar todo el trabajo pesado a una tarea de fondo (BackgroundTasks)
        background_tasks.add_task(
            process_scan_background,
            campaign_code=campaign_code,
            params=params,
            user_agent_string=user_agent,
            client_ip=client_ip,
            session_id=session_id,
            destination=destination
        )
        
        # Redirigir INSTANTÁNEAMENTE usando 307 Temporary Redirect
        return RedirectResponse(url=destination, status_code=307)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

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

@app.delete("/api/campaigns/{campaign_code}")
async def delete_campaign(campaign_code: str):
    """Eliminar campaña (desactivar)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE campaigns 
                SET active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE campaign_code = ?
            """, (campaign_code,))
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "Campaña no encontrada"}
            
            conn.commit()
        
        logger.info(f"Campaña eliminada (desactivada): {campaign_code}")
        return {"success": True, "message": "Campaña eliminada exitosamente"}
    except Exception as e:
        logger.error(f"Error eliminando campaña: {e}")
        return {"success": False, "error": str(e)}

# ================================
# APIs DE DISPOSITIVOS - CORREGIDAS
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
# APIs DE ANALYTICS
# ================================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Obtener datos completos para el dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM campaigns WHERE active = 1) as active_campaigns,
                    (SELECT COUNT(*) FROM physical_devices WHERE active = 1) as active_devices,
                    (SELECT COUNT(*) FROM scans) as total_scans,
                    (SELECT COUNT(*) FROM scans WHERE redirect_completed = 1) as completed_redirects,
                    (SELECT COUNT(DISTINCT client) FROM scans WHERE client != '') as total_clients
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
            
            # Dispositivos de usuarios
            cursor.execute("""
                SELECT user_device_type as device_type, browser, operating_system, COUNT(*) as count
                FROM scans 
                WHERE user_device_type IS NOT NULL
                GROUP BY user_device_type, browser, operating_system
                ORDER BY count DESC
                LIMIT 10
            """)
            user_devices = [dict(row) for row in cursor.fetchall()]
            
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
                LIMIT 10
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
        
            return {
            "success": True,
            "stats": stats,
            "campaigns": campaigns,
            "user_devices": user_devices,
            "physical_devices": physical_devices,
            "venues": venues
        }
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
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
                start_time = datetime.fromisoformat(result["scan_timestamp"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(completion_time.replace("Z", "+00:00"))
                duration = (end_time - start_time).total_seconds()
            
            # Actualizar el registro
            cursor.execute("""
                UPDATE scans 
                SET redirect_completed = 1, 
                    redirect_timestamp = CURRENT_TIMESTAMP,
                    duration_seconds = ?
                WHERE id = ? AND session_id = ?
            """, (duration, scan_id, session_id))
            conn.commit()
        
        return {"success": True, "message": "Tracking completado"}
    except Exception as e:
        logger.error(f"Error completando tracking: {e}")
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
# APIs ADICIONALES ÚTILES
# ================================

@app.get("/api/scans")
async def get_scans(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    campaign_code: Optional[str] = None,
    device_id: Optional[str] = None,
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

@app.get("/api/campaigns/{campaign_code}/devices")
async def get_campaign_devices(campaign_code: str):
    """Obtener dispositivos físicos asociados a una campaña específica"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la campaña existe
            cursor.execute("SELECT * FROM campaigns WHERE campaign_code = ?", (campaign_code,))
            campaign = cursor.fetchone()
            if not campaign:
                return {"success": False, "error": "Campaña no encontrada"}
            
            # Obtener dispositivos con estadísticas para esta campaña
            cursor.execute("""
                SELECT 
                    pd.device_id,
                    pd.device_name,
                    pd.location,
                    pd.venue,
                    pd.device_type,
                    COUNT(s.id) as scans,
                    COUNT(CASE WHEN s.redirect_completed = 1 THEN 1 END) as completions,
                    ROUND(AVG(s.duration_seconds), 2) as avg_duration,
                    MAX(s.scan_timestamp) as last_scan
                FROM physical_devices pd
                LEFT JOIN scans s ON pd.device_id = s.device_id AND s.campaign_code = ?
                WHERE pd.active = 1
                GROUP BY pd.id
                HAVING COUNT(s.id) > 0
                ORDER BY scans DESC
            """, (campaign_code,))
            
            devices = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "campaign_code": campaign_code,
            "devices": devices,
            "total_devices": len(devices)
        }
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos para campaña {campaign_code}: {e}")
        return {"success": False, "error": str(e)}
    
@app.get("/api/analytics/device-matrix")
async def get_device_matrix():
    """Obtener matriz de tipos de dispositivos por campaña"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener campañas activas
            cursor.execute("""
                SELECT DISTINCT campaign_code 
                FROM scans 
                WHERE campaign_code IN (SELECT campaign_code FROM campaigns WHERE active = 1)
                ORDER BY campaign_code
            """)
            campaigns = [row[0] for row in cursor.fetchall()]
            
            # Obtener tipos de dispositivos
            cursor.execute("""
                SELECT DISTINCT user_device_type 
                FROM scans 
                WHERE user_device_type IS NOT NULL AND user_device_type != ''
                ORDER BY user_device_type
            """)
            device_types = [row[0] for row in cursor.fetchall()]
            
            # Construir matriz
            matrix = {}
            for device_type in device_types:
                matrix[device_type] = {}
                for campaign in campaigns:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM scans 
                        WHERE user_device_type = ? AND campaign_code = ?
                    """, (device_type, campaign))
                    count = cursor.fetchone()[0]
                    matrix[device_type][campaign] = count
        
        return {
            "success": True,
            "matrix": matrix,
            "campaigns": campaigns,
            "device_types": device_types
        }
    except Exception as e:
        logger.error(f"Error obteniendo matriz de dispositivos: {e}")
        return {"success": False, "error": str(e)}    

@app.get("/api/analytics/hourly-matrix")
async def get_hourly_matrix():
    """Obtener matriz de actividad por hora y campaña"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener campañas activas
            cursor.execute("""
                SELECT DISTINCT campaign_code 
                FROM scans 
                WHERE campaign_code IN (SELECT campaign_code FROM campaigns WHERE active = 1)
                ORDER BY campaign_code
            """)
            campaigns = [row[0] for row in cursor.fetchall()]
            
            # Horas del día (0-23)
            hours = list(range(24))
            
            # Construir matriz
            matrix = {}
            for hour in hours:
                matrix[hour] = {}
                for campaign in campaigns:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM scans 
                        WHERE CAST(strftime('%H', scan_timestamp) AS INTEGER) = ? 
                        AND campaign_code = ?
                    """, (hour, campaign))
                    count = cursor.fetchone()[0]
                    matrix[hour][campaign] = count
        
        return {
            "success": True,
            "matrix": matrix,
            "campaigns": campaigns,
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error obteniendo matriz horaria: {e}")
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
            import csv
            import io
            
            output = io.StringIO()
            if scans:
                writer = csv.DictWriter(output, fieldnames=scans[0].keys())
                writer.writeheader()
                writer.writerows(scans)
            
            from fastapi.responses import StreamingResponse
            
            def iter_csv():
                output.seek(0)
                yield output.read()
            
            return StreamingResponse(
                iter_csv(),
                media_type="text/csv",
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

# ================================
# INICIALIZACIÓN
# ================================

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la aplicación"""
    logger.info("Iniciando QR Tracking System v2.5.0")
    init_database()
    logger.info("Sistema iniciado correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("Cerrando QR Tracking System")

# ================================
# EJECUTAR APLICACIÓN
# ================================

if __name__ == "__main__":
    import uvicorn
      
    # Ejecutar servidor
    uvicorn.run(
        "app:app",  # Nombre del archivo principal
        host="0.0.0.0",
        port=8000,
        reload=True,  # Para desarrollo, cambiar a False en producción
        log_level="info"
    )