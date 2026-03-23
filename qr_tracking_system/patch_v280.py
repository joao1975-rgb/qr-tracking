import sys
import shutil

# First, restore from pristine backup
shutil.copy("app_original.py", "app.py")

with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

with open("app_additions_v280_1.py", "r", encoding="utf-8") as f:
    additions = f.read()

# EXTRACCIONES DE additions
section1_start = additions.find('# SECCIÓN 1: CONSTANTES Y TAXONOMÍAS')
section1_end = additions.find('# SECCIÓN 2: MODELO PYDANTIC ACTUALIZADO')
taxonomies = additions[section1_start:section1_end].strip()

section2_start = additions.find('class CampaignCreate(BaseModel):')
section2_end = additions.find('# SECCIÓN 3: FUNCIONES DE AYUDA (Helpers)')
campaign_create_code = additions[section2_start:section2_end].strip()

# Create a companion CampaignUpdate_v280
campaign_update_code = campaign_create_code.replace('CampaignCreate', 'CampaignUpdate')
campaign_update_code = campaign_update_code.replace('campaign_code: str', '')
campaign_update_code = campaign_update_code.replace(': str', ': Optional[str] = None')
campaign_update_code = campaign_update_code.replace(': int', ': Optional[int] = None')
campaign_update_code = campaign_update_code.replace(': float', ': Optional[float] = None')
campaign_update_code = campaign_update_code.replace(': bool', ': Optional[bool] = None')
campaign_update_code = campaign_update_code.replace('Optional[Optional[', 'Optional[')

section3_start = additions.find('def generate_benchmark_group')
section3_end = additions.find('# SECCIÓN 5: ENDPOINTS NUEVOS')
helpers_code = additions[section3_start:section3_end].strip()

# 1. Inject constants
config_marker = app_code.find('DATABASE_PATH')
if config_marker != -1:
    end_of_line = app_code.find('\n', config_marker)
    app_code = app_code[:end_of_line+1] + '\n' + taxonomies + '\n\n' + app_code[end_of_line+1:]
else:
    # default fallback
    config_marker = app_code.find('import os')
    if config_marker != -1:
        app_code = app_code[:config_marker] + taxonomies + '\n\n' + app_code[config_marker:]

# 2. Reemplazar CampaignCreate y CampaignUpdate
old_create_start = app_code.find('class CampaignCreate(BaseModel):')
old_create_end = app_code.find('class DeviceCreate(BaseModel):')
if old_create_start != -1 and old_create_end != -1:
    app_code = app_code[:old_create_start] + campaign_create_code + '\n\n' + campaign_update_code + '\n\n' + app_code[old_create_end:]

# 3. Inject helpers
helpers_marker = app_code.find('class ScanCreate(BaseModel):')
if helpers_marker != -1:
    app_code = app_code[:helpers_marker] + helpers_code + '\n\n' + app_code[helpers_marker:]

# 4. Endpoints síncronos
app_code = app_code.replace('from pydantic import BaseModel', 'from pydantic import BaseModel, root_validator, validator')

