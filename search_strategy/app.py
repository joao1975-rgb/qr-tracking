from flask import Flask, render_template, request, redirect, url_for, jsonify
import re
import os
import json
from urllib.parse import urlparse, unquote
import logging
from datetime import datetime
import sqlite3
import hashlib
import uuid
from contextlib import contextmanager
from functools import wraps

# Crear la instancia de Flask
app = Flask(__name__)

# Configuración básica de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu-clave-secreta-super-segura-aqui')
app.config['DATABASE'] = 'tracking.db'

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar base de datos
def init_db():
    """Inicializar la base de datos con las tablas necesarias"""
    with sqlite3.connect(app.config['DATABASE']) as conn:
        # Tabla principal de tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tracking_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                campaign TEXT NOT NULL,
                client TEXT NOT NULL,
                destination TEXT NOT NULL,
                device_id TEXT DEFAULT 'unknown',
                
                -- Datos del dispositivo del usuario
                user_agent TEXT,
                device_type TEXT,
                browser TEXT,
                operating_system TEXT,
                screen_resolution TEXT,
                
                -- Datos de red
                ip_address TEXT,
                referrer TEXT,
                
                -- Datos temporales
                access_time TIMESTAMP NOT NULL,
                redirect_time TIMESTAMP,
                duration_seconds INTEGER,
                
                -- Datos de interacción
                completed_redirect BOOLEAN DEFAULT FALSE,
                
                -- Metadatos
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de campañas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_code TEXT UNIQUE NOT NULL,
                client TEXT NOT NULL,
                destination TEXT NOT NULL,
                description TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de dispositivos físicos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS physical_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL,
                location TEXT NOT NULL,
                device_type TEXT NOT NULL,
                venue TEXT NOT NULL,
                installation_date DATE,
                active BOOLEAN DEFAULT TRUE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear algunas campañas de ejemplo (ampliadas)
        campaigns_example = [
            ('metro_plaza_venezuela', 'Coca Cola', 'https://instagram.com/cocacola', 'Anuncio Metro Plaza Venezuela'),
            ('cc_sambil', 'Samsung', 'https://www.samsung.com/ve', 'Centro Comercial Sambil'),
            ('terminal_la_bandera', 'McDonald\'s', 'https://instagram.com/mcdonaldsve', 'Terminal La Bandera'),
            ('autopista_francisco_fajardo', 'Pepsi', 'https://www.pepsi.com.ve', 'Valla Autopista Francisco Fajardo'),
            ('cc_ccct', 'Apple', 'https://www.apple.com/ve', 'Centro Comercial Ciudad Tamanaco'),
            ('metro_capitolio', 'Nike', 'https://instagram.com/nike', 'Estación Metro Capitolio'),
            
            # Nuevas campañas de ejemplo
            ('promocion_black_friday_2024', 'Nike', 'https://www.nike.com/ve/promociones', 'Promoción especial Black Friday'),
            ('descuento_navidad', 'Adidas', 'https://www.adidas.com.ve/ofertas', 'Descuentos navideños'),
            ('nueva_coleccion_2024', 'Zara', 'https://www.zara.com/ve/nueva-coleccion', 'Nueva colección primavera'),
            ('ofertas_fin_año', 'H&M', 'https://www2.hm.com/es_es/ofertas', 'Ofertas especiales fin de año'),
            ('lanzamiento_iphone', 'Apple', 'https://www.apple.com/ve/iphone', 'Lanzamiento nuevo iPhone'),
            ('promocion_pizza', 'Dominos', 'https://www.dominos.com.ve/promociones', 'Promoción 2x1 en pizzas'),
            ('campaña_verano', 'Cerveza Polar', 'https://www.empresas-polar.com/', 'Campaña de verano Polar'),
            ('festival_musica', 'Red Bull', 'https://www.redbull.com/ve-es/events', 'Festival de música patrocinado'),
            ('descuento_estudiantes', 'Spotify', 'https://www.spotify.com/ve/student/', 'Descuento especial estudiantes'),
            ('nueva_sucursal', 'Starbucks', 'https://www.starbucks.com.ve/ubicaciones', 'Inauguración nueva sucursal')
        ]
        
        for campaign in campaigns_example:
            conn.execute('''
                INSERT OR IGNORE INTO campaigns (campaign_code, client, destination, description) 
                VALUES (?, ?, ?, ?)
            ''', campaign)
        
        # Dispositivos físicos de ejemplo (ampliados)
        devices_example = [
            ('totem_entrada_principal', 'Totem Digital Principal', 'Entrada Principal', 'Totem Interactivo', 'CC Sambil'),
            ('pantalla_planta_baja', 'Pantalla LED Planta Baja', 'Planta Baja - Zona Central', 'Pantalla LED', 'CC Sambil'),
            ('kiosco_food_court', 'Kiosco Food Court', 'Food Court - Mesa 15', 'Kiosco Interactivo', 'CC Sambil'),
            ('totem_estacionamiento_A', 'Totem Estacionamiento A', 'Estacionamiento Nivel A', 'Totem Digital', 'CC Sambil'),
            ('pantalla_metro_entrada', 'Pantalla Entrada Metro', 'Entrada Estación Metro', 'Pantalla Digital', 'Metro Plaza Venezuela'),
            ('totem_terminal_sur', 'Totem Terminal Sur', 'Área de Espera Sur', 'Totem Interactivo', 'Terminal La Bandera'),
            ('pantalla_autopista_norte', 'Pantalla Valla Norte', 'Km 15 Sentido Norte', 'Valla Digital', 'Autopista Francisco Fajardo'),
            ('pantalla_autopista_sur', 'Pantalla Valla Sur', 'Km 15 Sentido Sur', 'Valla Digital', 'Autopista Francisco Fajardo'),
            ('totem_ccct_nivel1', 'Totem CCCT Nivel 1', 'Nivel 1 - Entrada Principal', 'Totem Interactivo', 'CC Ciudad Tamanaco'),
            ('pantalla_metro_capitolio', 'Pantalla Metro Capitolio', 'Andén Principal', 'Pantalla LED', 'Metro Capitolio'),
            
            # Nuevos dispositivos
            ('tablet_starbucks_altamira', 'Tablet Mesa Starbucks', 'Mesa Principal', 'Tablet Interactivo', 'Starbucks Altamira'),
            ('pantalla_universidad_ucv', 'Pantalla Digital UCV', 'Plaza Cubierta', 'Pantalla LED', 'Universidad Central'),
            ('kiosco_maiquetia', 'Kiosco Aeropuerto', 'Terminal Nacional Llegadas', 'Kiosco Interactivo', 'Aeropuerto Maiquetía'),
            ('totem_plaza_venezuela', 'Totem Plaza Venezuela', 'Centro de la Plaza', 'Totem Digital', 'Plaza Venezuela'),
            ('pantalla_cine_sambil', 'Pantalla Cines Unidos', 'Lobby de Cines', 'Pantalla LED', 'Cines Unidos Sambil')
        ]
        
        for device in devices_example:
            conn.execute('''
                INSERT OR IGNORE INTO physical_devices 
                (device_id, device_name, location, device_type, venue) 
                VALUES (?, ?, ?, ?, ?)
            ''', device)
        
        conn.commit()
        logger.info("Base de datos con tracking de dispositivos inicializada correctamente")

