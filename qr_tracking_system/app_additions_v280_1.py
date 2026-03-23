"""
============================================================
ADICIONES PARA app.py — v2.8.0
Proyecto: qr-tracking-cloud (Antigravity)
============================================================

INSTRUCCIONES DE INTEGRACIÓN:
1. Copiar INDUSTRY_TAXONOMY y CAMPAIGN_CONFIG al inicio de app.py
   (después de los imports, junto a otras constantes de configuración)
2. Reemplazar la clase CampaignCreate con CampaignCreate_v280
3. Reemplazar la función create_campaign con create_campaign_v280
4. Agregar los nuevos endpoints de comparación/benchmark al final
5. Ejecutar migration_campaigns_v280.sql en la BD

============================================================
"""

# ─────────────────────────────────────────────────────────────
# SECCIÓN 1: CONSTANTES DE TAXONOMÍA (agregar tras los imports)
# ─────────────────────────────────────────────────────────────

INDUSTRY_TAXONOMY = {
    "alimentacion_bebidas":      {"label": "Alimentación y Bebidas",      "iab": "IAB8",  "emoji": "🍔"},
    "automotriz":                {"label": "Automotriz",                   "iab": "IAB2",  "emoji": "🚗"},
    "banca_finanzas":            {"label": "Banca y Finanzas",             "iab": "IAB13", "emoji": "🏦"},
    "belleza_cuidado":           {"label": "Belleza y Cuidado Personal",   "iab": "IAB18", "emoji": "💄"},
    "bienes_raices":             {"label": "Bienes Raíces",                "iab": "IAB21", "emoji": "🏠"},
    "construccion_hogar":        {"label": "Construcción y Hogar",         "iab": "IAB10", "emoji": "🔨"},
    "educacion":                 {"label": "Educación",                    "iab": "IAB5",  "emoji": "📚"},
    "electronica_tecnologia":    {"label": "Electrónica y Tecnología",     "iab": "IAB19", "emoji": "📱"},
    "energia_servicios":         {"label": "Energía y Servicios Públicos", "iab": "IAB17", "emoji": "⚡"},
    "entretenimiento_medios":    {"label": "Entretenimiento y Medios",     "iab": "IAB1",  "emoji": "🎬"},
    "farmacia_salud":            {"label": "Farmacia y Salud",             "iab": "IAB7",  "emoji": "💊"},
    "gobierno_institucional":    {"label": "Gobierno e Institucional",     "iab": "IAB11", "emoji": "🏛️"},
    "moda_retail":               {"label": "Moda y Retail",                "iab": "IAB18", "emoji": "👗"},
    "ong_social":                {"label": "ONG y Causa Social",           "iab": "IAB22", "emoji": "❤️"},
    "restaurantes_gastronomia":  {"label": "Restaurantes y Gastronomía",   "iab": "IAB8",  "emoji": "🍽️"},
    "seguros":                   {"label": "Seguros",                      "iab": "IAB13", "emoji": "🛡️"},
    "telecomunicaciones":        {"label": "Telecomunicaciones",           "iab": "IAB19", "emoji": "📡"},
    "transporte_turismo":        {"label": "Transporte y Turismo",         "iab": "IAB20", "emoji": "✈️"},
    "servicios_profesionales":   {"label": "Servicios Profesionales",      "iab": "IAB3",  "emoji": "💼"},
    "deportes_fitness":          {"label": "Deportes y Fitness",           "iab": "IAB17", "emoji": "🏋️"},
    "otro":                      {"label": "Otro / No clasificado",        "iab": "IAB26", "emoji": "📋"},
}

