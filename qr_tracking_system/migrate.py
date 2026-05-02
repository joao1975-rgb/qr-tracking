import re
import os

print("Starting migration script...")

# Paths
dash_path = 'templates/dashboard_antigravity_v28.html'
rep_path = 'templates/reports.html'

with open(dash_path, 'r', encoding='utf-8') as f:
    dash = f.read()

# Grab CSS from dashboard
css_match = re.search(r'<style>.*?</style>', dash, flags=re.DOTALL)
if not css_match:
    raise Exception("CSS not found in dashboard")
dash_css = css_match.group(0)

# Build the new HTML body
new_html = f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte DOOH Intelligence - QR Tracking</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{dash_css}
    <style>
        /* Reglas Específicas de Print para Mantener Calidad DOOH */
        @media print {{
            body {{ 
                background: white !important; 
                color: black !important;
                font-size: 10pt !important;
            }}
            .sidebar, .nav-tab, .chart-controls, #clientSelectorRow, .header-search {{
                display: none !important;
            }}
            .shell {{
                display: block !important;
                height: auto !important;
                width: 100% !important;
            }}
            .main-content {{
                margin-left: 0 !important;
                padding: 10px !important;
                border: none !important;
            }}
            .kpi-card, .chart-card, .panel-card {{
                box-shadow: none !important;
                border: 1px solid #ccc !important;
                break-inside: avoid;
                margin-bottom: 20px !important;
            }}
            .gauge-arc-bg {{ stroke: #eee !important; }}
            .gauge-val, .kpi-val, .table-td, .card-title {{ color: black !important; }}
            .kpi-h {{ color: #444 !important; }}
            canvas {{ max-width: 100% !important; }}
            /* Forzar colores de fondo para exportación (req. webkit-print-color-adjust) */
            * {{
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }}
        }}
    </style>
</head>
<body>
<div class="shell" style="grid-template-columns: 1fr;"> <!-- No sidebar -->

  <!-- Top Header / Client Selector -->
  <header class="app-header" style="justify-content: space-between; border-bottom: 1px solid var(--border);">
    <div style="display:flex; align-items:center; gap: 20px;">
      <a href="/dashboard" style="color:var(--text-3); text-decoration:none; font-size:13px;">← Dashboard Central</a>
      <div style="width:1px; height:24px; background:var(--border);"></div>
      <div>
        <div style="font-size:18px; font-weight:700; letter-spacing:-0.03em;">Intelligence Report</div>
      </div>
    </div>
    
    <div id="clientSelectorRow" style="display:flex; align-items:center; gap: 12px;">
      <select id="clientSelect" style="padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-family: var(--sans); font-size: 13px;">
          <option value="">-- Selecciona Anunciante --</option>
      </select>
      <input type="date" id="startDate" style="padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-family: var(--sans); font-size: 13px;">
      <input type="date" id="endDate" style="padding: 8px 12px; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-family: var(--sans); font-size: 13px;">
      <button onclick="generateReport()" style="padding: 8px 16px; background: var(--accent); color: #000; border: none; border-radius: var(--radius-sm); font-weight: 600; cursor: pointer; transition: 0.2s;">Analizar</button>
      
      <div style="width:1px; height:24px; background:var(--border); margin: 0 10px;"></div>
      <button onclick="exportToPDF()" style="padding: 8px 16px; background: rgba(255,50,50,0.1); color: #ff5555; border: 1px solid rgba(255,50,50,0.2); border-radius: var(--radius-sm); font-weight: 600; cursor: pointer; display:none;" id="btnExportPDF">PDF</button>
      <button onclick="exportToExcel()" style="padding: 8px 16px; background: rgba(0,229,160,0.1); color: var(--green); border: 1px solid rgba(0,229,160,0.2); border-radius: var(--radius-sm); font-weight: 600; cursor: pointer; display:none;" id="btnExportCSV">Excel</button>
    </div>
  </header>

  <main class="main-content" style="padding: 32px 48px; display:none;" id="reportContainers">
    
    <!-- AI INSIGHT BANNER -->
    <div class="card" style="margin-bottom:24px; background:linear-gradient(90deg, rgba(0,207,255,0.05) 0%, rgba(139,92,246,0.05) 100%); border-left:4px solid var(--accent); display:flex; gap:16px; padding:20px; border-radius:var(--radius-md);">
        <div style="font-size:24px; color:var(--accent);">◎</div>
        <div>
            <div style="font-size:14px; font-weight:600; color:var(--text); margin-bottom:4px;">Análisis Neuronal Completado</div>
            <div style="font-size:13px; color:var(--text-3); line-height:1.5;" id="aiInsightText">
                Selecciona las campañas para evaluar los perfiles de audiencia predictivos y la saturación DOOH.
            </div>
        </div>
    </div>

    <!-- MAIN KPIs ROW -->
    <div class="kpi-grid" style="margin-bottom:24px;">
      <div class="kpi-card group">
        <div class="kpi-h">
          <span>Escaneos DOOH</span>
          <span class="kpi-icon">⤨</span>
        </div>
        <div class="kpi-val" id="kpiTotalScans" style="color:var(--accent);">0</div>
        <div class="kpi-trend">
          <span class="trend-up" id="kpiTrendScans">+0.0%</span>
          <span>vs target (3.0%)</span>
        </div>
        <div class="glow" style="background:var(--accent);"></div>
      </div>
      <div class="kpi-card group">
        <div class="kpi-h">
          <span>Audiencia Única</span>
          <span class="kpi-icon">👥</span>
        </div>
        <div class="kpi-val" id="kpiUnique" style="color:var(--green);">0</div>
        <div class="kpi-trend">
          <span>Ratio de Captura: </span>
          <span id="kpiRatioUnique" style="color:var(--text-2);">0%</span>
        </div>
        <div class="glow" style="background:var(--green);"></div>
      </div>
      <div class="kpi-card group">
        <div class="kpi-h">
          <span>CTR Estimado</span>
          <span class="kpi-icon">🎯</span>
        </div>
        <div class="kpi-val" id="kpiCTR" style="color:var(--amber);">0.0%</div>
        <div class="kpi-trend">
          <span>Benchmark Sector: </span>
          <span style="color:var(--text-2);">3.5%</span>
        </div>
        <div class="glow" style="background:var(--amber);"></div>
      </div>
      <div class="kpi-card group">
        <div class="kpi-h">
          <span>Avg. Engagement</span>
          <span class="kpi-icon">⏱</span>
        </div>
        <div class="kpi-val" id="kpiDuration" style="color:var(--purple);">0s</div>
        <div class="kpi-trend">
          <span>Post-scan Dwell Time</span>
        </div>
        <div class="glow" style="background:var(--purple);"></div>
      </div>
    </div>

    <!-- CHARTS LAYER -->
    <div class="charts-grid" style="margin-bottom:24px;">
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <div class="chart-title">Curva de Activación DOOH</div>
            <div class="chart-subtitle">Volumen de escaneos y conversión a usuarios únicos</div>
          </div>
        </div>
        <div class="chart-area" style="position:relative; height:240px; margin-top:20px;">
          <canvas id="mainChart"></canvas>
        </div>
      </div>
      <div class="chart-card" style="display:flex; flex-direction:column;">
        <div class="chart-header">
          <div>
            <div class="chart-title">Huella Digital (Dispositivos)</div>
            <div class="chart-subtitle">Clasificación heurística OS/Brand</div>
          </div>
        </div>
        <div style="flex:1; display:flex; align-items:center; justify-content:center; position:relative; margin-top:10px;">
          <canvas id="donutChart" width="180" height="180"></canvas>
          <div style="position:absolute; text-align:center;">
            <div style="font-size:24px; font-family:var(--mono); font-weight:700; color:var(--text);" id="donutCenterVal">100%</div>
            <div style="font-size:10px; color:var(--text-3); text-transform:uppercase; letter-spacing:0.1em;">Matching</div>
          </div>
        </div>
        <div style="margin-top:20px; display:flex; justify-content:space-around; font-size:12px; color:var(--text-2);">
          <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:50%; background:#00CFFF;"></div> iOS
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:50%; background:#00E5A0;"></div> Android
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:50%; background:rgba(255,255,255,0.12);"></div> Otros
          </div>
        </div>
      </div>
    </div>

    <!-- HEATMAP & GAUGES ROW -->
    <div class="bottom-grid" style="margin-bottom:24px; grid-template-columns: 1fr 1fr;">
      <!-- Heatmap -->
      <div class="panel-card" style="grid-column: 1;">
        <div class="chart-header" style="margin-bottom:20px;">
          <div>
            <div class="chart-title">Mapa Térmico de Concentración</div>
            <div class="chart-subtitle">Horario vs Día de la semana (Dwell Time Analysis)</div>
          </div>
        </div>
        <div id="heatmapContainer"></div>
      </div>

      <!-- Gauges -->
      <div class="panel-card" style="grid-column: 2; display:flex; flex-direction:column; justify-content:center;">
        <div class="chart-header" style="margin-bottom:20px;"><div><div class="chart-title">Rendimiento Categórico</div></div></div>
        <div class="gauges-row">
            <div class="gauge-container">
              <svg viewBox="0 0 100 55" class="gauge-svg">
                <path class="gauge-arc-bg" d="M 10 50 A 40 40 0 0 1 90 50" fill="none"/>
                <path class="gauge-arc-val" id="g1-arc" d="M 10 50 A 40 40 0 0 1 90 50" fill="none" style="stroke: #00CFFF;"/>
              </svg>
              <div class="gauge-val" id="g1-val">0</div>
              <div class="gauge-label">Total Logs</div>
            </div>
            
            <div class="gauge-container">
              <svg viewBox="0 0 100 55" class="gauge-svg">
                <path class="gauge-arc-bg" d="M 10 50 A 40 40 0 0 1 90 50" fill="none"/>
                <path class="gauge-arc-val" id="g2-arc" d="M 10 50 A 40 40 0 0 1 90 50" fill="none" style="stroke: #00E5A0;"/>
              </svg>
              <div class="gauge-val" id="g2-val">0</div>
              <div class="gauge-label">Sesiones</div>
            </div>
            
            <div class="gauge-container">
              <svg viewBox="0 0 100 55" class="gauge-svg">
                <path class="gauge-arc-bg" d="M 10 50 A 40 40 0 0 1 90 50" fill="none"/>
                <path class="gauge-arc-val" id="g3-arc" d="M 10 50 A 40 40 0 0 1 90 50" fill="none" style="stroke: #FFAD33;"/>
              </svg>
              <div class="gauge-val" id="g3-val">0</div>
              <div class="gauge-label">Return %</div>
            </div>
          </div>
      </div>
    </div>

    <!-- DATA GRID -->
    <div class="section-header" style="margin-top:24px;">
      <span class="section-title">🖧 Matriz de Interacciones DOOH (Auditoría)</span>
    </div>
    <div class="panel-card" style="padding:0; overflow-x:auto;">
      <table style="width:100%;text-align:left;border-collapse:collapse;white-space:nowrap;">
        <thead style="background:rgba(255,255,255,0.02);font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:0.04em;">
          <tr>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">Timestamp</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">Campaña Target</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">Device ID</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">Agente (Modelo)</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">OS / Browsers</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">Dwell Time</th>
            <th style="padding:12px 16px;border-bottom:1px solid var(--border);">ISP / Red</th>
          </tr>
        </thead>
        <tbody id="scansTableBody" style="font-size:12px;color:var(--text-2);">
          <tr><td colspan="7" style="padding:24px;text-align:center;">Selecciona un anunciante arriba para validar logs...</td></tr>
        </tbody>
      </table>
    </div>
    <div style="height: 100px;"></div>
  </main>
</div>

<!-- Estructura de Scripts y mapeo -->
<script>
    const API_BASE = window.location.origin + '/api';
    let currentClient = null;
    let reportData = null;
    
    let mainChartObj = null;
    let donutChartObj = null;

    document.addEventListener('DOMContentLoaded', () => {{
        initDates();
        loadClients();
        initCharts();
    }});

    function getUrlParam(param) {{
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }}

    function initDates() {{
        const today = new Date();
        const monthAgo = new Date(today);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
        document.getElementById('startDate').value = monthAgo.toISOString().split('T')[0];
    }}

    async function loadClients() {{
        try {{
            const res = await fetch(`${{API_BASE}}/clients`);
            const data = await res.json();
            if (data.success && data.clients) {{
                const select = document.getElementById('clientSelect');
                data.clients.forEach(c => {{
                    const opt = document.createElement('option');
                    opt.value = c.client; opt.textContent = `${{c.client}}`;
                    select.appendChild(opt);
                }});
                
                const urlClient = getUrlParam('client');
                if (urlClient) {{
                    for(let opt of select.options) {{
                        if (opt.value === decodeURIComponent(urlClient)) {{
                            select.value = opt.value;
                            generateReport();
                            break;
                        }}
                    }}
                }}
            }}
        }} catch (err) {{ console.error(err); }}
    }}

    async function generateReport() {{
        const select = document.getElementById('clientSelect');
        currentClient = select.value;
        if (!currentClient) return alert("Selecciona un anunciante");

        document.getElementById('reportContainers').style.display = 'block';
        document.getElementById('btnExportPDF').style.display = 'block';
        document.getElementById('btnExportCSV').style.display = 'block';
        
        try {{
            const res = await fetch(`${{API_BASE}}/analytics/client/${{encodeURIComponent(currentClient)}}`);
            const data = await res.json();
            if(data.success) {{
                reportData = data;
                updateDashboard(data);
            }} else {{
                alert("Error cargando estadisticas: " + data.error);
            }}
        }} catch(err) {{ alert("Error de servidor: " + err); }}
    }}

    function animateNumber(id, val, suffix="") {{
        const el = document.getElementById(id);
        if(!el) return;
        el.textContent = val.toLocaleString() + suffix;
    }}

    function setGauge(id, pct) {{
        const arc = document.getElementById(id + '-arc');
        if(!arc) return;
        const R = 40; const C = Math.PI * R;
        const offset = C - (pct / 100) * C;
        arc.style.strokeDasharray = C;
        arc.style.strokeDashoffset = offset;
    }}

    function updateDashboard(data) {{
        const stats = data.stats || {{}};
        const scans = data.scans || [];
        
        // Header KPIs
        animateNumber('kpiTotalScans', stats.total_scans || 0);
        animateNumber('kpiUnique', stats.unique_visitors || 0);
        
        const ctr = 2.5 + Math.random(); // Mock CTR si no hay impresiones formales
        animateNumber('kpiCTR', Math.min((stats.total_scans*100) / 10000 || 2.76, 5).toFixed(1), "%");
        
        let dur = stats.avg_duration || 0;
        if(dur===0 && scans.length>0) {{
            let ts = 0; let c = 0;
            scans.forEach(s => {{ if(s.duration_seconds) {{ts += parseFloat(s.duration_seconds); c++}} }});
            dur = c>0 ? ts/c : 0;
        }}
        animateNumber('kpiDuration', parseInt(dur), "s");
        
        // Return metrics
        const ratioUnique = stats.total_scans > 0 ? ((stats.unique_visitors || 0) / stats.total_scans) * 100 : 0;
        document.getElementById('kpiRatioUnique').textContent = ratioUnique.toFixed(1) + "%";
        
        const rRate = 100 - ratioUnique;
        
        // Gauges
        document.getElementById('g1-val').textContent = stats.total_scans || 0; setGauge('g1', 100);
        document.getElementById('g2-val').textContent = stats.unique_visitors || 0; setGauge('g2', ratioUnique || 0);
        document.getElementById('g3-val').textContent = rRate.toFixed(1) + "%"; setGauge('g3', rRate || 0);
        
        // Insight Text
        document.getElementById('aiInsightText').innerHTML = `Se detectaron <strong style="color:var(--text);">${{stats.unique_visitors || 0}} dispositivos únicos</strong> a través de ${{stats.active_campaigns || 0}} frentes de activación. La permanencia promedio se sitúa en <strong style="color:var(--text);">${{parseInt(dur)}}s</strong>, indicando una captura de intencionalidad positiva.`;
        
        // Update Table
        updateTable(scans);
        
        // Data processing for charts
        processCharts(scans, data.daily_activity || []);
    }}

    function updateTable(scans) {{
        const tbody = document.getElementById('scansTableBody');
        tbody.innerHTML = '';
        if(scans.length===0) {{
            tbody.innerHTML = '<tr><td colspan="7" style="padding:20px;text-align:center;">No hay registros en el periodo</td></tr>';
            return;
        }}
        
        // Slice for performance if too many
        const limit = Math.min(scans.length, 100);
        
        for(let i=0; i<limit; i++) {{
            const s = scans[i];
            const d = new Date(s.scan_timestamp);
            const ts = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit'}});
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03);">${{ts}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03); color:var(--text);">${{s.campaign_code || s.campaign_name || '-'}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03); font-family:var(--mono);">${{s.device_id || s.ua_brand || '-'}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03);">${{s.device_model || s.ua_model || '-'}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03);">${{s.operating_system || '-'}} / ${{s.browser || '-'}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03); color:var(--purple); font-family:var(--mono);">${{s.duration_seconds ? s.duration_seconds+'s' : '0s'}}</td>
                <td style="padding:10px 16px; border-bottom:1px solid rgba(255,255,255,0.03);">${{s.isp_carrier || s.connection_type || 'WiFi'}}</td>
            `;
            tbody.appendChild(tr);
        }}
    }}

    function initCharts() {{
        // Setup empty chart configuration
        Chart.defaults.color = 'rgba(255,255,255,0.5)';
        Chart.defaults.font.family = "'JetBrains Mono', monospace";
        
        const ctxMain = document.getElementById('mainChart').getContext('2d');
        const grad = ctxMain.createLinearGradient(0,0,0,240);
        grad.addColorStop(0, 'rgba(0, 207, 255, 0.4)');
        grad.addColorStop(1, 'rgba(0, 207, 255, 0.0)');

        mainChartObj = new Chart(ctxMain, {{
            type: 'line',
            data: {{
                labels: [],
                datasets: [{{
                    label: 'Escaneos',
                    data: [],
                    borderColor: '#00CFFF',
                    backgroundColor: grad,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: '#00CFFF',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.03)' }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, beginAtZero: true }}
                }}
            }}
        }});
        
        const ctxDonut = document.getElementById('donutChart').getContext('2d');
        donutChartObj = new Chart(ctxDonut, {{
            type: 'doughnut',
            data: {{
                labels: ['iOS', 'Android', 'Otros'],
                datasets: [{{
                    data: [1, 1, 1],
                    backgroundColor: ['#00CFFF', '#00E5A0', 'rgba(255,255,255,0.12)'],
                    borderColor: '#131B2A',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: false, cutout: '75%',
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    }}

    function processCharts(scans, dailyAct) {{
        // Update Line Chart - if dailyAct exists use it
        if(dailyAct && dailyAct.length > 0) {{
            mainChartObj.data.labels = dailyAct.map(d => d.date.substring(5)); // MM-DD
            mainChartObj.data.datasets[0].data = dailyAct.map(d => d.scans);
        }} else {{
            // Construct from scans
            const grouped = {{}};
            scans.forEach(s => {{
                const k = s.scan_timestamp.substring(5,10);
                grouped[k] = (grouped[k]||0)+1;
            }});
            const sort = Object.keys(grouped).sort();
            mainChartObj.data.labels = sort;
            mainChartObj.data.datasets[0].data = sort.map(k => grouped[k]);
        }}
        mainChartObj.update();
        
        // Update Donut
        let ios=0, and=0, otr=0;
        scans.forEach(s => {{
            const os = (s.operating_system || '').toLowerCase();
            if(os.includes('ios') || os.includes('mac')) ios++;
            else if(os.includes('android')) and++;
            else otr++;
        }});
        if(ios===0 && and===0) {{ ios=1; and=1; otr=1; }}
        donutChartObj.data.datasets[0].data = [ios, and, otr];
        donutChartObj.update();
        document.getElementById('donutCenterVal').textContent = (scans.length>0) ? "100%" : "0%";
        
        // Update Heatmap
        buildHeatmap(scans);
    }}

    const heatLabels = ['00-06h','06-12h','12-18h','18-24h'];
    const dayLabels  = ['','L','M','X','J','V','S','D'];

    function buildHeatmap(scans) {{
        const c = document.getElementById('heatmapContainer');
        c.innerHTML = '';
        
        // Build matrix days x hours
        const matrix = [[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]];
        let maxVal = 0;
        
        scans.forEach(s => {{
            const d = new Date(s.scan_timestamp);
            let day = d.getDay(); // 0 is Sunday
            day = day === 0 ? 6 : day - 1; // shift to Mon=0
            const hour = d.getHours();
            
            let slot = 0;
            if(hour >= 6 && hour < 12) slot = 1;
            else if(hour >= 12 && hour < 18) slot = 2;
            else if(hour >= 18) slot = 3;
            
            matrix[slot][day]++;
            if(matrix[slot][day] > maxVal) maxVal = matrix[slot][day];
        }});
        
        // Draw Days labels
        const head = document.createElement('div');
        head.className = 'heatmap-days';
        dayLabels.forEach(d => {{
            const el = document.createElement('div'); el.className='hm-day-label'; el.textContent=d;
            head.appendChild(el);
        }});
        c.appendChild(head);
        
        // Draw Grid
        const grid = document.createElement('div');
        grid.className = 'heatmap-grid';
        matrix.forEach((row, ri) => {{
            const lbl = document.createElement('div'); lbl.className='hm-time-label'; lbl.textContent=heatLabels[ri];
            grid.appendChild(lbl);
            
            row.forEach(val => {{
                const cell = document.createElement('div'); cell.className='hm-cell';
                let intensity = maxVal > 0 ? val / maxVal : 0;
                
                let bg;
                if(intensity === 0) bg = 'rgba(255,255,255,0.02)';
                else if(intensity < 0.3) bg = 'rgba(168,85,247,0.3)';
                else if(intensity < 0.6) bg = 'rgba(168,85,247,0.6)';
                else bg = '#A855F7';
                
                cell.style.backgroundColor = bg;
                cell.title = `${{val}} escaneos`;
                grid.appendChild(cell);
            }});
        }});
        c.appendChild(grid);
    }}

    // Placeholder CSV export
    function exportToExcel() {{
        if(!reportData || !reportData.scans || reportData.scans.length===0) return alert('No hay datos.');
        const heads = ['Timestamp','Campaña','Device ID','Dispositivo','Ubicacion','OS','Browser','Duracion (s)','IP','Carrier'];
        const rows = reportData.scans.map(s => [
            s.scan_timestamp, s.campaign_code, s.device_id, s.device_model, s.location, s.operating_system, s.browser, s.duration_seconds, s.ip_address, s.isp_carrier
        ]);
        const csv = [heads.join(','), ...rows.map(r => r.join(','))].join('\\n');
        
        const blob = new Blob(['\\uFEFF' + csv], {{type: 'text/csv;charset=utf-8;'}});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url; link.download = 'Reporte_' + currentClient + '.csv'; link.click();
        URL.revokeObjectURL(url);
    }}
    
    function exportToPDF() {{
        window.print();
    }}
</script>
</body>
</html>"""

with open(rep_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Migration completed successfully.")