@contextmanager
def get_db_connection():
    """Context manager para conexiones a la base de datos"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_device_info(user_agent):
    """Extraer información del dispositivo desde el User-Agent"""
    ua_lower = user_agent.lower() if user_agent else ''
    
    # Detectar tipo de dispositivo
    if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        device_type = 'Mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # Detectar navegador
    if 'chrome' in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = 'Safari'
    elif 'edge' in ua_lower:
        browser = 'Edge'
    else:
        browser = 'Other'
    
    # Detectar sistema operativo
    if 'android' in ua_lower:
        os_name = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        os_name = 'iOS'
    elif 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'mac' in ua_lower:
        os_name = 'macOS'
    elif 'linux' in ua_lower:
        os_name = 'Linux'
    else:
        os_name = 'Other'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'operating_system': os_name
    }

def get_campaign_info(campaign_code):
    """Obtener información de la campaña desde la base de datos"""
    with get_db_connection() as conn:
        result = conn.execute(
            'SELECT * FROM campaigns WHERE campaign_code = ? AND active = TRUE',
            (campaign_code,)
        ).fetchone()
        
        if result:
            return dict(result)
    return None

def get_physical_device_info(device_id):
    """Obtener información del dispositivo físico"""
    with get_db_connection() as conn:
        result = conn.execute(
            'SELECT * FROM physical_devices WHERE device_id = ? AND active = TRUE',
            (device_id,)
        ).fetchone()
        
        if result:
            return dict(result)
    return None

def get_campaign_with_stats(campaign_code):
    """Obtener campaña con estadísticas básicas"""
    with get_db_connection() as conn:
        campaign = conn.execute(
            'SELECT * FROM campaigns WHERE campaign_code = ?',
            (campaign_code,)
        ).fetchone()
        
        if not campaign:
            return None
        
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total_scans,
                COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completions,
                MAX(access_time) as last_scan
            FROM tracking_data
            WHERE campaign = ?
        ''', (campaign_code,)).fetchone()
        
        campaign_dict = dict(campaign)
        campaign_dict.update(dict(stats) if stats else {})
        
        return campaign_dict

# Middleware para validación de admin (opcional - agregar autenticación básica)
def require_admin():
    """Decorador para requerir autenticación de admin (implementar según necesidades)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Aquí podrías agregar validación de autenticación
            # Por ejemplo, verificar un token de admin o sesión
            
            # Por ahora, permitir acceso libre
            # En producción, implementar autenticación real
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# RUTAS PRINCIPALES
# ============================================================================

