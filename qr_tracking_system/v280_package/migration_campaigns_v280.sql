-- ============================================================
-- MIGRACIÓN: Enriquecimiento tabla campaigns — v2.8.0
-- Proyecto: qr-tracking-cloud (Antigravity)
-- Fecha: 2026-03
-- Descripción: Nuevos campos para comparación inteligente
--              de campañas, taxonomía IAB y benchmarking
-- Compatible: SQLite y PostgreSQL (Neon)
-- ============================================================

-- ─────────────────────────────────────────────
-- BLOQUE 1: TEMPORALIDAD DE CAMPAÑA
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS start_date        DATE;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS end_date          DATE;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS planned_duration_days INTEGER;
-- Para SQLite (no soporta IF NOT EXISTS en ALTER):
-- Ejecutar solo si la columna no existe (verificar antes con PRAGMA table_info)

-- ─────────────────────────────────────────────
-- BLOQUE 2: TAXONOMÍA DE INDUSTRIA (IAB-LATAM)
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS industry          VARCHAR(80);
-- Valores permitidos (enum lógico):
-- 'alimentacion_bebidas' | 'automotriz' | 'banca_finanzas' |
-- 'belleza_cuidado' | 'bienes_raices' | 'construccion_hogar' |
-- 'educacion' | 'electronica_tecnologia' | 'energia_servicios' |
-- 'entretenimiento_medios' | 'farmacia_salud' | 'gobierno_institucional' |
-- 'moda_retail' | 'ong_social' | 'restaurantes_gastronomia' |
-- 'seguros' | 'telecomunicaciones' | 'transporte_turismo' |
-- 'servicios_profesionales' | 'deportes_fitness' | 'otro'

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS industry_sub      VARCHAR(120);
-- Subcategoría libre para mayor granularidad (ej: 'cerveza', 'SUV premium')

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS iab_tier1         VARCHAR(60);
-- Código IAB Content Taxonomy 3.0 Tier 1 (para interoperabilidad programática)

-- ─────────────────────────────────────────────
-- BLOQUE 3: TIPO Y OBJETIVO DE CAMPAÑA
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS campaign_type     VARCHAR(60);
-- Valores permitidos:
-- 'branding'          → Imagen de marca / Top of mind
-- 'lanzamiento'       → Nuevo producto o servicio
-- 'promocion'         → Oferta táctica / Descuento
-- 'generacion_leads'  → Captación de contactos
-- 'performance'       → Conversión directa / ROI medible
-- 'retencion'         → Lealtad / CRM / Retención
-- 'reposicionamiento' → Cambio de percepción de marca
-- 'evento'            → Activación / Experiencial / Evento
-- 'causa_rse'         → Responsabilidad social
-- 'estacional'        → Navidad, verano, regreso clases, etc.
-- 'lanzamiento_tienda'→ Apertura de punto de venta

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS campaign_objective VARCHAR(40);
-- Valores (funnel AIDA):
-- 'awareness'         → Notoriedad
-- 'consideracion'     → Evaluación / Interés
-- 'intencion'         → Intención de compra
-- 'conversion'        → Compra / Lead
-- 'lealtad'           → Retención / Frecuencia
-- 'advocacy'          → Embajadores / NPS

-- ─────────────────────────────────────────────
-- BLOQUE 4: CONTEXTO DE INVERSIÓN
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS budget_tier       VARCHAR(20);
-- 'micro'      → Hasta $1,000
-- 'pequeno'    → $1,000 – $10,000
-- 'mediano'    → $10,000 – $50,000
-- 'grande'     → $50,000 – $200,000
-- 'enterprise' → Más de $200,000

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS budget_currency   VARCHAR(3) DEFAULT 'USD';
-- ISO 4217: USD | BRL | COP | MXN | ARS | VES | etc.

