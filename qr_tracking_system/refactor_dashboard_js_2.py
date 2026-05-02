import os
import re

file_path = "templates/dashboard_antigravity_v28.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Init patch
html = re.sub(
    r"document\.addEventListener\('DOMContentLoaded', \(\) => \{\s*// Build charts immediately\s*createMainChart\(\);\s*createDonut\(\);\s*buildHeatmap\(\);\s*// Initialize Live Data Stream\s*loadLiveScans\(\);\s*setInterval\(loadLiveScans, 15000\);\s*// Draw sparklines\s*const sparkData = \{",
    r"let chartsConfigured = false;\ndocument.addEventListener('DOMContentLoaded', () => {\n  loadLiveScans();\n  setInterval(loadLiveScans, 15000);\n  loadLiveStats();\n\n  const sparkData = {",
    html
)

# 2. loadLiveStats patch
html = re.sub(
    r"async function loadLiveStats\(\) \{\s*try \{\s*const res = await fetch\('/api/analytics/dashboard'\);\s*const data = await res\.json\(\);\s*if \(data\.success \|\| data\.stats\) \{\s*const stats = data\.stats \|\| data;",
    r"""async function loadLiveStats() {
  try {
    const res = await fetch('/api/analytics/dashboard');
    const data = await res.json();
    if (data.success || data.stats) {
      const stats = data.stats || data;
      
      if (!chartsConfigured && data.daily_scans) {
         let labels = [], totalScans = [], uniqueScans = [], multis = [];
         data.daily_scans.forEach(d => {
             labels.push(d.date.substring(5)); // MM-DD
             totalScans.push(d.scans);
             uniqueScans.push(d.unique_scans);
             let singles = d.single_scans || 0;
             let m = d.unique_scans - singles;
             let mtot = d.scans - singles;
             multis.push(m>0? mtot/m : 0);
         });
         chartData['30d'] = { labels: labels, scans: totalScans, unique: uniqueScans, multiAvg: multis, bench: new Array(labels.length).fill(10) };
         chartData['7d'] = chartData['30d'];
         
         if(data.operating_systems && data.operating_systems.length > 0){
             window.sysData = data.operating_systems;
         }
         if(data.heatmap_data) {
             window.hmData = data.heatmap_data;
         }

         createMainChart();
         createDonut();
         buildHeatmap();
         chartsConfigured = true;
      }""",
      html
)

# 3. Heatmap patch
old_heatmap_block = r"""// Cells\s*for \(let hr = 0; hr < 24; hr\+\+\) \{\s*for \(let day = 0; day < 7; day\+\+\) \{\s*const el = document\.createElement\('div'\);\s*el\.className = 'heatmap-cell';\s*// procedural dummy\s*let val = Math\.random\(\) \* 80;\s*if \(hr > 8 && hr < 20\) val \+= 30;\s*if \(day > 4\) val \+= 20;"""

new_heatmap_block = r"""// Cells
  let maxHm = 1;
  const hmMap = {};
  if(window.hmData) {
      window.hmData.forEach(hd => {
         hmMap[`${hd.dow}-${hd.hour}`] = hd.count;
         if(hd.count > maxHm) maxHm = hd.count;
      });
  }

  for (let hr = 0; hr < 24; hr++) {
    for (let day = 0; day < 7; day++) {
      const el = document.createElement('div');
      el.className = 'heatmap-cell';
      
      let val = 0;
      if(window.hmData) {
          let sqlDow = day === 6 ? 0 : day + 1;
          val = hmMap[`${sqlDow}-${hr}`] || 0;
          val = (val / maxHm) * 100;
      } else {
          val = Math.random() * 80;
          if (hr > 8 && hr < 20) val += 30; 
          if (day > 4) val += 20; 
      }"""

html = re.sub(old_heatmap_block, new_heatmap_block, html)

# Goals patches
html = re.sub(r'<div class="pg-val">12\.309</div>\s*<div class="pg-tar">Meta: 15\.000</div>', r'<div class="pg-val" id="pg-tot-ui">0</div>\n              <div class="pg-tar" id="pg-tot-target">Meta: -</div>', html)
html = re.sub(r'<div class="pg-val">8\.980</div>\s*<div class="pg-tar">Alcance: 10\.000</div>', r'<div class="pg-val" id="pg-uq-ui">0</div>\n              <div class="pg-tar" id="pg-uq-target">Alcance: -</div>', html)
html = re.sub(r'<div class="pg-val">2\.8%</div>\s*<div class="pg-tar">Objetivo: 2\.5%</div>', r'<div class="pg-val" id="pg-ctr-ui">0%</div>\n              <div class="pg-tar" id="pg-ctr-target">Objetivo: -</div>', html)

# Goals injection JS
html = re.sub(r"document\.getElementById\('pg-tot'\)\.textContent = total;", r"document.getElementById('pg-tot-ui').textContent = total;", html)
html = re.sub(r"document\.querySelector\('#pg-tot'\)", r"document.querySelector('#pg-tot-ui')", html)
html = re.sub(r"document\.getElementById\('pg-uq'\)\.textContent = unique;", r"document.getElementById('pg-uq-ui').textContent = unique;", html)
html = re.sub(r"document\.querySelector\('#pg-uq'\)", r"document.querySelector('#pg-uq-ui')", html)
html = re.sub(r"document\.getElementById\('pg-ctr'\)\.textContent = ctr\.toFixed\(1\) \+ '%';", r"document.getElementById('pg-ctr-ui').textContent = ctr.toFixed(1) + '%';", html)
html = re.sub(r"document\.querySelector\('#pg-ctr'\)", r"document.querySelector('#pg-ctr-ui')", html)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Regex patch applied.")
