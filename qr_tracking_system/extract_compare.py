lines = open('app.py', 'r', encoding='utf-8').readlines()
idx = 0
for i, l in enumerate(lines):
    if '@app.get("/api/analytics/compare/vs-previous/{campaign_code}")' in l:
        idx = i
        break
open('compare_endpoints.txt', 'w', encoding='utf-8').writelines(lines[idx:idx+800])