CAMPAIGN_TYPES = {
    "branding":          {"label": "Branding / Imagen de Marca",     "objective": "awareness",    "bench_weight": 1.0},
    "lanzamiento":       {"label": "Lanzamiento de Producto",         "objective": "awareness",    "bench_weight": 1.2},
    "promocion":         {"label": "Promoción / Oferta Táctica",      "objective": "conversion",   "bench_weight": 1.5},
    "generacion_leads":  {"label": "Generación de Leads",             "objective": "intencion",    "bench_weight": 1.3},
    "performance":       {"label": "Performance / Conversión Directa","objective": "conversion",   "bench_weight": 1.4},
    "retencion":         {"label": "Retención y Lealtad",             "objective": "lealtad",      "bench_weight": 0.9},
    "reposicionamiento": {"label": "Reposicionamiento de Marca",      "objective": "consideracion","bench_weight": 0.8},
    "evento":            {"label": "Evento / Activación",             "objective": "awareness",    "bench_weight": 1.6},
    "causa_rse":         {"label": "Causa Social / RSE",              "objective": "awareness",    "bench_weight": 0.7},
    "estacional":        {"label": "Temporada / Estacional",          "objective": "conversion",   "bench_weight": 1.3},
    "lanzamiento_tienda":{"label": "Apertura de Tienda / Sucursal",   "objective": "awareness",    "bench_weight": 1.1},
}

CAMPAIGN_OBJECTIVES = {
    "awareness":      "Notoriedad / Top of Mind",
    "consideracion":  "Consideración / Evaluación",
    "intencion":      "Intención de Compra",
    "conversion":     "Conversión / Compra",
    "lealtad":        "Retención / Lealtad",
    "advocacy":       "Advocacy / Embajadores",
}

DOOH_FORMATS = {
    "cartelera_digital":    "Cartelera Digital (exterior grande)",
    "pantalla_mall":        "Pantalla de Centro Comercial",
    "pantalla_aeropuerto":  "Pantalla de Aeropuerto",
    "pantalla_transito":    "Pantalla de Transporte Público",
    "pantalla_calle":       "Pantalla de Calle (small format)",
    "pantalla_interior":    "Pantalla Interior (oficina/lobby)",
    "pantalla_interactiva": "Pantalla Interactiva / Touchscreen",
    "multipantalla":        "Múltiples Formatos Simultáneos",
}

CREATIVE_TYPES = {
    "imagen_estatica": "Imagen Estática",
    "video":           "Video",
    "animacion":       "Animación / GIF / HTML5",
    "interactivo_qr":  "Interactivo con QR Destacado",
    "ar":              "Realidad Aumentada (AR)",
    "dinamico":        "Contenido Dinámico (clima/hora/datos)",
}

VENUE_CATEGORIES = {
    "centro_comercial":  "Centro Comercial (Mall)",
    "aeropuerto":        "Aeropuerto",
    "transporte":        "Transporte Público (metro/bus/tren)",
    "via_publica":       "Vía Pública / Outdoor",
    "oficinas":          "Oficinas / Coworking / Edificios",
    "restaurantes_fb":   "Restaurantes / F&B Venues",
    "gimnasios":         "Gimnasios / Centros Fitness",
    "hoteles":           "Hoteles / Hospitalidad",
    "estadios":          "Estadios / Arenas / Eventos",
    "universidades":     "Universidades / Campuses",
    "mixto":             "Mixto (múltiples venues)",
}

BUDGET_TIERS = {
    "micro":      {"label": "Micro (hasta $1K)",         "min": 0,      "max": 1000},
    "pequeno":    {"label": "Pequeño ($1K – $10K)",      "min": 1000,   "max": 10000},
    "mediano":    {"label": "Mediano ($10K – $50K)",     "min": 10000,  "max": 50000},
    "grande":     {"label": "Grande ($50K – $200K)",     "min": 50000,  "max": 200000},
    "enterprise": {"label": "Enterprise (>$200K)",       "min": 200000, "max": None},
}

