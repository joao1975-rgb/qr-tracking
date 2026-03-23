import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url_html = "https://project-qr-tracking.9r85r6.easypanel.host/dashboard"
url_api = "https://project-qr-tracking.9r85r6.easypanel.host/api/analytics/dashboard"
url_scans = "https://project-qr-tracking.9r85r6.easypanel.host/api/scans?limit=5"

try:
    print("----- VERIFICANDO HTML DASHBOARD -----")
    req_html = urllib.request.Request(url_html)
    with urllib.request.urlopen(req_html, context=ctx) as response:
        html = response.read().decode('utf-8')
        if 'id="avgDuration"' in html and 'id="iosPct"' in html:
            print("[OK] El HTML de dashboard.html ESTA ACTUALIZADO con KPI de v2.8!")
        else:
            print("[ERROR] El HTML NO esta actualizado. Faltan tarjetas de KPI en dashboard.")
            
    print("\n----- VERIFICANDO API ANALYTICS (HISTÓRICOS) -----")
    req_api = urllib.request.Request(url_api)
    with urllib.request.urlopen(req_api, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        if data.get("success"):
            stats = data.get("stats", {})
            print(f"[OK] API Analytics respondio 200 con éxito.")
            print(f" -> Total Escaneos: {stats.get('total_scans')}")
            print(f" -> Unique Visitors: {stats.get('unique_visitors')}")
            print(f" -> Duración Promedio (s): {stats.get('avg_duration')}")
            print(f" -> Porcentaje iOS (%): {stats.get('ios_pct')}")
        else:
            print("[ERROR] La API reporto success=False.")
            print(data)

    print("\n----- VERIFICANDO ENDPOINT ESCANEOS (HISTÓRICOS) -----")
    req_scans = urllib.request.Request(url_scans)
    with urllib.request.urlopen(req_scans, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        if data.get("success"):
            scans = data.get("scans", [])
            print(f"[OK] API Scans respondio 200 con éxito. Devolvió {len(scans)} registros.")
        else:
            print("[ERROR] La API reporto success=False.")
            print(data)

except urllib.error.HTTPError as e:
    print(f"[HTTP ERROR] Código: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"[UNKNOWN ERROR] {e}")