@app.route('/')
def index():
    """Página principal del escáner QR (mantenida para compatibilidad)"""
    try:
        logger.info("Accediendo a página principal")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error en ruta principal: {e}")
        return f"Error cargando página: {str(e)}", 500

@app.route('/track')
def track_access():
    """Página intermedia de tracking - captura datos y redirige"""
    try:
        # Obtener parámetros de la URL
        campaign = request.args.get('campaign', '').strip()
        destination = request.args.get('destination', '').strip()
        client = request.args.get('client', '').strip()
        device_id = request.args.get('device_id', 'unknown_device').strip()
        
        logger.info(f"Tracking access - Campaign: {campaign}, Client: {client}, Device: {device_id}")
        
        # Obtener información del dispositivo físico
        physical_device_info = get_physical_device_info(device_id)
        device_location = physical_device_info['location'] if physical_device_info else 'Ubicación desconocida'
        device_venue = physical_device_info['venue'] if physical_device_info else 'Venue desconocido'
        
        # Si no hay campaña, usar parámetros de destino directo
        if not campaign and destination:
            campaign = 'direct_link'
            client = 'unknown'
        elif campaign and not destination:
            # Buscar campaña en base de datos
            campaign_info = get_campaign_info(campaign)
            if campaign_info:
                destination = campaign_info['destination']
                client = campaign_info['client']
            else:
                logger.warning(f"Campaña no encontrada: {campaign}")
                return render_template('error.html', 
                    error_message="Campaña no válida o expirada"), 404
        
        if not destination:
            logger.warning("No se proporcionó destino")
            return render_template('error.html', 
                error_message="Enlace QR inválido"), 400
        
        # Generar ID único para esta sesión
        session_id = str(uuid.uuid4())
        
        # Capturar datos del dispositivo del usuario
        user_agent = request.headers.get('User-Agent', '')
        device_info = get_device_info(user_agent)
        
        # Datos de la request
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                        request.environ.get('REMOTE_ADDR', ''))
        referrer = request.referrer or ''
        
        # Datos adicionales del cliente (JavaScript los enviará)
        access_time = datetime.now()
        
        # Guardar datos iniciales en la base de datos
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO tracking_data (
                    session_id, campaign, client, destination, device_id,
                    user_agent, device_type, browser, operating_system,
                    ip_address, referrer, access_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, campaign, client, destination, device_id,
                user_agent, device_info['device_type'], 
                device_info['browser'], device_info['operating_system'],
                ip_address, referrer, access_time
            ))
            conn.commit()
        
        logger.info(f"Datos de tracking guardados - Session: {session_id}, Device: {device_id}")
        
        # Renderizar página intermedia
        return render_template('tracking.html',
            session_id=session_id,
            destination=destination,
            client=client,
            campaign=campaign,
            device_id=device_id,
            device_location=device_location,
            device_venue=device_venue
        )
        
    except Exception as e:
        logger.error(f"Error en tracking: {e}")
        return render_template('error.html', 
            error_message="Error procesando enlace"), 500