create_update_sync = """
@app.post("/api/campaigns")
async def create_campaign(campaign: CampaignCreate):
    try:
        campaign.campaign_code = campaign.campaign_code.upper().replace(' ', '_')
        bg = generate_benchmark_group(campaign)
        dur = compute_planned_duration(campaign.start_date, campaign.end_date)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = \"\"\"
                INSERT INTO campaigns (
                    campaign_code, client, destination, description, active,
                    product_name, start_date, end_date, campaign_status, campaign_phase,
                    account_manager, hashtag, tags, industry, industry_sub,
                    geo_country, geo_region, is_benchmark_eligible, campaign_type,
                    campaign_objective, dooh_format, creative_type, venue_category,
                    budget_tier, budget_currency, target_audience, social_amplification,
                    social_platforms, influencer_support, internal_notes, target_scans,
                    target_unique_visitors, target_ctr_pct, benchmark_group, planned_duration_days
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING *
            \"\"\"
            values = (
                campaign.campaign_code, campaign.client, campaign.destination, campaign.description, campaign.active,
                campaign.product_name, campaign.start_date, campaign.end_date, campaign.campaign_status, campaign.campaign_phase,
                campaign.account_manager, campaign.hashtag, campaign.tags, campaign.industry, campaign.industry_sub,
                campaign.geo_country, campaign.geo_region, campaign.is_benchmark_eligible, campaign.campaign_type,
                campaign.campaign_objective, campaign.dooh_format, campaign.creative_type, campaign.venue_category,
                campaign.budget_tier, campaign.budget_currency, campaign.target_audience, campaign.social_amplification,
                campaign.social_platforms, campaign.influencer_support, campaign.internal_notes, campaign.target_scans,
                campaign.target_unique_visitors, campaign.target_ctr_pct, bg, dur
            )
            cursor.execute(query, values)
            new_campaign = cursor.fetchone()
            if new_campaign:
                new_campaign = dict(new_campaign)
            conn.commit()
            
        return {"success": True, "message": "Campaña creada exitosamente", "campaign": new_campaign}
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "duplicate" in str(e).lower() or "IntegrityError" in str(type(e)):
            return {"success": False, "error": "El código de campaña ya existe"}
        return {"success": False, "error": str(e)}

@app.put("/api/campaigns/{campaign_code}")
async def update_campaign(campaign_code: str, campaign_update: CampaignUpdate):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM campaigns WHERE campaign_code = %s", (campaign_code,))
            if not cursor.fetchone():
                return {"success": False, "error": "Campaña no encontrada"}
            
            update_fields = []
            values = []
            upd_dict = campaign_update.dict(exclude_unset=True)
            for k, v in upd_dict.items():
                update_fields.append(f"{k} = %s")
                values.append(v)
            
            if not update_fields:
                return {"success": False, "error": "No hay campos para actualizar"}
                
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(campaign_code)
            
            query = f"UPDATE campaigns SET {', '.join(update_fields)} WHERE campaign_code = %s"
            cursor.execute(query, values)
            conn.commit()
            
        return {"success": True, "message": "Campaña actualizada exitosamente"}
    except Exception as e:
        return {"success": False, "error": str(e)}
"""

