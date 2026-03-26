"""
QR Tracking System - Módulo de Base de Datos
Abstracción para soportar SQLite (desarrollo) y PostgreSQL (producción)
"""

import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
import logging

# Intentar importar psycopg2 para PostgreSQL
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from config import DATABASE_URL, IS_POSTGRES

logger = logging.getLogger("qr_tracking.database")

# ================================
# ADAPTADOR DE CONSULTAS SQL
# ================================

def adapt_query(query: str) -> str:
    """
    Adapta una consulta SQL de SQLite a PostgreSQL si es necesario.
    
    Cambios principales:
    - ? → %s (placeholders)
    - datetime('now', '-X days') → NOW() - INTERVAL 'X days'
    - AUTOINCREMENT → SERIAL (manejado en schema)
    """
    if not IS_POSTGRES:
        return query
    
    # Reemplazar placeholders ? por %s
    # Usamos un enfoque que no afecta los ? dentro de strings
    adapted = query
    
    # Reemplazar ? por %s (simple, funciona para la mayoría de casos)
    adapted = adapted.replace("?", "%s")
    
    # Adaptar funciones de fecha de SQLite a PostgreSQL
    # datetime('now', '-24 hours') → NOW() - INTERVAL '24 hours'
    adapted = re.sub(
        r"datetime\s*\(\s*'now'\s*,\s*'(-?\d+)\s*(hours?|days?|minutes?|seconds?)'\s*\)",
        r"NOW() - INTERVAL '\1 \2'",
        adapted,
        flags=re.IGNORECASE
    )
    
    # datetime('now') → NOW()
    adapted = re.sub(
        r"datetime\s*\(\s*'now'\s*\)",
        "NOW()",
        adapted,
        flags=re.IGNORECASE
    )
    
    # DATE(column) funciona igual en PostgreSQL, no necesita cambio
    
    # Convertir LIKE a ILIKE para que Postgres sea case-insensitive (como SQLite)
    adapted = re.sub(r'\bLIKE\b', 'ILIKE', adapted, flags=re.IGNORECASE)
    
    # Fix Postgres ROUND(AVG(...), 2) by casting to numeric
    # Because Postgres AVG() returns double precision, which ROUND(..., int) doesn't accept
    adapted = re.sub(
        r"ROUND\s*\(\s*AVG\s*\((.*?)\)\s*,\s*(\d+)\s*\)",
        r"ROUND(CAST(AVG(\1) AS NUMERIC), \2)",
        adapted,
        flags=re.IGNORECASE
    )
    
    # CURRENT_TIMESTAMP funciona igual en ambos
    
    return adapted


# ================================
# CONEXIÓN A BASE DE DATOS
# ================================