-- ─────────────────────────────────────────────
-- BLOQUE 5: FORMATO DOOH Y CREATIVIDAD
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS dooh_format       VARCHAR(40);
-- 'cartelera_digital'  → Digital Billboard (exterior grande)
-- 'pantalla_mall'      → Pantalla interior mall
-- 'pantalla_aeropuerto'→ Aeropuerto
-- 'pantalla_transito'  → Metro, bus, tren
-- 'pantalla_calle'     → Street level (pequeño formato)
-- 'pantalla_interior'  → Oficinas, lobbies, ascensores
-- 'pantalla_interactiva'→ Touchscreen
-- 'multipantalla'      → Múltiples formatos simultáneos

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS creative_type     VARCHAR(30);
-- 'imagen_estatica'    → JPEG/PNG estático
-- 'video'              → MP4, loop de video
-- 'animacion'          → GIF / HTML5 animation
-- 'interactivo_qr'     → Diseño con QR prominente
-- 'ar'                 → Realidad Aumentada
-- 'dinamico'           → Contenido dinámico (clima, hora, etc.)

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS product_name      VARCHAR(150);
-- Nombre específico del producto/servicio anunciado

-- ─────────────────────────────────────────────
-- BLOQUE 6: VENUE Y GEOGRAFÍA
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS venue_category    VARCHAR(40);
-- 'centro_comercial'   → Shopping Mall
-- 'aeropuerto'         → Airport
-- 'transporte'         → Transit hub (metro, bus terminal)
-- 'via_publica'        → OOH exterior / street
-- 'oficinas'           → Indoor oficinas / coworking
-- 'restaurantes_fb'    → Food & Beverage venues
-- 'gimnasios'          → Gyms / fitness centers
-- 'hoteles'            → Hotels / hospitality
-- 'estadios'           → Stadiums / arenas
-- 'universidades'      → Education campuses
-- 'mixto'              → Combinación de venues

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS geo_region        VARCHAR(80);
-- Texto libre: ciudad(es), región o país de la campaña

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS geo_country       VARCHAR(2) DEFAULT 'BR';
-- ISO 3166-1 alpha-2: BR | CO | MX | AR | VE | CL | PE | etc.

-- ─────────────────────────────────────────────
-- BLOQUE 7: AMPLIFICACIÓN DIGITAL / RRSS
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS social_amplification BOOLEAN DEFAULT FALSE;
-- TRUE si la campaña tiene soporte/amplificación en redes sociales

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS social_platforms  VARCHAR(200);
-- JSON string o lista separada por comas:
-- 'instagram,tiktok,facebook,youtube,twitter,linkedin,whatsapp'

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS influencer_support BOOLEAN DEFAULT FALSE;
-- TRUE si cuenta con creadores de contenido / influencers

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS hashtag           VARCHAR(100);
-- Hashtag principal de la campaña (para correlación con RRSS)

-- ─────────────────────────────────────────────
-- BLOQUE 8: METAS Y BENCHMARKS PROPIOS
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS target_scans      INTEGER;
-- Meta de escaneos totales definida al inicio

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS target_unique_visitors INTEGER;
-- Meta de visitantes únicos

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS target_ctr_pct    DECIMAL(5,2);
-- CTR objetivo en % (ej: 2.50 = 2.5%)

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS target_audience   VARCHAR(100);
-- Descripción de audiencia objetivo: 'mujeres 25-45 NSE A-B'

-- ─────────────────────────────────────────────
-- BLOQUE 9: ESTADO Y GESTIÓN INTERNA
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS campaign_status   VARCHAR(20) DEFAULT 'draft';
-- 'draft'     → En preparación (sin lanzar)
-- 'active'    → En curso
-- 'paused'    → Pausada temporalmente
-- 'completed' → Finalizada exitosamente
-- 'archived'  → Archivada / histórico
-- 'cancelled' → Cancelada

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS campaign_phase    VARCHAR(20);
-- 'lanzamiento' | 'sustento' | 'cierre' | 'recall'
-- Fase del ciclo de vida de la campaña

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS tags              VARCHAR(300);
-- Tags libres para filtrado: 'navidad,2025,premium,lanzamiento'

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS internal_notes    TEXT;
-- Notas internas del equipo (no visible para el cliente)

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS account_manager   VARCHAR(100);
-- Ejecutivo de cuenta responsable

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS campaign_version  INTEGER DEFAULT 1;
-- Para futuras versiones/variantes de la misma campaña

