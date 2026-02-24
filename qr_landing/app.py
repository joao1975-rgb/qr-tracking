from flask import Flask, render_template, request, redirect, url_for, jsonify
import re
import os
import json
from urllib.parse import urlparse
import logging

# Crear la instancia de Flask
app = Flask(__name__)

# Configuración básica de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu-clave-secreta-super-segura-aqui')

# Configurar logging para debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_valid_url(url):
    """
    Valida si una URL es válida y segura
    """
    try:
        # Agregar protocolo si no lo tiene
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parsear la URL
        parsed = urlparse(url)
        
        # Verificar que tenga esquema y netloc
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"URL inválida - esquema o netloc faltante: {url}")
            return False, None
        
        # Solo permitir HTTP y HTTPS
        if parsed.scheme not in ['http', 'https']:
            logger.warning(f"Esquema no permitido: {parsed.scheme}")
            return False, None
        
        # Lista básica de dominios bloqueados (opcional)
        blocked_domains = ['localhost', '127.0.0.1', '0.0.0.0', 'local']
        domain_lower = parsed.netloc.lower().split(':')[0]  # Remover puerto si existe
        
        if domain_lower in blocked_domains:
            logger.warning(f"Dominio bloqueado: {domain_lower}")
            return False, None
        
        # Verificar que el dominio tenga al menos un punto (excepto localhost)
        if '.' not in domain_lower and domain_lower != 'localhost':
            logger.warning(f"Dominio inválido: {domain_lower}")
            return False, None
        
        logger.info(f"URL válida: {url}")
        return True, url
    
    except Exception as e:
        logger.error(f"Error validando URL '{url}': {e}")
        return False, None

def detect_qr_content_type(qr_data):
    """
    Detecta el tipo de contenido del QR
    """
    qr_data = qr_data.strip()
    
    # URLs
    if qr_data.startswith(('http://', 'https://', 'www.')) or '.' in qr_data:
        return 'url'
    
    # Emails
    if '@' in qr_data and '.' in qr_data.split('@')[-1]:
        return 'email'
    
    # Teléfonos
    if qr_data.startswith(('tel:', '+')) or (qr_data.replace('-', '').replace(' ', '').isdigit() and len(qr_data.replace('-', '').replace(' ', '')) >= 7):
        return 'phone'
    
    # WiFi
    if qr_data.startswith('WIFI:'):
        return 'wifi'
    
    # SMS
    if qr_data.startswith('SMS:') or qr_data.startswith('SMSTO:'):
        return 'sms'
    
    # Coordenadas GPS
    if qr_data.startswith(('geo:', 'GEO:')):
        return 'location'
    
    # Texto plano
    return 'text'

@app.route('/')
def index():
    """
    Página principal del escáner QR
    """
    try:
        logger.info("Accediendo a página principal")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error en ruta principal: {e}")
        return f"Error cargando página: {str(e)}", 500

@app.route('/scan', methods=['POST'])
def scan_qr():
    """
    Procesar el código QR escaneado
    """
    try:
        # Obtener datos JSON del request
        data = request.get_json()
        
        if not data:
            logger.warning("No se recibieron datos JSON")
            return jsonify({
                'success': False,
                'error': 'No se recibieron datos'
            }), 400
        
        qr_data = data.get('qr_data', '').strip()
        
        if not qr_data:
            logger.warning("Datos de QR vacíos")
            return jsonify({
                'success': False,
                'error': 'Código QR vacío'
            }), 400
        
        # Truncar para logging (seguridad)
        log_data = qr_data[:100] + '...' if len(qr_data) > 100 else qr_data
        logger.info(f"Procesando código QR: {log_data}")
        
        # Detectar tipo de contenido
        content_type = detect_qr_content_type(qr_data)
        logger.info(f"Tipo de contenido detectado: {content_type}")
        
        # Procesar según el tipo
        if content_type == 'url':
            # Validar si es una URL
            is_url, validated_url = is_valid_url(qr_data)
            
            if is_url:
                logger.info(f"URL válida procesada: {validated_url}")
                return jsonify({
                    'success': True,
                    'type': 'url',
                    'redirect_url': validated_url,
                    'message': 'URL válida detectada',
                    'content': qr_data
                })
            else:
                logger.warning(f"URL inválida: {qr_data}")
                return jsonify({
                    'success': False,
                    'error': 'URL no válida o no segura'
                }), 400
        
        elif content_type == 'email':
            logger.info(f"Email detectado: {qr_data}")
            return jsonify({
                'success': True,
                'type': 'email',
                'redirect_url': f"mailto:{qr_data}",
                'content': qr_data,
                'message': 'Dirección de email detectada'
            })
        
        elif content_type == 'phone':
            # Limpiar número de teléfono
            clean_phone = qr_data
            if not clean_phone.startswith('tel:'):
                clean_phone = f"tel:{qr_data}"
            
            logger.info(f"Teléfono detectado: {qr_data}")
            return jsonify({
                'success': True,
                'type': 'phone',
                'redirect_url': clean_phone,
                'content': qr_data,
                'message': 'Número de teléfono detectado'
            })
        
        elif content_type == 'wifi':
            logger.info(f"Configuración WiFi detectada")
            return jsonify({
                'success': True,
                'type': 'wifi',
                'redirect_url': None,
                'content': qr_data,
                'message': 'Configuración WiFi detectada'
            })
        
        elif content_type == 'sms':
            logger.info(f"SMS detectado")
            return jsonify({
                'success': True,
                'type': 'sms',
                'redirect_url': qr_data if qr_data.startswith(('SMS:', 'SMSTO:')) else f"sms:{qr_data}",
                'content': qr_data,
                'message': 'SMS detectado'
            })
        
        elif content_type == 'location':
            logger.info(f"Ubicación detectada")
            return jsonify({
                'success': True,
                'type': 'location',
                'redirect_url': qr_data,
                'content': qr_data,
                'message': 'Coordenadas GPS detectadas'
            })
        
        else:
            # Texto plano u otros tipos
            logger.info(f"Contenido de texto detectado: {log_data}")
            return jsonify({
                'success': True,
                'type': 'text',
                'redirect_url': None,
                'content': qr_data,
                'message': 'Contenido de texto procesado exitosamente'
            })
    
    except json.JSONDecodeError:
        logger.error("Error decodificando JSON")
        return jsonify({
            'success': False,
            'error': 'Formato de datos inválido'
        }), 400
    
    except Exception as e:
        logger.error(f"Error procesando QR: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor'
        }), 500