def get_postgres_connection():
    """Obtener conexión a PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        raise ImportError("psycopg2 no está instalado. Ejecute: pip install psycopg2-binary")
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def get_sqlite_connection(db_path: str = "qr_tracking.db"):
    """Obtener conexión a SQLite"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_connection():
    """
    Context manager para obtener conexión a la base de datos.
    Detecta automáticamente si usar SQLite o PostgreSQL.
    """
    conn = None
    try:
        if IS_POSTGRES:
            conn = get_postgres_connection()
            # Usar DictCursor para soportar tanto acceso por clave as como por índice
            conn.cursor_factory = psycopg2.extras.DictCursor
        else:
            # Extraer path de SQLite del DATABASE_URL
            db_path = DATABASE_URL.replace("sqlite:///", "")
            conn = get_sqlite_connection(db_path)
        
        yield conn
        
    except Exception as e:
        logger.error(f"Error en conexión a base de datos: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


class DatabaseCursor:
    """
    Wrapper para cursor que adapta resultados entre SQLite y PostgreSQL.
    Permite usar la misma interfaz independientemente de la base de datos.
    """
    
    def __init__(self, cursor, is_postgres: bool = False):
        self.cursor = cursor
        self.is_postgres = is_postgres
        self._lastrowid = None
    
    def execute(self, query: str, params: tuple = None):
        """Ejecutar query adaptándola al tipo de base de datos"""
        adapted_query = adapt_query(query)
        
        if params:
            self.cursor.execute(adapted_query, params)
        else:
            self.cursor.execute(adapted_query)
        
        # Capturar lastrowid para PostgreSQL (requiere RETURNING)
        if self.is_postgres and "INSERT" in query.upper():
            # Para PostgreSQL, necesitamos usar RETURNING para obtener el ID
            pass  # Se maneja en la query específica
        
        return self
    
    def fetchone(self):
        """Obtener un resultado"""
        result = self.cursor.fetchone()
        if result is None:
            return None
        
        # SQLite Row y psycopg2 RealDictRow son compatibles con dict()
        if hasattr(result, 'keys'):
            d = dict(result)
            for i, v in enumerate(result.values() if hasattr(result, 'values') else []):
                d[i] = v
            return d
        return result
    
    def fetchall(self):
        """Obtener todos los resultados"""
        results = self.cursor.fetchall()
        # Convertir a lista de diccionarios
        if results and hasattr(results[0], 'keys'):
            out = []
            for r in results:
                d = dict(r)
                for i, v in enumerate(r.values() if hasattr(r, 'values') else []):
                    d[i] = v
                out.append(d)
            return out
        return results
    
    @property
    def lastrowid(self):
        """Obtener ID del último registro insertado"""
        if self.is_postgres:
            return self._lastrowid
        return self.cursor.lastrowid
    
    @property
    def rowcount(self):
        """Obtener número de filas afectadas"""
        return self.cursor.rowcount


# ================================
# ESQUEMA DE BASE DE DATOS
# ================================

SQLITE_SCHEMA = """
-- Tabla de campañas
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_code TEXT NOT NULL UNIQUE,
    client TEXT NOT NULL,
    destination TEXT NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT 1,
    start_date DATE,
    end_date DATE,
    planned_duration_days INTEGER,
    industry TEXT,
    industry_sub TEXT,
    iab_tier1 TEXT,
    campaign_type TEXT,
    campaign_objective TEXT,
    budget_tier TEXT,
    budget_currency TEXT DEFAULT 'USD',
    dooh_format TEXT,
    creative_type TEXT,
    product_name TEXT,
    venue_category TEXT,
    geo_region TEXT,
    geo_country TEXT DEFAULT 'BR',
    social_amplification BOOLEAN DEFAULT 0,
    social_platforms TEXT,
    influencer_support BOOLEAN DEFAULT 0,
    hashtag TEXT,
    target_scans INTEGER,
    target_unique_visitors INTEGER,
    target_ctr_pct REAL,
    target_audience TEXT,
    campaign_status TEXT DEFAULT 'draft',
    campaign_phase TEXT,
    tags TEXT,
    internal_notes TEXT,
    account_manager TEXT,
    campaign_version INTEGER DEFAULT 1,
    benchmark_group TEXT,
    is_benchmark_eligible BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de dispositivos físicos
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

-- Tabla de escaneos
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
    is_unique BOOLEAN DEFAULT 0,
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
);

-- Tabla de generación de QR
CREATE TABLE IF NOT EXISTS qr_generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    physical_device_id INTEGER,
    qr_size INTEGER,
    generated_by TEXT,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_scans_campaign ON scans(campaign_code);
CREATE INDEX IF NOT EXISTS idx_scans_device ON scans(device_id);
CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(scan_timestamp);
CREATE INDEX IF NOT EXISTS idx_scans_session ON scans(session_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client);
CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address);
CREATE INDEX IF NOT EXISTS idx_scans_utm_source ON scans(utm_source);
"""

POSTGRES_SCHEMA = """
-- Tabla de campañas
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    campaign_code TEXT NOT NULL UNIQUE,
    client TEXT NOT NULL,
    destination TEXT NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    planned_duration_days INTEGER,
    industry VARCHAR(80),
    industry_sub VARCHAR(120),
    iab_tier1 VARCHAR(60),
    campaign_type VARCHAR(60),
    campaign_objective VARCHAR(40),
    budget_tier VARCHAR(20),
    budget_currency VARCHAR(3) DEFAULT 'USD',
    dooh_format VARCHAR(40),
    creative_type VARCHAR(30),
    product_name VARCHAR(150),
    venue_category VARCHAR(40),
    geo_region VARCHAR(80),
    geo_country VARCHAR(2) DEFAULT 'BR',
    social_amplification BOOLEAN DEFAULT FALSE,
    social_platforms VARCHAR(200),
    influencer_support BOOLEAN DEFAULT FALSE,
    hashtag VARCHAR(100),
    target_scans INTEGER,
    target_unique_visitors INTEGER,
    target_ctr_pct DECIMAL(5,2),
    target_audience VARCHAR(100),
    campaign_status VARCHAR(20) DEFAULT 'draft',
    campaign_phase VARCHAR(20),
    tags VARCHAR(300),
    internal_notes TEXT,
    account_manager VARCHAR(100),
    campaign_version INTEGER DEFAULT 1,
    benchmark_group VARCHAR(60),
    is_benchmark_eligible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de dispositivos físicos
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
);

-- Tabla de escaneos
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
    is_unique BOOLEAN DEFAULT FALSE,
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
);

-- Tabla de generación de QR
CREATE TABLE IF NOT EXISTS qr_generations (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER,
    physical_device_id INTEGER,
    qr_size INTEGER,
    generated_by TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_scans_campaign ON scans(campaign_code);
CREATE INDEX IF NOT EXISTS idx_scans_device ON scans(device_id);
CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(scan_timestamp);
CREATE INDEX IF NOT EXISTS idx_scans_session ON scans(session_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client);
CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(ip_address);
CREATE INDEX IF NOT EXISTS idx_scans_utm_source ON scans(utm_source);
"""


def init_database():
    """Inicializar la base de datos con el esquema apropiado"""
    logger.info(f"Inicializando base de datos ({'PostgreSQL' if IS_POSTGRES else 'SQLite'})...")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Seleccionar esquema según el tipo de base de datos
            schema = POSTGRES_SCHEMA if IS_POSTGRES else SQLITE_SCHEMA
            
            # Ejecutar cada statement por separado
            for statement in schema.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            conn.commit()
            
            # Verificar tablas creadas
            if IS_POSTGRES:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            
            tables = cursor.fetchall()
            table_names = [t[0] if isinstance(t, tuple) else list(t.values())[0] for t in tables]
            logger.info(f"Tablas en base de datos: {table_names}")
            
        logger.info("Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


def execute_query(query: str, params: tuple = None, fetch: str = None) -> Any:
    """
    Ejecutar una query de forma simplificada.
    
    Args:
        query: SQL query
        params: Parámetros para la query
        fetch: 'one', 'all', o None
    
    Returns:
        Resultado de la query o None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        adapted_query = adapt_query(query)
        
        if params:
            cursor.execute(adapted_query, params)
        else:
            cursor.execute(adapted_query)
        
        if fetch == 'one':
            result = cursor.fetchone()
            return dict(result) if result and hasattr(result, 'keys') else result
        elif fetch == 'all':
            results = cursor.fetchall()
            if results and hasattr(results[0], 'keys'):
                return [dict(row) for row in results]
            return results
        else:
            conn.commit()
            return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None


# ================================
# FUNCIONES DE UTILIDAD
# ================================

def check_connection() -> Dict[str, Any]:
    """Verificar conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if IS_POSTGRES:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                db_type = "PostgreSQL"
            else:
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()
                db_type = "SQLite"
            
            return {
                "status": "connected",
                "type": db_type,
                "version": str(version) if version else "unknown"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
