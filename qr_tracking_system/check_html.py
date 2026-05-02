import requests

try:
    r = requests.get('http://167.172.217.151/dashboard', timeout=5)
    html = r.text
    if 'AISLAMIENTO DE GRÁFICO' in html:
        print('JS CODE IS PRESENT ON SERVER')
    else:
        print('JS CODE IS *NOT* PRESENT ON SERVER - DID NOT DEPLOY PROPERLY!')
        # Let's see what's on the server instead
        idx = html.find('loadLiveStats')
        print(html[idx:idx+500])
except Exception as e:
    print('Failed to fetch:', e)
