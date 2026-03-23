import urllib.request
import json
import ssl
import sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req = urllib.request.Request('https://project-qr-tracking.9r85r6.easypanel.host/api/scans?limit=10')
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
        if 'scans' in data:
            print("=== LATEST SCANS RAW ===")
            for s in data['scans']:
                print(f"ID: {s.get('id')}")
                print(f"Brand: {s.get('device_brand')} | Model: {s.get('device_model')}")
                print(f"UA: {s.get('user_agent')}")
                print(f"Res: {s.get('screen_resolution')} | VP: {s.get('viewport_size')} | DPR: {s.get('device_pixel_ratio')}")
                print(f"Duration: {s.get('duration_seconds')} | Time: {s.get('scan_timestamp')}")
                print("---")
except Exception as e:
    print('API FETCH ERROR:', e)