@app.route('/collect-data', methods=['POST'])
def collect_additional_data():
    """Endpoint para recibir datos adicionales del cliente (JavaScript)"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID requerido'}), 400
        
        # Datos adicionales del dispositivo
        screen_resolution = data.get('screen_resolution', '')
        viewport_size = data.get('viewport_size', '')
        timezone = data.get('timezone', '')
        language = data.get('language', '')
        
        # Actualizar datos en la base de datos
        with get_db_connection() as conn:
            conn.execute('''
                UPDATE tracking_data 
                SET screen_resolution = ?
                WHERE session_id = ?
            ''', (screen_resolution, session_id))
            conn.commit()
        
        logger.info(f"Datos adicionales actualizados - Session: {session_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error actualizando datos: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500

@app.route('/complete-redirect', methods=['POST'])
def complete_redirect():
    """Marcar que se completó la redirección"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False}), 400
        
        redirect_time = datetime.now()
        
        with get_db_connection() as conn:
            # Obtener tiempo de acceso para calcular duración
            result = conn.execute(
                'SELECT access_time FROM tracking_data WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if result:
                access_time = datetime.fromisoformat(result['access_time'])
                duration = int((redirect_time - access_time).total_seconds())
                
                conn.execute('''
                    UPDATE tracking_data 
                    SET redirect_time = ?, duration_seconds = ?, completed_redirect = TRUE
                    WHERE session_id = ?
                ''', (redirect_time, duration, session_id))
                conn.commit()
        
        logger.info(f"Redirección completada - Session: {session_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error marcando redirección: {e}")
        return jsonify({'success': False}), 500

# ============================================================================
# RUTAS DE ADMINISTRACIÓN Y DASHBOARD
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """Dashboard de estadísticas para anunciantes"""
    try:
        with get_db_connection() as conn:
            # Estadísticas generales
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completed_redirects,
                    COUNT(DISTINCT campaign) as active_campaigns,
                    COUNT(DISTINCT client) as total_clients,
                    COUNT(DISTINCT device_id) as physical_devices_used
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-30 days')
            ''').fetchone()
            
            # Estadísticas por campaña
            campaigns_stats = conn.execute('''
                SELECT 
                    campaign, client, destination,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completions,
                    AVG(duration_seconds) as avg_duration,
                    MAX(access_time) as last_scan,
                    COUNT(DISTINCT device_id) as devices_used
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-30 days')
                GROUP BY campaign, client, destination
                ORDER BY scans DESC
            ''').fetchall()
            
            # Estadísticas por dispositivo físico
            device_stats = conn.execute('''
                SELECT 
                    td.device_id,
                    pd.device_name,
                    pd.location,
                    pd.venue,
                    pd.device_type,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN td.completed_redirect = TRUE THEN 1 END) as completions,
                    AVG(td.duration_seconds) as avg_duration
                FROM tracking_data td
                LEFT JOIN physical_devices pd ON td.device_id = pd.device_id
                WHERE DATE(td.access_time) >= DATE('now', '-30 days')
                GROUP BY td.device_id, pd.device_name, pd.location, pd.venue, pd.device_type
                ORDER BY scans DESC
            ''').fetchall()
            
            # Estadísticas por dispositivo del usuario
            user_device_stats = conn.execute('''
                SELECT 
                    device_type, browser, operating_system,
                    COUNT(*) as count
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-30 days')
                GROUP BY device_type, browser, operating_system
                ORDER BY count DESC
                LIMIT 10
            ''').fetchall()
            
            # Actividad por horas
            hourly_stats = conn.execute('''
                SELECT 
                    strftime('%H', access_time) as hour,
                    COUNT(*) as scans
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-7 days')
                GROUP BY hour
                ORDER BY hour
            ''').fetchall()
            
            # Top venues/ubicaciones
            venue_stats = conn.execute('''
                SELECT 
                    pd.venue,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN td.completed_redirect = TRUE THEN 1 END) as completions,
                    COUNT(DISTINCT td.device_id) as devices_count
                FROM tracking_data td
                LEFT JOIN physical_devices pd ON td.device_id = pd.device_id
                WHERE DATE(td.access_time) >= DATE('now', '-30 days')
                GROUP BY pd.venue
                ORDER BY scans DESC
            ''').fetchall()
        
        return render_template('dashboard.html',
            stats=dict(stats),
            campaigns=campaigns_stats,
            physical_devices=device_stats,
            user_devices=user_device_stats,
            hourly=hourly_stats,
            venues=venue_stats
        )
        
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return f"Error cargando dashboard: {str(e)}", 500

@app.route('/admin')
def admin_redirect():
    """Redirigir a administración de campañas"""
    return redirect(url_for('admin_campaigns'))

@app.route('/admin/campaigns')
def admin_campaigns():
    """Página de administración de campañas"""
    try:
        # Puedes agregar autenticación aquí en el futuro
        return render_template('admin_campaigns.html')
    except Exception as e:
        logger.error(f"Error en página de administración: {e}")
        return f"Error: {str(e)}", 500

@app.route('/generate-qr')
def generate_qr_page():
    """Página para generar códigos QR de campañas"""
    try:
        with get_db_connection() as conn:
            campaigns = conn.execute('''
                SELECT * FROM campaigns WHERE active = TRUE ORDER BY created_at DESC
            ''').fetchall()
            
            devices = conn.execute('''
                SELECT * FROM physical_devices WHERE active = TRUE ORDER BY venue, location
            ''').fetchall()
        
        return render_template('generate_qr.html', 
            campaigns=campaigns, 
            physical_devices=devices
        )
        
    except Exception as e:
        logger.error(f"Error en página de generar QR: {e}")
        return f"Error: {str(e)}", 500

@app.route('/devices')
def devices_page():
    """Página de administración de dispositivos físicos"""
    try:
        with get_db_connection() as conn:
            devices = conn.execute('''
                SELECT 
                    pd.*,
                    COUNT(td.id) as total_scans,
                    MAX(td.access_time) as last_scan
                FROM physical_devices pd
                LEFT JOIN tracking_data td ON pd.device_id = td.device_id 
                    AND DATE(td.access_time) >= DATE('now', '-30 days')
                GROUP BY pd.id
                ORDER BY pd.venue, pd.location
            ''').fetchall()
        
        return render_template('devices.html', devices=devices)
        
    except Exception as e:
        logger.error(f"Error en página de dispositivos: {e}")
        return f"Error: {str(e)}", 500

# ============================================================================
# API RUTAS PARA ADMINISTRACIÓN DE CAMPAÑAS
# ============================================================================

@app.route('/api/campaigns', methods=['GET'])
def api_campaigns():
    """API para obtener campañas disponibles"""
    try:
        with get_db_connection() as conn:
            campaigns = conn.execute('''
                SELECT campaign_code, client, destination, description, active, created_at
                FROM campaigns
                WHERE active = TRUE
                ORDER BY created_at DESC
            ''').fetchall()
        
        return jsonify({
            'success': True,
            'campaigns': [dict(campaign) for campaign in campaigns]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo campañas: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    """Crear nueva campaña"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['campaign_code', 'client', 'destination']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'Campo {field} es requerido'
                }), 400
        
        # Validar formato del código de campaña
        campaign_code = data['campaign_code'].strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', campaign_code):
            return jsonify({
                'success': False,
                'error': 'El código de campaña solo puede contener letras, números, guiones y guiones bajos'
            }), 400
        
        # Validar URL de destino
        destination = data['destination'].strip()
        try:
            result = urlparse(destination)
            if not all([result.scheme, result.netloc]):
                raise ValueError("URL inválida")
        except:
            return jsonify({
                'success': False,
                'error': 'La URL de destino no es válida'
            }), 400
        
        with get_db_connection() as conn:
            # Verificar que no existe la campaña
            existing = conn.execute(
                'SELECT id FROM campaigns WHERE campaign_code = ?',
                (campaign_code,)
            ).fetchone()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Ya existe una campaña con ese código'
                }), 409
            
            # Crear nueva campaña
            conn.execute('''
                INSERT INTO campaigns (campaign_code, client, destination, description, active)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                campaign_code,
                data['client'].strip(),
                destination,
                data.get('description', '').strip() or None,
                data.get('active', True)
            ))
            conn.commit()
        
        logger.info(f"Nueva campaña creada: {campaign_code} para {data['client']}")
        
        return jsonify({
            'success': True,
            'message': 'Campaña creada exitosamente',
            'campaign_code': campaign_code,
            'tracking_url': f"{request.host_url}track?campaign={campaign_code}"
        })
        
    except Exception as e:
        logger.error(f"Error creando campaña: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/campaigns/<campaign_code>', methods=['PUT'])
def update_campaign(campaign_code):
    """Actualizar campaña existente"""
    try:
        data = request.get_json()
        
        with get_db_connection() as conn:
            # Verificar que existe la campaña
            existing = conn.execute(
                'SELECT id FROM campaigns WHERE campaign_code = ?',
                (campaign_code,)
            ).fetchone()
            
            if not existing:
                return jsonify({
                    'success': False,
                    'error': 'Campaña no encontrada'
                }), 404
            
            # Preparar campos a actualizar
            update_fields = []
            update_values = []
            
            if 'client' in data:
                update_fields.append('client = ?')
                update_values.append(data['client'].strip())
            
            if 'destination' in data:
                # Validar URL
                try:
                    result = urlparse(data['destination'])
                    if not all([result.scheme, result.netloc]):
                        raise ValueError("URL inválida")
                    update_fields.append('destination = ?')
                    update_values.append(data['destination'].strip())
                except:
                    return jsonify({
                        'success': False,
                        'error': 'La URL de destino no es válida'
                    }), 400
            
            if 'description' in data:
                update_fields.append('description = ?')
                update_values.append(data['description'].strip() or None)
            
            if 'active' in data:
                update_fields.append('active = ?')
                update_values.append(data['active'])
            
            if not update_fields:
                return jsonify({
                    'success': False,
                    'error': 'No hay campos para actualizar'
                }), 400
            
            # Agregar campo de actualización de timestamp
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now())
            
            # Ejecutar actualización
            update_values.append(campaign_code)
            query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE campaign_code = ?"
            
            conn.execute(query, update_values)
            conn.commit()
        
        logger.info(f"Campaña actualizada: {campaign_code}")
        
        return jsonify({
            'success': True,
            'message': 'Campaña actualizada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error actualizando campaña: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/campaigns/<campaign_code>', methods=['DELETE'])
def delete_campaign(campaign_code):
    """Eliminar campaña (soft delete)"""
    try:
        with get_db_connection() as conn:
            # Verificar que existe la campaña
            existing = conn.execute(
                'SELECT id FROM campaigns WHERE campaign_code = ?',
                (campaign_code,)
            ).fetchone()
            
            if not existing:
                return jsonify({
                    'success': False,
                    'error': 'Campaña no encontrada'
                }), 404
            
            # Soft delete - marcar como inactiva
            conn.execute(
                'UPDATE campaigns SET active = FALSE, updated_at = ? WHERE campaign_code = ?',
                (datetime.now(), campaign_code)
            )
            conn.commit()
        
        logger.info(f"Campaña desactivada: {campaign_code}")
        
        return jsonify({
            'success': True,
            'message': 'Campaña desactivada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error eliminando campaña: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/campaigns/<campaign_code>/stats')
def campaign_stats(campaign_code):
    """Obtener estadísticas de una campaña específica"""
    try:
        with get_db_connection() as conn:
            # Verificar que existe la campaña
            campaign = conn.execute(
                'SELECT * FROM campaigns WHERE campaign_code = ?',
                (campaign_code,)
            ).fetchone()
            
            if not campaign:
                return jsonify({
                    'success': False,
                    'error': 'Campaña no encontrada'
                }), 404
            
            # Obtener estadísticas
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completed_redirects,
                    AVG(duration_seconds) as avg_duration,
                    MAX(access_time) as last_scan,
                    COUNT(DISTINCT device_id) as unique_devices,
                    COUNT(DISTINCT ip_address) as unique_ips
                FROM tracking_data
                WHERE campaign = ? AND DATE(access_time) >= DATE('now', '-30 days')
            ''', (campaign_code,)).fetchone()
            
            # Estadísticas por dispositivo
            device_stats = conn.execute('''
                SELECT 
                    device_type,
                    browser,
                    operating_system,
                    COUNT(*) as count
                FROM tracking_data
                WHERE campaign = ? AND DATE(access_time) >= DATE('now', '-30 days')
                GROUP BY device_type, browser, operating_system
                ORDER BY count DESC
                LIMIT 10
            ''', (campaign_code,)).fetchall()
            
            # Actividad por días
            daily_stats = conn.execute('''
                SELECT 
                    DATE(access_time) as date,
                    COUNT(*) as scans,
                    COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completions
                FROM tracking_data
                WHERE campaign = ? AND DATE(access_time) >= DATE('now', '-30 days')
                GROUP BY DATE(access_time)
                ORDER BY date DESC
            ''', (campaign_code,)).fetchall()
        
        return jsonify({
            'success': True,
            'campaign': dict(campaign),
            'stats': dict(stats) if stats else {},
            'device_stats': [dict(row) for row in device_stats],
            'daily_stats': [dict(row) for row in daily_stats]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de campaña: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/api/campaigns/bulk', methods=['POST'])
def bulk_create_campaigns():
    """Crear múltiples campañas en lote"""
    try:
        data = request.get_json()
        campaigns = data.get('campaigns', [])
        
        if not campaigns:
            return jsonify({
                'success': False,
                'error': 'No se proporcionaron campañas'
            }), 400
        
        results = {
            'created': [],
            'errors': []
        }
        
        with get_db_connection() as conn:
            for campaign in campaigns:
                try:
                    # Validar campos requeridos
                    if not all(field in campaign for field in ['campaign_code', 'client', 'destination']):
                        results['errors'].append({
                            'campaign': campaign.get('campaign_code', 'unknown'),
                            'error': 'Campos requeridos faltantes'
                        })
                        continue
                    
                    campaign_code = campaign['campaign_code'].strip()
                    
                    # Validar formato
                    if not re.match(r'^[a-zA-Z0-9_-]+$', campaign_code):
                        results['errors'].append({
                            'campaign': campaign_code,
                            'error': 'Formato de código inválido'
                        })
                        continue
                    
                    # Verificar duplicados
                    existing = conn.execute(
                        'SELECT id FROM campaigns WHERE campaign_code = ?',
                        (campaign_code,)
                    ).fetchone()
                    
                    if existing:
                        results['errors'].append({
                            'campaign': campaign_code,
                            'error': 'Ya existe'
                        })
                        continue
                    
                    # Crear campaña
                    conn.execute('''
                        INSERT INTO campaigns (campaign_code, client, destination, description, active)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        campaign_code,
                        campaign['client'].strip(),
                        campaign['destination'].strip(),
                        campaign.get('description', '').strip() or None,
                        campaign.get('active', True)
                    ))
                    
                    results['created'].append({
                        'campaign_code': campaign_code,
                        'client': campaign['client'],
                        'tracking_url': f"{request.host_url}track?campaign={campaign_code}"
                    })
                    
                except Exception as e:
                    results['errors'].append({
                        'campaign': campaign.get('campaign_code', 'unknown'),
                        'error': str(e)
                    })
            
            conn.commit()
        
        logger.info(f"Creación en lote completada: {len(results['created'])} exitosas, {len(results['errors'])} errores")
        
        return jsonify({
            'success': True,
            'message': f"Proceso completado: {len(results['created'])} creadas, {len(results['errors'])} errores",
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error en creación en lote: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ============================================================================
# API RUTAS PARA DISPOSITIVOS FÍSICOS
# ============================================================================

@app.route('/api/devices')
def api_devices():
    """API para obtener dispositivos físicos disponibles"""
    try:
        with get_db_connection() as conn:
            devices = conn.execute('''
                SELECT device_id, device_name, location, device_type, venue, active
                FROM physical_devices
                WHERE active = TRUE
                ORDER BY venue, location
            ''').fetchall()
        
        return jsonify({
            'success': True,
            'devices': [dict(device) for device in devices]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500

@app.route('/api/devices', methods=['POST'])
def create_device():
    """Crear nuevo dispositivo físico"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['device_id', 'device_name', 'location', 'device_type', 'venue']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'Campo {field} es requerido'
                }), 400
        
        device_id = data['device_id'].strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', device_id):
            return jsonify({
                'success': False,
                'error': 'El ID del dispositivo solo puede contener letras, números, guiones y guiones bajos'
            }), 400
        
        with get_db_connection() as conn:
            # Verificar que no existe el dispositivo
            existing = conn.execute(
                'SELECT id FROM physical_devices WHERE device_id = ?',
                (device_id,)
            ).fetchone()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Ya existe un dispositivo con ese ID'
                }), 409
            
            # Crear nuevo dispositivo
            conn.execute('''
                INSERT INTO physical_devices 
                (device_id, device_name, location, device_type, venue, notes, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_id,
                data['device_name'].strip(),
                data['location'].strip(),
                data['device_type'].strip(),
                data['venue'].strip(),
                data.get('notes', '').strip() or None,
                data.get('active', True)
            ))
            conn.commit()
        
        logger.info(f"Nuevo dispositivo creado: {device_id} en {data['venue']}")
        
        return jsonify({
            'success': True,
            'message': 'Dispositivo creado exitosamente',
            'device_id': device_id
        })
        
    except Exception as e:
        logger.error(f"Error creando dispositivo: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ============================================================================
# RUTAS DE COMPATIBILIDAD Y UTILIDAD
# ============================================================================

@app.route('/scan', methods=['POST'])
def scan_qr():
    """Procesar código QR escaneado - redirige al sistema de tracking"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
        
        qr_data = data.get('qr_data', '').strip()
        if not qr_data:
            return jsonify({'success': False, 'error': 'Código QR vacío'}), 400
        
        # Si es una URL de nuestro sistema de tracking, procesarla
        if 'track?' in qr_data or qr_data.startswith(request.host_url):
            return jsonify({
                'success': True,
                'type': 'tracking_url',
                'redirect_url': qr_data,
                'message': 'Enlace de tracking detectado'
            })
        
        # Si es una URL normal, redirigir al sistema de tracking
        from urllib.parse import quote
        tracking_url = f"{request.host_url}track?destination={quote(qr_data)}"
        
        return jsonify({
            'success': True,
            'type': 'url',
            'redirect_url': tracking_url,
            'message': 'URL procesada para tracking'
        })
        
    except Exception as e:
        logger.error(f"Error procesando QR: {e}")
        return jsonify({'success': False, 'error': 'Error interno'}), 500

# ============================================================================
# RUTAS DE SALUD Y UTILIDAD
# ============================================================================

@app.route('/health')
def health_check():
    """Endpoint de verificación de salud"""
    try:
        # Verificar conexión a base de datos
        with get_db_connection() as conn:
            conn.execute('SELECT 1').fetchone()
        
        # Contar estadísticas básicas
        with get_db_connection() as conn:
            campaigns_count = conn.execute('SELECT COUNT(*) as count FROM campaigns WHERE active = TRUE').fetchone()['count']
            devices_count = conn.execute('SELECT COUNT(*) as count FROM physical_devices WHERE active = TRUE').fetchone()['count']
            total_scans = conn.execute('SELECT COUNT(*) as count FROM tracking_data').fetchone()['count']
        
        return jsonify({
            'status': 'healthy',
            'message': 'Sistema de tracking QR con dispositivos funcionando correctamente',
            'version': '2.2.0',
            'features': ['device_tracking', 'physical_devices', 'venue_analytics', 'campaign_management'],
            'stats': {
                'active_campaigns': campaigns_count,
                'active_devices': devices_count,
                'total_scans': total_scans
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Error en el sistema',
            'error': str(e)
        }), 500

@app.route('/api/stats/summary')
def stats_summary():
    """Resumen de estadísticas generales del sistema"""
    try:
        with get_db_connection() as conn:
            # Estadísticas generales
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_scans,
                    COUNT(CASE WHEN completed_redirect = TRUE THEN 1 END) as completed_redirects,
                    COUNT(DISTINCT campaign) as total_campaigns,
                    COUNT(DISTINCT client) as total_clients,
                    COUNT(DISTINCT device_id) as devices_used,
                    AVG(duration_seconds) as avg_duration
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-30 days')
            ''').fetchone()
            
            # Top campañas
            top_campaigns = conn.execute('''
                SELECT campaign, client, COUNT(*) as scans
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-30 days')
                GROUP BY campaign, client
                ORDER BY scans DESC
                LIMIT 5
            ''').fetchall()
            
            # Actividad reciente
            recent_activity = conn.execute('''
                SELECT DATE(access_time) as date, COUNT(*) as scans
                FROM tracking_data
                WHERE DATE(access_time) >= DATE('now', '-7 days')
                GROUP BY DATE(access_time)
                ORDER BY date DESC
            ''').fetchall()
        
        return jsonify({
            'success': True,
            'stats': dict(stats) if stats else {},
            'top_campaigns': [dict(row) for row in top_campaigns],
            'recent_activity': [dict(row) for row in recent_activity],
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de estadísticas: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ============================================================================
# MANEJADORES DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"Página no encontrada: {request.url}")
    return render_template('error.html', error_message="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return render_template('error.html', error_message="Error interno del servidor"), 500

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Petición incorrecta: {request.url}")
    return render_template('error.html', error_message="Petición incorrecta"), 400

# ============================================================================
# MIDDLEWARE Y CONFIGURACIONES
# ============================================================================

@app.before_request
def log_request_info():
    """Middleware para logging de requests"""
    if request.endpoint not in ['health_check', 'collect_additional_data']:
        logger.info(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Middleware para logging de responses"""
    if request.endpoint not in ['health_check', 'collect_additional_data']:
        logger.info(f"Response: {response.status_code} - {request.method} {request.url}")
    
    # Agregar headers CORS si es necesario
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.before_first_request
def initialize_application():
    """Configuraciones que se ejecutan antes del primer request"""
    logger.info("Inicializando aplicación QR Tracking System")
    init_db()

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    
    # Configuración
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Configuraciones adicionales
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    app.config['JSON_SORT_KEYS'] = False  # Mantener orden de keys en JSON
    
    logger.info("=" * 60)
    logger.info("🚀 QR TRACKING SYSTEM CON ADMINISTRACIÓN DE CAMPAÑAS")
    logger.info("=" * 60)
    logger.info(f"🌐 Servidor iniciando en puerto {port}")
    logger.info(f"🔧 Modo debug: {debug_mode}")
    logger.info(f"📊 Panel de administración: /admin/campaigns")
    logger.info(f"📈 Dashboard: /dashboard")
    logger.info(f"🔗 Generar QR: /generate-qr")
    logger.info(f"💡 Health check: /health")
    logger.info("=" * 60)
    
    try:
        # Mostrar algunas estadísticas iniciales
        with get_db_connection() as conn:
            campaigns_count = conn.execute('SELECT COUNT(*) as count FROM campaigns WHERE active = TRUE').fetchone()['count']
            devices_count = conn.execute('SELECT COUNT(*) as count FROM physical_devices WHERE active = TRUE').fetchone()['count']
            
        logger.info(f"📋 Campañas activas: {campaigns_count}")
        logger.info(f"📱 Dispositivos físicos: {devices_count}")
        logger.info("✅ Sistema listo para recibir conexiones")
        
        # Iniciar servidor
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=debug_mode, 
            threaded=True,
            use_reloader=debug_mode
        )
        
    except Exception as e:
        logger.error(f"❌ Error iniciando aplicación: {e}")
        raise