analytics_part = """
# ─────────────────────────────────────────────────────────────
# SECCIÓN 5: ENDPOINTS NUEVOS (SÍNCRONOS)
# ─────────────────────────────────────────────────────────────

@app.get("/api/analytics/compare/vs-previous/{campaign_code}")
async def compare_vs_previous(campaign_code: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE campaign_code = %s", (campaign_code.upper(),))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(404, "Campaña no encontrada")

        cursor.execute(\"\"\"
            SELECT c.*, 
                   COUNT(s.id) as total_scans,
                   COUNT(CASE WHEN s.is_unique THEN 1 END) as unique_visitors,
                   AVG(s.scan_duration) as avg_duration,
                   AVG(s.device_pixel_ratio) as avg_dpr
            FROM campaigns c
            LEFT JOIN scans s ON s.campaign_code = c.campaign_code
            WHERE c.client = %s
              AND c.campaign_code != %s
              AND c.campaign_status IN ('completed', 'active')
            GROUP BY c.id
            ORDER BY c.end_date DESC NULLS LAST, c.created_at DESC
            LIMIT 1
        \"\"\", (current["client"], campaign_code.upper()))
        previous = cursor.fetchone()

        if not previous:
            return {"status": "no_previous", "message": "No hay campaña anterior para comparar"}

        cursor.execute(\"\"\"
            SELECT 
                COUNT(id) as total_scans,
                COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                AVG(scan_duration) as avg_duration,
                AVG(device_pixel_ratio) as avg_dpr,
                COUNT(CASE WHEN os ILIKE '%ios%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as ios_pct
            FROM scans WHERE campaign_code = %s
        \"\"\", (campaign_code.upper(),))
        current_kpis = cursor.fetchone()

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
                "ios_pct": round(current_kpis["ios_pct"] or 0, 1) if current_kpis["ios_pct"] else 0,
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

@app.get("/api/analytics/compare/vs-benchmark/{campaign_code}")
async def compare_vs_benchmark(campaign_code: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE campaign_code = %s", (campaign_code.upper(),))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(404, "Campaña no encontrada")

        bench_group = current["benchmark_group"]
        if not bench_group:
            bench_group = generate_benchmark_group(current)

        cursor.execute(\"\"\"
            SELECT 
                COUNT(id) as total_scans,
                COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                AVG(scan_duration) as avg_duration,
                COUNT(CASE WHEN os ILIKE '%ios%' THEN 1 END) * 100.0 / NULLIF(COUNT(id), 0) as ios_pct,
                AVG(device_pixel_ratio) as avg_dpr,
                AVG(cpu_cores) as avg_cpu
            FROM scans WHERE campaign_code = %s
        \"\"\", (campaign_code.upper(),))
        current_kpis = cursor.fetchone()

        cursor.execute(\"\"\"
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
            WHERE c.benchmark_group = %s
              AND c.campaign_code != %s
              AND c.is_benchmark_eligible = TRUE
              AND c.campaign_status = 'completed'
            GROUP BY c.id
            ORDER BY COUNT(s.id) DESC
            LIMIT 1
        \"\"\", (bench_group, campaign_code.upper()))
        best_in_group = cursor.fetchone()

        cursor.execute(\"\"\"
            SELECT 
                AVG(scan_count) as avg_scans,
                AVG(unique_count) as avg_unique,
                AVG(dur_avg) as avg_duration
            FROM (
                SELECT 
                    c.id,
                    COUNT(s.id) as scan_count,
                    COUNT(CASE WHEN s.is_unique THEN 1 END) as unique_count,
                    AVG(s.scan_duration) as dur_avg
                FROM campaigns c
                JOIN scans s ON s.campaign_code = c.campaign_code
                WHERE c.benchmark_group = %s
                  AND c.campaign_code != %s
                  AND c.is_benchmark_eligible = TRUE
                GROUP BY c.id
            ) sub
        \"\"\", (bench_group, campaign_code.upper()))
        group_avg = cursor.fetchone()

        if not best_in_group:
            return {"status": "no_benchmark", "message": "No hay datos de benchmark suficientes"}

        def safe_delta(current_val, prev_val):
            if prev_val and prev_val > 0:
                return round(((current_val or 0) - prev_val) / prev_val * 100, 1)
            return None

        total_current = current_kpis["total_scans"] or 0
        avg_scans = group_avg["avg_scans"] or 0
        percentile = "Above Average" if total_current > avg_scans else "Below Average"

        return {
            "current": {
                "campaign_code": current["campaign_code"],
                "total_scans": current_kpis["total_scans"],
                "unique_visitors": current_kpis["unique_visitors"],
                "avg_duration": round(current_kpis["avg_duration"] or 0, 1)
            },
            "benchmark_best": {
                "campaign_type": best_in_group["campaign_type"],
                "dooh_format": best_in_group["dooh_format"],
                "creative_type": best_in_group["creative_type"],
                "total_scans": best_in_group["total_scans"],
                "unique_visitors": best_in_group["unique_visitors"],
                "avg_duration": round(best_in_group["avg_duration"] or 0, 1)
            },
            "benchmark_group_stats": {
                "group_id": bench_group,
                "avg_scans": round(avg_scans, 1),
                "avg_unique": round(group_avg["avg_unique"] or 0, 1),
                "percentile_estimated": percentile
            },
            "deltas_vs_best": {
                "scans_delta_pct": safe_delta(current_kpis["total_scans"], best_in_group["total_scans"]),
                "duration_delta_pct": safe_delta(current_kpis["avg_duration"], best_in_group["avg_duration"]),
            },
            "comparison_type": "vs_benchmark_anonymous"
        }

@app.get("/api/analytics/compare/vs-selected/{campaign_code}/{compare_code}")
async def compare_vs_selected(campaign_code: str, compare_code: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM campaigns WHERE campaign_code = %s", (campaign_code.upper(),))
        current = cursor.fetchone()
        
        cursor.execute("SELECT * FROM campaigns WHERE campaign_code = %s", (compare_code.upper(),))
        compare = cursor.fetchone()
        
        if not current or not compare:
            raise HTTPException(404, "Campaña no encontrada")

        is_same_client = current["client"] == compare["client"]
        
        def fetch_kpis(code):
            cursor.execute(\"\"\"
                SELECT 
                    COUNT(id) as total_scans,
                    COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                    AVG(scan_duration) as avg_duration
                FROM scans WHERE campaign_code = %s
            \"\"\", (code.upper(),))
            return cursor.fetchone()
            
        current_kpis = fetch_kpis(campaign_code)
        compare_kpis = fetch_kpis(compare_code)

        def safe_delta(current_val, prev_val):
            if prev_val and prev_val > 0:
                return round(((current_val or 0) - prev_val) / prev_val * 100, 1)
            return None

        comp_data = {
            "campaign_code": compare["campaign_code"] if is_same_client else "ANONYMOUS_REF",
            "client": compare["client"] if is_same_client else "Confidencial",
            "industry": compare["industry"],
            "campaign_type": compare["campaign_type"],
            "total_scans": compare_kpis["total_scans"],
            "unique_visitors": compare_kpis["unique_visitors"],
            "avg_duration": round(compare_kpis["avg_duration"] or 0, 1)
        }

        return {
            "current": {
                "campaign_code": current["campaign_code"],
                "industry": current["industry"],
                "campaign_type": current["campaign_type"],
                "total_scans": current_kpis["total_scans"],
                "unique_visitors": current_kpis["unique_visitors"],
                "avg_duration": round(current_kpis["avg_duration"] or 0, 1)
            },
            "compare_to": comp_data,
            "deltas": {
                "scans_delta_pct": safe_delta(current_kpis["total_scans"], compare_kpis["total_scans"]),
                "unique_delta_pct": safe_delta(current_kpis["unique_visitors"], compare_kpis["unique_visitors"]),
            },
            "comparison_type": "vs_selected",
            "is_anonymous": not is_same_client
        }

@app.get("/api/analytics/industry-benchmarks")
async def get_industry_benchmarks():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(\"\"\"
            SELECT 
                c.industry,
                COUNT(DISTINCT c.id) as total_campaigns,
                AVG(kpi.total_scans) as avg_scans,
                AVG(kpi.unique_visitors) as avg_unique,
                AVG(kpi.avg_duration) as avg_duration
            FROM campaigns c
            LEFT JOIN (
                SELECT campaign_code, 
                       COUNT(id) as total_scans,
                       COUNT(CASE WHEN is_unique THEN 1 END) as unique_visitors,
                       AVG(scan_duration) as avg_duration
                FROM scans GROUP BY campaign_code
            ) kpi ON c.campaign_code = kpi.campaign_code
            WHERE c.is_benchmark_eligible = TRUE
              AND c.industry IS NOT NULL
            GROUP BY c.industry
            HAVING COUNT(DISTINCT c.id) >= 2
            ORDER BY avg_scans DESC
        \"\"\")
        benchmarks = cursor.fetchall()
        
        return {
            "success": True,
            "data": [dict(b) for b in benchmarks] if benchmarks else []
        }

@app.get("/api/analytics/compare/available/{campaign_code}")
async def get_available_for_comparison(campaign_code: str, industry_filter: bool = False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT client, industry FROM campaigns WHERE campaign_code = %s", (campaign_code.upper(),))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(404, "Campaña no encontrada")
            
        where_clause = "campaign_code != %s AND campaign_status IN ('completed', 'active')"
        params = [campaign_code.upper()]
        
        if industry_filter and current["industry"]:
            where_clause += " AND industry = %s"
            params.append(current["industry"])
            
        cursor.execute(f"SELECT * FROM campaigns WHERE {where_clause} ORDER BY created_at DESC", tuple(params))
        campaigns = cursor.fetchall()
        
        result = []
        for c in campaigns:
            is_same_client = (c["client"] == current["client"])
            if is_same_client or c["is_benchmark_eligible"]:
                result.append({
                    "campaign_code": c["campaign_code"] if is_same_client else "ANONYMOUS_" + str(c["id"]),
                    "client": c["client"] if is_same_client else "Confidencial",
                    "product_name": c["product_name"] if is_same_client else "Producto de " + (c["industry"] or "Industria"),
                    "industry": c["industry"],
                    "campaign_type": c["campaign_type"],
                    "is_own_client": is_same_client
                })
                
        return {"success": True, "available": result}
"""

start_crt = app_code.find('@app.post("/api/campaigns")')
end_crt = app_code.find('@app.put("/api/campaigns/{campaign_code}/pause")')
if start_crt != -1 and end_crt != -1:
    app_code = app_code[:start_crt] + create_update_sync + '\\n\\n' + app_code[end_crt:]
else:
    print("WARNING: create_campaign block not found")

app_code += '\\n\\n' + analytics_part

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Patch applied successfully.")