# Benchmarks de industria basados en datos públicos IAB/OAAA 2024-2025
# Fuente: Uniqode State of QR Report, OAAA/Harris Poll, Bitly QR Stats
INDUSTRY_BENCHMARKS = {
    "alimentacion_bebidas":   {"avg_ctr": 2.8, "avg_duration": 45, "scan_rate": 1.8},
    "automotriz":             {"avg_ctr": 1.9, "avg_duration": 72, "scan_rate": 1.2},
    "banca_finanzas":         {"avg_ctr": 1.5, "avg_duration": 85, "scan_rate": 0.9},
    "belleza_cuidado":        {"avg_ctr": 3.2, "avg_duration": 55, "scan_rate": 2.1},
    "bienes_raices":          {"avg_ctr": 1.8, "avg_duration": 95, "scan_rate": 1.0},
    "construccion_hogar":     {"avg_ctr": 1.4, "avg_duration": 68, "scan_rate": 0.8},
    "educacion":              {"avg_ctr": 2.1, "avg_duration": 78, "scan_rate": 1.4},
    "electronica_tecnologia": {"avg_ctr": 2.6, "avg_duration": 62, "scan_rate": 1.7},
    "energia_servicios":      {"avg_ctr": 1.2, "avg_duration": 58, "scan_rate": 0.7},
    "entretenimiento_medios": {"avg_ctr": 3.8, "avg_duration": 48, "scan_rate": 2.5},
    "farmacia_salud":         {"avg_ctr": 2.0, "avg_duration": 88, "scan_rate": 1.3},
    "gobierno_institucional": {"avg_ctr": 1.1, "avg_duration": 62, "scan_rate": 0.6},
    "moda_retail":            {"avg_ctr": 3.5, "avg_duration": 50, "scan_rate": 2.3},
    "ong_social":             {"avg_ctr": 1.8, "avg_duration": 72, "scan_rate": 1.2},
    "restaurantes_gastronomia":{"avg_ctr": 4.2, "avg_duration": 38, "scan_rate": 2.8},
    "seguros":                {"avg_ctr": 1.3, "avg_duration": 90, "scan_rate": 0.8},
    "telecomunicaciones":     {"avg_ctr": 2.4, "avg_duration": 55, "scan_rate": 1.6},
    "transporte_turismo":     {"avg_ctr": 2.9, "avg_duration": 65, "scan_rate": 1.9},
    "servicios_profesionales":{"avg_ctr": 1.6, "avg_duration": 82, "scan_rate": 1.0},
    "deportes_fitness":       {"avg_ctr": 3.1, "avg_duration": 52, "scan_rate": 2.0},
    "otro":                   {"avg_ctr": 2.0, "avg_duration": 60, "scan_rate": 1.3},
}


# ─────────────────────────────────────────────────────────────
# SECCIÓN 2: MODELO PYDANTIC ACTUALIZADO (reemplaza CampaignCreate)
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date, datetime


