import urllib.request
import json

print("Consultando el servidor Live por HTTP puro...")
try:
    req = urllib.request.Request("https://project-qr-tracking.9r85r6.easypanel.host/api/analytics/industry-benchmarks")
    with urllib.request.urlopen(req) as response:
        print("Code:", response.getcode())
        data = json.loads(response.read().decode())
        print("Datos:", str(data)[:100] + "...")
        
    req_html = urllib.request.Request("https://project-qr-tracking.9r85r6.easypanel.host/admin")
    with urllib.request.urlopen(req_html) as response:
        html = response.read().decode('utf-8')
        if 'Industria' in html or 'industry_sub' in html:
            print("\nUI CHECK: El HTML publico SÍ es la version v2.8 (Industria/Type)!")
        else:
            print("\nUI CHECK: El HTML publico ES el viejo formato (v2.7)!")
            
except Exception as e:
    print(e)
