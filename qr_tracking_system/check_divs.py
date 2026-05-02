from bs4 import BeautifulSoup

with open('templates/dashboard_antigravity_v28.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

overview = soup.find(id='tab-overview')
if overview:
    print(f"tab-overview contains table? : {bool(overview.find('table'))}")
    print(f"tab-overview contains scansTableBody? : {bool(overview.find(id='scansTableBody'))}")

compare = soup.find(id='tab-compare')
if compare:
    print(f"tab-compare contains table? : {bool(compare.find('table'))}")

benchmarks = soup.find(id='tab-benchmarks')
if benchmarks:
    print(f"tab-benchmarks contains table? : {bool(benchmarks.find('table'))}")

# Are there any scripts or other elements pushing the table out?
# Maybe the table is not inside tab-overview at all?
table = soup.find(id='scansTableBody')
if table:
    parents = [p.name + (f"#{p.get('id')}" if p.get('id') else "") for p in table.parents if p.name]
    print(f"scansTableBody parents: {parents}")