-- ─────────────────────────────────────────────
-- BLOQUE 10: REFERENCIA PARA COMPARACIÓN
-- ─────────────────────────────────────────────
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS benchmark_group   VARCHAR(60);
-- Agrupador anónimo para comparación entre campañas del mismo sector
-- Generado automáticamente: 'BG_RETAIL_MALL_BRANDING'
-- Formato: BG_{INDUSTRY}_{VENUE}_{TYPE}

ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS is_benchmark_eligible BOOLEAN DEFAULT TRUE;
-- FALSE si el cliente rechazó participar en el pool anónimo de benchmarks

-- ─────────────────────────────────────────────
-- ÍNDICES PARA PERFORMANCE EN ANALÍTICA
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_campaigns_industry     ON campaigns(industry);
CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_type ON campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_venue        ON campaigns(venue_category);
CREATE INDEX IF NOT EXISTS idx_campaigns_status       ON campaigns(campaign_status);
CREATE INDEX IF NOT EXISTS idx_campaigns_dates        ON campaigns(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_campaigns_benchmark    ON campaigns(benchmark_group);
CREATE INDEX IF NOT EXISTS idx_campaigns_geo          ON campaigns(geo_country, geo_region);

-- ─────────────────────────────────────────────
-- VISTA MATERIALIZABLE: Benchmark Pool (anónimo)
-- ─────────────────────────────────────────────
-- Esta vista se usa para el módulo de comparación sin exponer datos del cliente
CREATE OR REPLACE VIEW v_benchmark_pool AS
SELECT
    c.benchmark_group,
    c.industry,
    c.campaign_type,
    c.campaign_objective,
    c.venue_category,
    c.dooh_format,
    c.creative_type,
    c.geo_country,
    c.social_amplification,
    c.planned_duration_days,
    -- KPIs calculados desde scans (sin datos de cliente)
    COUNT(s.id)                                          AS total_scans,
    COUNT(CASE WHEN s.is_unique THEN 1 END)              AS unique_visitors,
    ROUND(AVG(s.duration_seconds), 1)                       AS avg_duration_sec,
    COUNT(CASE WHEN s.is_unique THEN 1 END) * 100.0 /
        NULLIF(COUNT(s.id), 0)                           AS unique_ratio_pct,
    -- Métricas de dispositivo (proxy NSE)
    COUNT(CASE WHEN s.operating_system LIKE '%ios%' THEN 1 END) * 100.0 /
        NULLIF(COUNT(s.id), 0)                           AS ios_pct,
    ROUND(AVG(s.device_pixel_ratio), 2)                  AS avg_dpr,
    ROUND(AVG(s.cpu_cores), 1)                           AS avg_cpu_cores,
    -- Temporal
    c.start_date,
    c.end_date,
    -- NO se incluye: campaign_code, client, description, destination
    -- Solo el ID del grupo de benchmark (anónimo)
    CONCAT('BM_', ROW_NUMBER() OVER (PARTITION BY c.benchmark_group
        ORDER BY c.created_at)) AS anon_campaign_ref
FROM campaigns c
LEFT JOIN scans s ON s.campaign_code = c.campaign_code
WHERE c.is_benchmark_eligible = TRUE
  AND c.campaign_status IN ('completed', 'active')
GROUP BY c.id, c.benchmark_group, c.industry, c.campaign_type,
         c.campaign_objective, c.venue_category, c.dooh_format,
         c.creative_type, c.geo_country, c.social_amplification,
         c.planned_duration_days, c.start_date, c.end_date
HAVING COUNT(s.id) > 50;

-- ─────────────────────────────────────────────
-- DATOS SEMILLA: benchmark_group automático
-- Se calculará via trigger o función Python al crear campaña
-- Formato: BG_{INDUSTRY_CODE}_{VENUE_CODE}_{TYPE_CODE}
-- Ejemplo: BG_RETAIL_MALL_BRAND → campañas de retail, en mall, branding
-- ─────────────────────────────────────────────