class CampaignCreate(BaseModel):
    # ── CAMPOS ORIGINALES (sin cambios para compatibilidad) ──
    campaign_code: str
    client: str
    destination: str
    description: Optional[str] = None

    # ── NUEVOS: TEMPORALIDAD ──
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # ── NUEVOS: TAXONOMÍA INDUSTRIA ──
    industry: Optional[str] = None                    # Clave de INDUSTRY_TAXONOMY
    industry_sub: Optional[str] = None               # Subcategoría libre
    iab_tier1: Optional[str] = None                  # Código IAB

    # ── NUEVOS: TIPO Y OBJETIVO ──
    campaign_type: Optional[str] = None              # Clave de CAMPAIGN_TYPES
    campaign_objective: Optional[str] = None         # Clave de CAMPAIGN_OBJECTIVES

    # ── NUEVOS: INVERSIÓN ──
    budget_tier: Optional[str] = None                # Clave de BUDGET_TIERS
    budget_currency: Optional[str] = "USD"

    # ── NUEVOS: FORMATO DOOH ──
    dooh_format: Optional[str] = None               # Clave de DOOH_FORMATS
    creative_type: Optional[str] = None             # Clave de CREATIVE_TYPES
    product_name: Optional[str] = None

    # ── NUEVOS: VENUE Y GEO ──
    venue_category: Optional[str] = None            # Clave de VENUE_CATEGORIES
    geo_region: Optional[str] = None
    geo_country: Optional[str] = "BR"               # ISO 3166-1 alpha-2

    # ── NUEVOS: AMPLIFICACIÓN SOCIAL ──
    social_amplification: Optional[bool] = False
    social_platforms: Optional[str] = None          # CSV: 'instagram,tiktok'
    influencer_support: Optional[bool] = False
    hashtag: Optional[str] = None

    # ── NUEVOS: METAS ──
    target_scans: Optional[int] = None
    target_unique_visitors: Optional[int] = None
    target_ctr_pct: Optional[float] = None
    target_audience: Optional[str] = None

    # ── NUEVOS: GESTIÓN INTERNA ──
    campaign_status: Optional[str] = "draft"
    campaign_phase: Optional[str] = None
    tags: Optional[str] = None
    internal_notes: Optional[str] = None
    account_manager: Optional[str] = None

    # ── NUEVOS: BENCHMARK ──
    is_benchmark_eligible: Optional[bool] = True

    @validator('campaign_code')
    def code_uppercase(cls, v):
        return v.strip().upper().replace(' ', '_')

    @validator('end_date')
    def end_after_start(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('end_date debe ser posterior a start_date')
        return v

    @validator('industry')
    def validate_industry(cls, v):
        if v and v not in INDUSTRY_TAXONOMY:
            raise ValueError(f'Industria inválida. Opciones: {list(INDUSTRY_TAXONOMY.keys())}')
        return v

    @validator('campaign_type')
    def validate_type(cls, v):
        if v and v not in CAMPAIGN_TYPES:
            raise ValueError(f'Tipo de campaña inválido. Opciones: {list(CAMPAIGN_TYPES.keys())}')
        return v


# ─────────────────────────────────────────────────────────────
# SECCIÓN 3: FUNCIÓN HELPER — Generar benchmark_group
# ─────────────────────────────────────────────────────────────

def generate_benchmark_group(campaign: CampaignCreate) -> str:
    """
    Genera el código de grupo de benchmark anónimo.
    Formato: BG_{INDUSTRY}_{VENUE}_{TYPE}
    Permite agrupar campañas similares para comparación sin revelar identidad.

    Ejemplos:
    - BG_RETAIL_MALL_BRAND  → Retail en mall, branding
    - BG_FOOD_TRANSIT_PROMO → Alimentos en transporte, promoción
    """
    industry_map = {
        "alimentacion_bebidas": "FOOD", "automotriz": "AUTO",
        "banca_finanzas": "FIN", "belleza_cuidado": "BEAUTY",
        "bienes_raices": "REALESTATE", "construccion_hogar": "HOME",
        "educacion": "EDU", "electronica_tecnologia": "TECH",
        "entretenimiento_medios": "ENT", "farmacia_salud": "HEALTH",
        "moda_retail": "RETAIL", "restaurantes_gastronomia": "FOOD",
        "telecomunicaciones": "TELCO", "transporte_turismo": "TRAVEL",
        "deportes_fitness": "SPORT", "otro": "OTHER",
    }
    venue_map = {
        "centro_comercial": "MALL", "aeropuerto": "AIRPORT",
        "transporte": "TRANSIT", "via_publica": "OOH",
        "oficinas": "OFFICE", "restaurantes_fb": "FB",
        "gimnasios": "GYM", "hoteles": "HOTEL",
        "estadios": "STADIUM", "universidades": "CAMPUS", "mixto": "MIX",
    }
    type_map = {
        "branding": "BRAND", "lanzamiento": "LAUNCH",
        "promocion": "PROMO", "generacion_leads": "LEADS",
        "performance": "PERF", "retencion": "RETAIN",
        "evento": "EVENT", "estacional": "SEASONAL",
    }

    ind = industry_map.get(campaign.industry, "GEN")
    ven = venue_map.get(campaign.venue_category, "GEN")
    typ = type_map.get(campaign.campaign_type, "GEN")

    return f"BG_{ind}_{ven}_{typ}"


# ─────────────────────────────────────────────────────────────
# SECCIÓN 4: FUNCIÓN HELPER — Calcular duración planeada
# ─────────────────────────────────────────────────────────────

def compute_planned_duration(start: Optional[date], end: Optional[date]) -> Optional[int]:
    if start and end:
        return (end - start).days
    return None


# ─────────────────────────────────────────────────────────────
# SECCIÓN 5: ENDPOINTS NUEVOS (agregar al router de app.py)
# ─────────────────────────────────────────────────────────────

# ── 5.1 COMPARACIÓN: Campaña vs Campaña Anterior del mismo cliente ──────────

@app.get("/api/analytics/compare/vs-previous/{campaign_code}")
async def compare_vs_previous(campaign_code: str, db=Depends(get_db)):
    """
    Compara la campaña actual con la campaña anterior del mismo cliente.
    Requiere que el cliente tenga al menos 2 campañas completadas.
    """
    # 1. Obtener campaña actual
    current = await db.fetch_one(
        "SELECT * FROM campaigns WHERE campaign_code = :code",
        {"code": campaign_code.upper()}
    )
    if not current:
        raise HTTPException(404, "Campaña no encontrada")

    # 2. Buscar campaña anterior del mismo cliente (por fecha end_date)
    previous = await db.fetch_one("""
        SELECT c.*, 
               COUNT(s.id) as total_scans,
               COUNT(CASE WHEN s.is_unique THEN 1 END) as unique_visitors,
               AVG(s.scan_duration) as avg_duration,
               AVG(s.device_pixel_ratio) as avg_dpr
        FROM campaigns c
        LEFT JOIN scans s ON s.campaign_code = c.campaign_code
        WHERE c.client = :client
          AND c.campaign_code != :code
          AND c.campaign_status IN ('completed', 'active')
        GROUP BY c.id
        ORDER BY c.end_date DESC NULLS LAST, c.created_at DESC
        LIMIT 1
    """, {"client": current["client"], "code": campaign_code.upper()})

    if not previous:
        return {"status": "no_previous", "message": "No hay campaña anterior para comparar"}

    # 3. Obtener KPIs de la campaña actual
    current_kpis = await db.fetch_one("""
        SELECT 
            COUNT(id) as total_scans,
            COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
            AVG(scan_duration) as avg_duration,
            AVG(device_pixel_ratio) as avg_dpr,
            COUNT(CASE WHEN os ILIKE '%ios%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as ios_pct
        FROM scans WHERE campaign_code = :code
    """, {"code": campaign_code.upper()})

    # 4. Calcular deltas
    def safe_delta(current_val, prev_val):
        if prev_val and prev_val > 0:
            return round(((current_val or 0) - prev_val) / prev_val * 100, 1)
        return None

    return {
        "current": {
            "campaign_code": current["campaign_code"],
            "campaign_type": current["campaign_type"],
            "industry": current["industry"],
            "start_date": str(current["start_date"]) if current["start_date"] else None,
            "end_date": str(current["end_date"]) if current["end_date"] else None,
            "total_scans": current_kpis["total_scans"],
            "unique_visitors": current_kpis["unique_visitors"],
            "avg_duration": round(current_kpis["avg_duration"] or 0, 1),
            "ios_pct": round(current_kpis["ios_pct"] or 0, 1),
        },
        "previous": {
            "campaign_code": previous["campaign_code"],
            "campaign_type": previous["campaign_type"],
            "start_date": str(previous["start_date"]) if previous["start_date"] else None,
            "end_date": str(previous["end_date"]) if previous["end_date"] else None,
            "total_scans": previous["total_scans"],
            "unique_visitors": previous["unique_visitors"],
            "avg_duration": round(previous["avg_duration"] or 0, 1),
        },
        "deltas": {
            "scans_delta_pct": safe_delta(current_kpis["total_scans"], previous["total_scans"]),
            "unique_delta_pct": safe_delta(current_kpis["unique_visitors"], previous["unique_visitors"]),
            "duration_delta_pct": safe_delta(current_kpis["avg_duration"], previous["avg_duration"]),
        },
        "comparison_type": "vs_previous_own"
    }


# ── 5.2 COMPARACIÓN: Campaña vs Mejor de la BD (anónimo) ────────────────────

@app.get("/api/analytics/compare/vs-benchmark/{campaign_code}")
async def compare_vs_benchmark(campaign_code: str, db=Depends(get_db)):
    """
    Compara la campaña actual vs la mejor campaña del mismo benchmark_group.
    No expone client, campaign_code ni description de la campaña de referencia.
    Solo devuelve métricas agregadas anónimas.
    """
    current = await db.fetch_one(
        "SELECT * FROM campaigns WHERE campaign_code = :code",
        {"code": campaign_code.upper()}
    )
    if not current:
        raise HTTPException(404, "Campaña no encontrada")

    bench_group = current["benchmark_group"]
    if not bench_group:
        # Recalcular si faltó al crear
        from app import generate_benchmark_group  # self-import
        bench_group = generate_benchmark_group(current)

    # KPIs actuales
    current_kpis = await db.fetch_one("""
        SELECT 
            COUNT(id) as total_scans,
            COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
            AVG(scan_duration) as avg_duration,
            COUNT(CASE WHEN os ILIKE '%ios%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as ios_pct,
            AVG(device_pixel_ratio) as avg_dpr,
            AVG(cpu_cores) as avg_cpu
        FROM scans WHERE campaign_code = :code
    """, {"code": campaign_code.upper()})

    # Mejor campaña del grupo (anónima) — EXCLUYE la campaña actual
    best_in_group = await db.fetch_one("""
        SELECT 
            COUNT(s.id) as total_scans,
            COUNT(CASE WHEN s.is_unique THEN 1 END) as unique_visitors,
            AVG(s.scan_duration) as avg_duration,
            AVG(s.device_pixel_ratio) as avg_dpr,
            c.campaign_type,
            c.dooh_format,
            c.creative_type,
            c.social_amplification,
            c.planned_duration_days
        FROM campaigns c
        JOIN scans s ON s.campaign_code = c.campaign_code
        WHERE c.benchmark_group = :group
          AND c.campaign_code != :code
          AND c.is_benchmark_eligible = TRUE
          AND c.campaign_status = 'completed'
        GROUP BY c.id
        ORDER BY COUNT(s.id) DESC
        LIMIT 1
    """, {"group": bench_group, "code": campaign_code.upper()})

    # Promedio del grupo (para percentil)
    group_avg = await db.fetch_one("""
        SELECT 
            AVG(scan_count) as avg_scans,
            AVG(unique_count) as avg_unique,
            AVG(dur_avg) as avg_duration,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY scan_count) as p75_scans,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY scan_count) as p90_scans
        FROM (
            SELECT 
                c.id,
                COUNT(s.id) as scan_count,
                COUNT(CASE WHEN s.is_unique THEN 1 END) as unique_count,
                AVG(s.scan_duration) as dur_avg
            FROM campaigns c
            JOIN scans s ON s.campaign_code = c.campaign_code
            WHERE c.benchmark_group = :group
              AND c.campaign_code != :code
              AND c.is_benchmark_eligible = TRUE
            GROUP BY c.id
        ) sub
    """, {"group": bench_group, "code": campaign_code.upper()})

    total_current = current_kpis["total_scans"] or 0

    # Calcular percentil de la campaña actual vs el grupo
    percentile = None
    if group_avg and group_avg["p75_scans"]:
        if total_current >= group_avg["p90_scans"]:
            percentile = "top_10"
        elif total_current >= group_avg["p75_scans"]:
            percentile = "top_25"
        elif total_current >= group_avg["avg_scans"]:
            percentile = "above_average"
        else:
            percentile = "below_average"

    return {
        "current": {
            "campaign_code": current["campaign_code"],
            "benchmark_group": bench_group,
            "total_scans": total_current,
            "unique_visitors": current_kpis["unique_visitors"],
            "avg_duration": round(current_kpis["avg_duration"] or 0, 1),
            "ios_pct": round(current_kpis["ios_pct"] or 0, 1),
        },
        "benchmark_best": {
            # SIN campaign_code, client, ni description — 100% anónimo
            "label": "Mejor campaña del segmento (anónimo)",
            "benchmark_group": bench_group,
            "total_scans": best_in_group["total_scans"] if best_in_group else None,
            "unique_visitors": best_in_group["unique_visitors"] if best_in_group else None,
            "avg_duration": round(best_in_group["avg_duration"] or 0, 1) if best_in_group else None,
            "dooh_format": best_in_group["dooh_format"] if best_in_group else None,
            "creative_type": best_in_group["creative_type"] if best_in_group else None,
            "social_amplification": best_in_group["social_amplification"] if best_in_group else None,
        },
        "benchmark_avg": {
            "avg_scans": round(group_avg["avg_scans"] or 0) if group_avg else None,
            "avg_unique": round(group_avg["avg_unique"] or 0) if group_avg else None,
            "avg_duration": round(group_avg["avg_duration"] or 0, 1) if group_avg else None,
            "p75_scans": round(group_avg["p75_scans"] or 0) if group_avg else None,
        },
        "position": {
            "percentile": percentile,
            "benchmark_group": bench_group,
        },
        "comparison_type": "vs_benchmark_anonymous"
    }


# ── 5.3 COMPARACIÓN: Campaña vs Otra campaña seleccionada ───────────────────

@app.get("/api/analytics/compare/vs-selected/{campaign_code}/{compare_code}")
async def compare_vs_selected(campaign_code: str, compare_code: str, db=Depends(get_db)):
    """
    Compara dos campañas específicas (puede ser del mismo cliente o diferente industria).
    Para campañas de otros clientes: oculta client y description.
    """
    current = await db.fetch_one(
        "SELECT * FROM campaigns WHERE campaign_code = :code",
        {"code": campaign_code.upper()}
    )
    compare = await db.fetch_one(
        "SELECT * FROM campaigns WHERE campaign_code = :code",
        {"code": compare_code.upper()}
    )

    if not current or not compare:
        raise HTTPException(404, "Una o ambas campañas no encontradas")

    same_client = current["client"] == compare["client"]

    async def get_kpis(code):
        return await db.fetch_one("""
            SELECT 
                COUNT(id) as total_scans,
                COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                AVG(scan_duration) as avg_duration,
                COUNT(CASE WHEN os ILIKE '%ios%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as ios_pct,
                COUNT(CASE WHEN connection_type ILIKE '%wifi%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as wifi_pct,
                AVG(device_pixel_ratio) as avg_dpr,
                AVG(cpu_cores) as avg_cpu
            FROM scans WHERE campaign_code = :code
        """, {"code": code.upper()})

    current_kpis = await get_kpis(campaign_code)
    compare_kpis = await get_kpis(compare_code)

    # Para campañas de otros clientes → anonimizar
    compare_campaign_info = {
        "campaign_code": compare["campaign_code"] if same_client else "ANON_" + compare["campaign_code"][:4],
        "industry": compare["industry"],
        "campaign_type": compare["campaign_type"],
        "dooh_format": compare["dooh_format"],
        "creative_type": compare["creative_type"],
        "venue_category": compare["venue_category"],
        "social_amplification": compare["social_amplification"],
        # Ocultar si es otro cliente
        "client": compare["client"] if same_client else "Anónimo",
        "description": compare["description"] if same_client else None,
    }

    return {
        "current": {
            "campaign_code": current["campaign_code"],
            "client": current["client"],
            "industry": current["industry"],
            "campaign_type": current["campaign_type"],
            **dict(current_kpis),
        },
        "compare": {
            **compare_campaign_info,
            "total_scans": compare_kpis["total_scans"],
            "unique_visitors": compare_kpis["unique_visitors"],
            "avg_duration": round(compare_kpis["avg_duration"] or 0, 1),
            "ios_pct": round(compare_kpis["ios_pct"] or 0, 1),
            "wifi_pct": round(compare_kpis["wifi_pct"] or 0, 1),
        },
        "same_client": same_client,
        "comparison_type": "vs_selected_campaign"
    }


# ── 5.4 INDUSTRIAS: Listado con benchmarks ──────────────────────────────────

@app.get("/api/analytics/industry-benchmarks")
async def get_industry_benchmarks():
    """Devuelve los benchmarks de industria basados en datos públicos IAB/OAAA."""
    return {
        "source": "IAB Content Taxonomy 3.0 + OAAA/Harris Poll 2024 + Uniqode State of QR 2024",
        "note": "Benchmarks globales. Los benchmarks internos de la BD prevalecen cuando hay datos suficientes.",
        "industries": {
            key: {
                **INDUSTRY_TAXONOMY[key],
                "benchmarks": INDUSTRY_BENCHMARKS.get(key, {}),
            }
            for key in INDUSTRY_TAXONOMY
        }
    }


# ── 5.5 LISTADO: Campañas disponibles para comparar (por industria) ─────────

@app.get("/api/analytics/compare/available/{campaign_code}")
async def get_comparable_campaigns(
    campaign_code: str,
    industry: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Lista campañas disponibles para seleccionar en la comparación manual.
    Incluye campañas del mismo cliente (con nombre) y otras industrias (anónimas).
    """
    current = await db.fetch_one(
        "SELECT * FROM campaigns WHERE campaign_code = :code",
        {"code": campaign_code.upper()}
    )
    if not current:
        raise HTTPException(404, "Campaña no encontrada")

    filter_industry = industry or current["industry"]

    rows = await db.fetch_all("""
        SELECT 
            c.campaign_code,
            c.client,
            c.campaign_type,
            c.industry,
            c.venue_category,
            c.dooh_format,
            c.campaign_status,
            c.start_date,
            c.end_date,
            COUNT(s.id) as total_scans,
            c.campaign_code = :own_client_marker as same_client
        FROM campaigns c
        LEFT JOIN scans s ON s.campaign_code = c.campaign_code
        WHERE c.campaign_code != :code
          AND (c.industry = :industry OR c.client = :client_name)
          AND c.campaign_status IN ('completed', 'active')
        GROUP BY c.id
        HAVING COUNT(s.id) > 0
        ORDER BY same_client DESC, COUNT(s.id) DESC
        LIMIT 20
    """, {
        "code": campaign_code.upper(),
        "own_client_marker": current["client"],
        "industry": filter_industry,
        "client_name": current["client"]
    })

    results = []
    for row in rows:
        is_same_client = row["client"] == current["client"]
        results.append({
            "campaign_code": row["campaign_code"],
            "display_name": f"{row['client']} — {row['campaign_code']}" if is_same_client
                           else f"Campaña anónima · {INDUSTRY_TAXONOMY.get(row['industry'], {}).get('label', row['industry'])}",
            "client": row["client"] if is_same_client else "Anónimo",
            "campaign_type": row["campaign_type"],
            "industry": row["industry"],
            "industry_label": INDUSTRY_TAXONOMY.get(row["industry"], {}).get("label"),
            "total_scans": row["total_scans"],
            "same_client": is_same_client,
        })

    return {
        "campaign_code": campaign_code,
        "industry_filter": filter_industry,
        "available_campaigns": results,
        "total": len(results)
    }
