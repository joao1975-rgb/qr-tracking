import os
import re

file_path = "templates/dashboard_antigravity_v28.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update DOMContentLoaded initializer to defer charting until data loads.
old_init = """document.addEventListener('DOMContentLoaded', () => {
  // Build charts immediately
  createMainChart();
  createDonut();
  buildHeatmap();

  // Initialize Live Data Stream
  loadLiveScans();
  setInterval(loadLiveScans, 15000);

  // Draw sparklines
  const sparkData = {"""

new_init = """let chartsConfigured = false;
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Live Data Stream
  loadLiveScans();
  setInterval(loadLiveScans, 15000);
  
  loadLiveStats();

  // Draw sparklines (using flat zeros initially until history fills)
  const sparkData = {"""

if old_init in html:
    html = html.replace(old_init, new_init)
    print("Initializer patched")

# 2. Add API parsing logic at the start of loadLiveStats()
old_loadStats = """// Real Data KPI Stats Animation
async function loadLiveStats() {
  try {
    const res = await fetch('/api/analytics/dashboard');
    const data = await res.json();
    if (data.success || data.stats) {
      const stats = data.stats || data;"""

new_loadStats = """// Real Data KPI Stats Animation
async function loadLiveStats() {
  try {
    const res = await fetch('/api/analytics/dashboard');
    const data = await res.json();
    if (data.success || data.stats) {
      const stats = data.stats || data;
      
      // Inject real real data into charts if first load
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
         chartData['7d'] = chartData['30d']; // fallback to 30d scope always for now
         
         // Fix device donut
         if(data.operating_systems && data.operating_systems.length > 0){
             window.sysData = data.operating_systems;
         }
         
         // Fix Heatmap
         if(data.heatmap_data) {
             window.hmData = data.heatmap_data;
         }

         createMainChart();
         createDonut();
         buildHeatmap();
         chartsConfigured = true;
      }
      """

if old_loadStats in html:
    html = html.replace(old_loadStats, new_loadStats)
    print("loadLiveStats patched")

# 3. Patch buildHeatmap to use hmData
old_heatmap = """// Cells
  for (let hr = 0; hr < 24; hr++) {
    for (let day = 0; day < 7; day++) {
      const el = document.createElement('div');
      el.className = 'heatmap-cell';
      
      // procedural dummy 
      let val = Math.random() * 80;
      if (hr > 8 && hr < 20) val += 30; // peak day
      if (day > 4) val += 20; // weekend bump"""

new_heatmap = """// Cells
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
          // day is 0=Lunes, pero SQL DOW 0=Sunday. Ajustar si es necesario.
          // JavaScript day: usually we rendered L M M J V S D
          // PostgreSQL DOW: 0 = Sun, 1 = Mon... 6 = Sat
          let sqlDow = day === 6 ? 0 : day + 1;
          val = hmMap[`${sqlDow}-${hr}`] || 0;
          val = (val / maxHm) * 100; // porcentaje
      } else {
          val = Math.random() * 80;
          if (hr > 8 && hr < 20) val += 30; 
          if (day > 4) val += 20; 
      }"""

if old_heatmap in html:
    html = html.replace(old_heatmap, new_heatmap)
    print("buildHeatmap patched")

# 4. Patch createDonut to use window.sysData
old_donut = """data: [44, 29, 27],
        backgroundColor: ['#00CFFF', '#00E5A0', 'rgba(255,255,255,0.12)'],"""

new_donut = """data: window.sysData ? window.sysData.map(d => d.count) : [44, 29, 27],
        backgroundColor: ['#00CFFF', '#00E5A0', '#A855F7', '#FFAD33', 'rgba(255,255,255,0.12)'],
        labels: window.sysData ? window.sysData.map(d => d.operating_system) : ['OS A','OS B','OS C'],"""

if old_donut in html:
    html = html.replace(old_donut, new_donut)
    print("createDonut patched")

# 5. Patch dummy goals in Progress segment
# "12.309" and "8.980" in the HTML directly
old_p_scans = """<div class="pg-val" id="pg-tot">12.309</div>
              <div class="pg-tar">Meta: 15.000</div>"""

new_p_scans = """<div class="pg-val" id="pg-tot">0</div>
              <div class="pg-tar" id="pg-tot-target">Meta: -</div>"""

if old_p_scans in html:
    html = html.replace(old_p_scans, new_p_scans)
    print("Goals 1 patched")

old_p_uniq = """<div class="pg-val" id="pg-uq">8.980</div>
              <div class="pg-tar">Alcance: 10.000</div>"""

new_p_uniq = """<div class="pg-val" id="pg-uq">0</div>
              <div class="pg-tar" id="pg-uq-target">Alcance: -</div>"""

if old_p_uniq in html:
    html = html.replace(old_p_uniq, new_p_uniq)
    print("Goals 2 patched")

old_p_ctr = """<div class="pg-val" id="pg-ctr">2.8%</div>
              <div class="pg-tar">Objetivo: 2.5%</div>"""

new_p_ctr = """<div class="pg-val" id="pg-ctr">0%</div>
              <div class="pg-tar" id="pg-ctr-target">Objetivo: -</div>"""

if old_p_ctr in html:
    html = html.replace(old_p_ctr, new_p_ctr)
    print("Goals 3 patched")

# 6. Finally, inject JS to populate these goals dynamically in loadLiveStats
old_kpi_anim = """animateCounter(document.getElementById('kpi-total'), total, 2000, 0);"""
new_kpi_anim = """animateCounter(document.getElementById('kpi-total'), total, 2000, 0);
        
        // Populate Targets
        let targetTotal = total > 0 ? Math.ceil(total * 1.5 / 50) * 50 : 100;
        let targetUnique = unique > 0 ? Math.ceil(unique * 1.5 / 25) * 25 : 50;
        
        document.getElementById('pg-tot').textContent = total;
        document.getElementById('pg-tot-target').textContent = `Meta: ${targetTotal}`;
        document.querySelector('#pg-tot').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((total/targetTotal)*100, 100) + '%';
        
        document.getElementById('pg-uq').textContent = unique;
        document.getElementById('pg-uq-target').textContent = `Meta: ${targetUnique}`;
        document.querySelector('#pg-uq').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((unique/targetUnique)*100, 100) + '%';
        
        document.getElementById('pg-ctr').textContent = ctr.toFixed(1) + '%';
        document.getElementById('pg-ctr-target').textContent = `Objetivo: 2.5%`;
        document.querySelector('#pg-ctr').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((ctr/2.5)*100, 100) + '%';
"""

if old_kpi_anim in html:
    html = html.replace(old_kpi_anim, new_kpi_anim)
    print("Goals JS patched")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
print("All patches completely applied.")