@app.route('/redirect')
def redirect_page():
    """
    Página de redirección con estadísticas
    """
    try:
        url = request.args.get('url', '')
        
        if not url:
            logger.warning("URL de redirección vacía")
            return redirect(url_for('index'))
        
        # Validar URL nuevamente por seguridad
        is_url, validated_url = is_valid_url(url)
        
        if not is_url:
            logger.warning(f"URL de redirección inválida: {url}")
            return redirect(url_for('index'))
        
        logger.info(f"Página de redirección para: {validated_url}")
        return render_template('redirect.html', redirect_url=validated_url)
    
    except Exception as e:
        logger.error(f"Error en página de redirección: {e}")
        return redirect(url_for('index'))

@app.route('/track-redirect', methods=['POST'])
def track_redirect():
    """
    Endpoint para registrar estadísticas de redirección (opcional)
    """
    try:
        data = request.get_json()
        destination = data.get('destination', '')
        timestamp = data.get('timestamp', '')
        
        # Aquí puedes agregar lógica para guardar estadísticas
        # Por ejemplo, en una base de datos o archivo de log
        logger.info(f"Redirección tracked: {destination} at {timestamp}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error tracking redirect: {e}")
        return jsonify({'success': False}), 500

@app.route('/health')
def health_check():
    """
    Endpoint de verificación de salud de la aplicación
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Aplicación funcionando correctamente',
        'version': '1.0.0'
    })

@app.route('/test-qr', methods=['POST'])
def test_qr():
    """
    Endpoint para pruebas de QR (solo en desarrollo)
    """
    if not app.debug:
        return jsonify({'error': 'No disponible en producción'}), 403
    
    test_qrs = [
        'https://www.google.com',
        'https://www.instagram.com/tu_perfil',
        'correo@ejemplo.com',
        '+1234567890',
        'WIFI:T:WPA;S:MiWiFi;P:password123;;',
        'geo:40.7128,-74.0060',
        'Texto simple de prueba'
    ]
    
    return jsonify({
        'test_qrs': test_qrs,
        'message': 'QRs de prueba disponibles'
    })

@app.errorhandler(404)
def not_found_error(error):
    """
    Manejar errores 404
    """
    logger.warning(f"Página no encontrada: {request.url}")
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Manejar errores internos del servidor
    """
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor'
    }), 500

@app.errorhandler(413)
def too_large(error):
    """
    Manejar archivos demasiado grandes
    """
    logger.warning(f"Archivo demasiado grande: {request.url}")
    return jsonify({
        'success': False,
        'error': 'Archivo demasiado grande'
    }), 413

# Middleware para logging de requests
@app.before_request
def log_request_info():
    if request.endpoint != 'health_check':  # No logear health checks
        logger.info(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    if request.endpoint != 'health_check':  # No logear health checks
        logger.info(f"Response: {response.status_code} - {request.method} {request.url}")
    return response

if __name__ == '__main__':
    # Configuración para desarrollo y producción
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Configurar límite de tamaño de archivo
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    
    logger.info(f"Iniciando aplicación en puerto {port}")
    logger.info(f"Modo debug: {debug_mode}")
    logger.info(f"Límite de archivo: {app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024}MB")
    
    try:
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=debug_mode,
            threaded=True  # Permitir múltiples requests concurrentes
        )
    except Exception as e:
        logger.error(f"Error iniciando aplicación: {e}")
        print(f"Error crítico: {e}")
