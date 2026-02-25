# 🚀 Guía de Despliegue: QR Tracking System en Google Cloud Run

## Resumen de Configuración

| Componente | Servicio | Región |
|------------|----------|--------|
| **Base de datos** | Neon PostgreSQL | São Paulo (sa-east-1) |
| **Aplicación** | Google Cloud Run | São Paulo (southamerica-east1) |
| **Project ID** | qr-tracking-centauro | - |

## Credenciales (YA CONFIGURADAS)

```
DATABASE_URL=postgresql://neondb_owner:npg_AOUY8hzcWEX3@ep-silent-bird-acva379a-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

---

## Paso 1: Preparar el Código Localmente

### 1.1 Crear estructura de proyecto

```bash
# Crear carpeta del proyecto
mkdir qr-tracking-cloud
cd qr-tracking-cloud
```

### 1.2 Copiar archivos necesarios

Copia estos archivos a la carpeta `qr-tracking-cloud`:

1. `app.py` (tu archivo original)
2. `config.py` (nuevo - módulo de configuración)
3. `database.py` (nuevo - abstracción de base de datos)
4. `requirements.txt` (nuevo - dependencias actualizadas)
5. `Dockerfile` (nuevo - para Cloud Run)
6. `.env.example` → renombrar a `.env` (configuración)
7. `.gcloudignore` (archivos a ignorar)
8. Carpeta `templates/` con tus HTMLs
9. Carpeta `static/` si tienes archivos estáticos

### 1.3 Modificar app.py

Agrega estas líneas al **INICIO** de tu `app.py`, después de los imports:

```python
# ================================
# CONFIGURACIÓN PARA CLOUD
# ================================
import os

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Detectar si estamos en PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///qr_tracking.db")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Si estamos en PostgreSQL, importar psycopg2
if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras
```

### 1.4 Modificar la función get_db_connection()

Reemplaza la función `get_db_connection()` en tu app.py con esta versión:

```python
def get_db_connection():
    """Obtener conexión a la base de datos (SQLite o PostgreSQL)"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///qr_tracking.db")
    
    if DATABASE_URL.startswith("postgresql"):
        # PostgreSQL (Neon)
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # SQLite (desarrollo local)
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
```

### 1.5 Crear función para adaptar queries

Agrega esta función después de `get_db_connection()`:

```python
def adapt_query(query: str) -> str:
    """Adapta queries de SQLite a PostgreSQL"""
    import re
    
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL.startswith("postgresql"):
        return query
    
    # Reemplazar ? por %s
    adapted = query.replace("?", "%s")
    
    # datetime('now', '-X days') → NOW() - INTERVAL 'X days'
    adapted = re.sub(
        r"datetime\s*\(\s*'now'\s*,\s*'(-?\d+)\s*(hours?|days?|minutes?)'\s*\)",
        r"NOW() - INTERVAL '\1 \2'",
        adapted,
        flags=re.IGNORECASE
    )
    
    # datetime('now') → NOW()
    adapted = re.sub(r"datetime\s*\(\s*'now'\s*\)", "NOW()", adapted, flags=re.IGNORECASE)
    
    return adapted
```

### 1.6 Modificar TODAS las queries

En cada lugar donde uses `cursor.execute()`, envuelve la query con `adapt_query()`:

**Antes:**
```python
cursor.execute("SELECT * FROM campaigns WHERE campaign_code = ?", (code,))
```

**Después:**
```python
cursor.execute(adapt_query("SELECT * FROM campaigns WHERE campaign_code = ?"), (code,))
```

---

## Paso 2: Configurar Google Cloud CLI

### 2.1 Instalar gcloud CLI

**Windows:**
```powershell
# Descargar de: https://cloud.google.com/sdk/docs/install
# Ejecutar el instalador GoogleCloudSDKInstaller.exe
```

**Mac:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 2.2 Iniciar sesión y configurar proyecto

```bash
# Iniciar sesión
gcloud auth login

# Configurar proyecto
gcloud config set project qr-tracking-centauro

# Configurar región
gcloud config set run/region southamerica-east1

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

---

## Paso 3: Desplegar en Cloud Run

### 3.1 Desde el directorio del proyecto

```bash
cd qr-tracking-cloud
```

### 3.2 Desplegar con un solo comando

```bash
gcloud run deploy qr-tracking \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://neondb_owner:npg_AOUY8hzcWEX3@ep-silent-bird-acva379a-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require" \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "LOG_LEVEL=INFO" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300
```

### 3.3 Esperar el despliegue

El proceso tarda aproximadamente 3-5 minutos. Verás algo como:

```
Building using Dockerfile and target platform linux/amd64
...
Deploying container to Cloud Run service [qr-tracking] in project [qr-tracking-centauro] region [southamerica-east1]
✓ Deploying... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [qr-tracking] revision [qr-tracking-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://qr-tracking-XXXXX-rj.a.run.app
```

### 3.4 ¡Listo! Tu URL será algo como:

```
https://qr-tracking-XXXXX-rj.a.run.app
```

---

## Paso 4: Verificar el Despliegue

### 4.1 Probar la API

```bash
# Health check
curl https://TU-URL.run.app/api/health

# Ver campañas
curl https://TU-URL.run.app/api/campaigns
```

### 4.2 Acceder al Dashboard

Abre en tu navegador:
```
https://TU-URL.run.app/dashboard
```

---

## Paso 5: Configurar URLs de Tracking

### 5.1 Actualizar BASE_URL

Una vez que tengas tu URL de Cloud Run, actualiza la variable de entorno:

```bash
gcloud run services update qr-tracking \
  --region southamerica-east1 \
  --set-env-vars "BASE_URL=https://TU-URL.run.app"
```

### 5.2 Generar códigos QR

Los códigos QR ahora usarán la URL de Cloud Run:
```
https://TU-URL.run.app/track?campaign=tu_campana
```

---

## Comandos Útiles

### Ver logs en tiempo real
```bash
gcloud run logs read qr-tracking --region southamerica-east1 --tail 50
```

### Ver logs con seguimiento
```bash
gcloud run logs tail qr-tracking --region southamerica-east1
```

### Actualizar el servicio
```bash
gcloud run deploy qr-tracking --source . --region southamerica-east1
```

### Ver detalles del servicio
```bash
gcloud run services describe qr-tracking --region southamerica-east1
```

### Eliminar el servicio (si necesitas)
```bash
gcloud run services delete qr-tracking --region southamerica-east1
```

---

## Solución de Problemas

### Error: "Permission denied"
```bash
gcloud auth login
gcloud config set project qr-tracking-centauro
```

### Error: "Database connection failed"
- Verifica que la URL de Neon sea correcta
- Asegúrate de incluir `?sslmode=require` al final

### Error de build con Pillow
El Dockerfile ya incluye las dependencias necesarias. Si falla:
```bash
# Verificar que el Dockerfile tenga:
RUN apt-get install -y libjpeg62-turbo-dev zlib1g-dev libpng-dev
```

### La aplicación no inicia
```bash
# Ver logs detallados
gcloud run logs read qr-tracking --region southamerica-east1 --limit 100
```

---

## Costos Estimados

| Uso | Costo Mensual |
|-----|---------------|
| ~1,000 scans/mes | **$0** (free tier) |
| ~10,000 scans/mes | ~$1-3 |
| ~50,000 scans/mes | ~$5-15 |

El free tier de Cloud Run incluye:
- 2 millones de requests/mes
- 180,000 vCPU-segundos/mes
- 360,000 GB-segundos de memoria/mes

---

## Dominio Personalizado (Opcional)

Para usar tu propio dominio (ej: `qr.centauroads.com`):

```bash
# 1. Verificar el dominio
gcloud domains verify centauroads.com

# 2. Mapear al servicio
gcloud run domain-mappings create \
  --service qr-tracking \
  --domain qr.centauroads.com \
  --region southamerica-east1
```

Luego configura los registros DNS según las instrucciones que te dé Google.

---

## ✅ Checklist Final

- [ ] gcloud CLI instalado
- [ ] Proyecto configurado (`qr-tracking-centauro`)
- [ ] APIs habilitadas
- [ ] Archivos copiados al directorio
- [ ] app.py modificado con adapt_query()
- [ ] Dockerfile presente
- [ ] requirements.txt actualizado
- [ ] Despliegue ejecutado
- [ ] URL de Cloud Run funcionando
- [ ] Health check respondiendo
- [ ] Dashboard accesible

---

**¡Listo!** Tu QR Tracking System ahora está corriendo en Google Cloud Run con base de datos PostgreSQL en Neon, ambos en la región de São Paulo para mínima latencia en Latinoamérica.
