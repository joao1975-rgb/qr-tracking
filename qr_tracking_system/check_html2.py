import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen("https://167.172.217.151/dashboard", context=ctx) as response:
        html = response.read().decode('utf-8')
    if 'AISLAMIENTO' in html:
        print('JS CODE IS PRESENT ON SERVER')
    else:
        print('JS CODE IS *NOT* PRESENT ON SERVER - DID NOT DEPLOY PROPERLY!')
        
except Exception as e:
    print('Failed to fetch:', e)
