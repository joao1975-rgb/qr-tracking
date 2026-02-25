"""
QR Tracking System - Configuración
Maneja variables de entorno para desarrollo local y producción en Cloud Run
"""

import os
from typing import Optional

# ================================
# CONFIGURACIÓN DE BASE DE DATOS
# ================================

# URL de conexión a la base de datos
# - Desarrollo (SQLite): sqlite:///qr_tracking.db
# - Producción (PostgreSQL): postgresql://user:pass@host/db
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///qr_tracking.db"  # Default para desarrollo local
)

# Detectar si estamos usando PostgreSQL
IS_POSTGRES: bool = DATABASE_URL.startswith("postgresql")

# ================================
# CONFIGURACIÓN DEL SERVIDOR
# ================================

# Puerto del servidor (Cloud Run usa 8080 por defecto)
PORT: int = int(os.getenv("PORT", "8000"))

# Host del servidor
HOST: str = os.getenv("HOST", "0.0.0.0")

# Entorno de ejecución
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# URL base del servidor (para generar URLs de tracking)
# En producción, esto será tu dominio de Cloud Run
BASE_URL: str = os.getenv("BASE_URL", f"http://localhost:{PORT}")

# ================================
# CONFIGURACIÓN DE SEGURIDAD
# ================================

# Secret key para sesiones y tokens
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Orígenes CORS permitidos
CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

# ================================
# CONFIGURACIÓN DE LOGGING
# ================================

# Nivel de logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Directorio de logs (en Cloud Run usar /tmp o logging a stdout)
LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")

# ================================
# CONFIGURACIÓN DE BACKUPS
# ================================

# Directorio de backups (solo aplica para SQLite local)
BACKUPS_DIR: str = os.getenv("BACKUPS_DIR", "backups")

# Habilitar backups automáticos (deshabilitado en Cloud Run)
ENABLE_BACKUPS: bool = os.getenv("ENABLE_BACKUPS", "true").lower() == "true" and not IS_POSTGRES

# ================================
# CONFIGURACIÓN DE QR
# ================================

# Tamaño por defecto de los códigos QR
DEFAULT_QR_SIZE: int = int(os.getenv("DEFAULT_QR_SIZE", "300"))

# ================================
# INFORMACIÓN DE DEBUG
# ================================

def print_config():
    """Imprimir configuración actual (oculta información sensible)"""
    print("=" * 60)
    print("QR TRACKING SYSTEM - CONFIGURACIÓN")
    print("=" * 60)
    print(f"Entorno: {ENVIRONMENT}")
    print(f"Base de datos: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}")
    print(f"Host: {HOST}:{PORT}")
    print(f"URL Base: {BASE_URL}")
    print(f"Backups habilitados: {ENABLE_BACKUPS}")
    print(f"Nivel de log: {LOG_LEVEL}")
    print("=" * 60)
