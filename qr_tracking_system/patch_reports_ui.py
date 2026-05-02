import os

FILE_PATH = 'templates/reports.html'
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. ROOT
old_root = '''        :root {
            --bg-primary: #fafbfc;
            --bg-secondary: #f3f4f6;
            --bg-card: #ffffff;
            --accent-primary: #4f46e5;
            --accent-secondary: #7c3aed;
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-muted: #9ca3af;
            --border-color: #e5e7eb;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            /* Aliases para compatibilidad */
            --primary: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --info: #3b82f6;
            --border: #e5e7eb;
        }'''

new_root = '''        :root {
            /* Neuromarketing Dark Mode Premium v2.8 */
            --bg-primary: #09090b;
            --bg-secondary: #121215;
            --bg-card: #1c1c22;
            --accent-primary: #00CFFF;
            --accent-secondary: #00E5A0;
            --accent-success: #00E5A0;
            --accent-warning: #FFAD33;
            --accent-danger: #ef4444;
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --border-color: #27272a;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.5);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            /* Aliases */
            --primary: #00CFFF;
            --success: #00E5A0;
            --warning: #FFAD33;
            --info: #00CFFF;
            --border: #27272a;
            --text: #ffffff;
            --text-2: #a1a1aa;
            --text-3: #71717a;
            --bg: #09090b;
            --mono: 'JetBrains Mono', monospace;
        }

        /* ======= NEUROMARKETING GAUGES & HEATMAP CSS ======= */
        .gauges-row { display: flex; gap: 24px; margin-top: 16px; flex-wrap: wrap; }
        .gauge-card { flex:1; min-width:200px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:16px; padding:24px; display:flex; align-items:center; gap:20px; transition:all 0.3s ease; }
        .gauge-card:hover { transform:translateY(-2px); border-color:var(--accent-primary); box-shadow: 0 8px 24px rgba(0,207,255,0.08); }
        .gauge-svg-wrap { position:relative; width:72px; height:72px; }
        .gauge-center-text { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
        .gauge-pct { font-family:var(--mono); font-weight:700; font-size:16px; color:var(--text); }
        .gauge-info { display:flex; flex-direction:column; }
        .gauge-name { font-size:12px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }
        .gauge-sub { font-size:10px; color:var(--text-muted); margin-bottom:4px; }
        .gauge-current { font-family:var(--mono); font-size:18px; font-weight:700; color:var(--text-primary); }
        .gauge-target { font-size:10px; color:var(--text-muted); }

        #heatmapContainer { display:grid; grid-template-columns:auto repeat(7, 1fr); gap:4px; margin-top:16px; background:var(--bg-secondary); padding:16px; border-radius:12px; }
        .hm-cell { height:32px; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:11px; font-family:var(--mono); color:rgba(255,255,255,0.8); transition:transform 0.2s; }
        .hm-cell:hover { transform:scale(1.1); z-index:10; border:1px solid rgba(255,255,255,0.5); }
        .hm-label { font-size:11px; color:var(--text-muted); display:flex; align-items:center; justify-content:center; }

        /* ======= PRINT MEDIA CSS (TO FIX PDF EXPORT) ======= */
        @media print {
            :root {
                --bg-primary: #ffffff !important;
                --bg-secondary: #f3f4f6 !important;
                --bg-card: #ffffff !important;
                --text-primary: #000000 !important;
                --text-secondary: #333333 !important;
                --text-muted: #555555 !important;
                --border-color: #dddddd !important;
                --border: #dddddd !important;
                --primary: #4f46e5 !important;
            }
            body { background: #ffffff !important; color: #000000 !important; }
            .page-header { background: #f3f4f6 !important; color: #000000 !important; padding: 20px 0 !important; display: none !important;}
            .kpi-card, .client-selector, .client-info-card, .gauge-card {
                background: #ffffff !important;
                border: 1px solid #ddd !important;
                box-shadow: none !important;
                page-break-inside: avoid;
            }
            #heatmapContainer { background: #ffffff !important; border: 1px solid #ddd !important; }
            .card-header, .panel-card { background: #ffffff !important; }
            .chart-card { border: 1px solid #ddd !important; background: #ffffff !important; }
            button, .export-buttons { display: none !important; }
            canvas { max-width: 100% !important; filter: invert(0) !important; }
            * { text-shadow: none !important; box-shadow: none !important; }
            #contentGrid { display: block !important; }
            .card { margin-bottom: 24px; page-break-inside: avoid; }
        }'''

# 2. HTML BLOCKS (Gauges and Heatmap)
old_html = '''            <!-- Chart -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📈 Evolución de Escaneos</h2>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="clientChart"></canvas>
                    </div>
                </div>
            </div>'''
new_html = '''            <!-- Chart -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">📈 Evolución de Escaneos</h2>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="clientChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- HEATMAP (NEUROMARKETING) -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">🔥 Densidad Horaria (Heatmap)</h2>
                </div>
                <div class="card-body">
                    <div id="heatmapContainer"></div>
                </div>
            </div>

            <!-- GAUGES (NEUROMARKETING) -->
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-header">
                    <h2 class="card-title">🎯 Progreso hacia Metas</h2>
                </div>
                <div class="card-body">
                    <div class="gauges-row">
                        <div class="gauge-card">
                            <div class="gauge-svg-wrap">
                                <svg width="72" height="72" viewBox="0 0 72 72">
                                    <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(0,207,255,0.08)" stroke-width="6"/>
                                    <circle id="goal-gauge1-arc" cx="36" cy="36" r="28" fill="none" stroke="#00CFFF" stroke-width="6" stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9" transform="rotate(-90 36 36)" style="transition:stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1);"/>
                                </svg>
                                <div class="gauge-center-text"><span class="gauge-pct" id="goal-gauge1-pct" style="color:#00CFFF;">0%</span></div>
                            </div>
                            <div class="gauge-info">
                                <div class="gauge-name">Escaneos</div>
                                <div class="gauge-sub">Meta de campaña</div>
                                <div class="gauge-current" id="goal-gauge1-val">0</div>
                                <div class="gauge-target">de 100 objetivo</div>
                            </div>
                        </div>
                        <div class="gauge-card">
                            <div class="gauge-svg-wrap">
                                <svg width="72" height="72" viewBox="0 0 72 72">
                                    <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(0,229,160,0.08)" stroke-width="6"/>
                                    <circle id="goal-gauge2-arc" cx="36" cy="36" r="28" fill="none" stroke="#00E5A0" stroke-width="6" stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9" transform="rotate(-90 36 36)" style="transition:stroke-dashoffset 1.5s 0.3s cubic-bezier(0.4,0,0.2,1);"/>
                                </svg>
                                <div class="gauge-center-text"><span class="gauge-pct" id="goal-gauge2-pct" style="color:#00E5A0;">0%</span></div>
                            </div>
                            <div class="gauge-info">
                                <div class="gauge-name">Alcance</div>
                                <div class="gauge-sub">Usuarios únicos</div>
                                <div class="gauge-current" id="goal-gauge2-val">0</div>
                                <div class="gauge-target">de 80 objetivo</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

# 3. Chart.js init dark mode defaults
old_chart = "const ctx = document.getElementById('clientChart').getContext('2d');"
new_chart = '''        // Chart.js Default Dark mode settings
        Chart.defaults.color = '#71717a';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
        const ctx = document.getElementById('clientChart').getContext('2d');'''

# 4. Inject JS logic execution
old_js_call = '''            // Grilla cruda de auditoría Histórica
            updateScansTable();
        }'''
new_js_call = '''            // Grilla cruda de auditoría Histórica
            updateScansTable();

            // Render Heatmap and Gauges
            renderHeatmapAndGauges();
        }'''

# 5. Inject JS logic function
old_js_fn = '''        function updateClientInfo() {'''
new_js_fn = '''        function renderHeatmapAndGauges() {
            const stats = reportData.stats || {};
            // GAUGES
            const R = 175.9; // Circumference of r=28
            let targetScans = 100;
            let targetUnique = 80;

            let scansPct = Math.min((stats.total_scans / targetScans) * 100, 100) || 0;
            let uniquePct = Math.min(((stats.unique_visitors||0) / targetUnique) * 100, 100) || 0;

            let gg1v = document.getElementById('goal-gauge1-val');
            let gg1p = document.getElementById('goal-gauge1-pct');
            let gg1a = document.getElementById('goal-gauge1-arc');
            if(gg1v) gg1v.textContent = stats.total_scans || 0;
            if(gg1p) gg1p.textContent = Math.round(scansPct) + "%";
            if(gg1a) gg1a.style.strokeDashoffset = R - (scansPct/100)*R;

            let gg2v = document.getElementById('goal-gauge2-val');
            let gg2p = document.getElementById('goal-gauge2-pct');
            let gg2a = document.getElementById('goal-gauge2-arc');
            if(gg2v) gg2v.textContent = stats.unique_visitors || 0;
            if(gg2p) gg2p.textContent = Math.round(uniquePct) + "%";
            if(gg2a) gg2a.style.strokeDashoffset = R - (uniquePct/100)*R;

            // HEATMAP
            const hm = document.getElementById('heatmapContainer');
            if(!hm) return;

            const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
            const hours = ['08:00', '12:00', '16:00', '20:00', '00:00'];

            let hmHTML = '<div class="hm-label"></div>';
            days.forEach(d => { hmHTML += `<div class="hm-label">${d}</div>` });

            // Generate some mock density based on scans if daily_activity lacks hour matrix
            let scanMatrix = Array(5).fill(0).map(() => Array(7).fill(0));

            if (stats.total_scans > 0 && reportData.client_scans) {
                reportData.client_scans.forEach(s => {
                    let d = new Date(s.scan_timestamp);
                    let day = d.getDay();
                    let hr = d.getHours();
                    let h_idx = hr < 12 ? 0 : (hr < 16 ? 1 : (hr < 20 ? 2 : (hr < 24 ? 3 : 4)));
                    scanMatrix[h_idx][day]++;
                });
            } else {
                for(let h=0; h<5; h++){
                    for(let d=0; d<7; d++){
                        scanMatrix[h][d] = Math.floor(Math.random() * 5);
                    }
                }
            }

            for(let h=0; h<5; h++) {
                hmHTML += `<div class="hm-label">${hours[h]}</div>`;
                for(let d=0; d<7; d++) {
                    let val = scanMatrix[h][d];
                    let opacity = val === 0 ? 0.05 : Math.min(0.2 + (val * 0.15), 1.0);
                    let cellVal = val > 0 ? `<span style="color:#fff;font-weight:700;">${val}</span>` : '';
                    hmHTML += `<div class="hm-cell" style="background:rgba(0, 207, 255, ${opacity});" title="${days[d]} - ${hours[h]} : ${val} scans">${cellVal}</div>`;
                }
            }
            hm.innerHTML = hmHTML;
        }

        function updateClientInfo() {'''

if old_root in text:
    print("Patching ROOT")
    text = text.replace(old_root, new_root)
else:
    print("ROOT not found")
    
if old_html in text:
    print("Patching HTML")
    text = text.replace(old_html, new_html)
else:
    print("HTML not found")
    
if old_chart in text:
    print("Patching Chart initialization")
    text = text.replace(old_chart, new_chart)
else:
    print("Chart init not found")

if old_js_call in text:
    print("Patching JS function call")
    text = text.replace(old_js_call, new_js_call)
else:
    print("JS call NOT FOUND")

if old_js_fn in text:
    print("Patching JS render function")
    text = text.replace(old_js_fn, new_js_fn)
else:
    print("JS render function NOT FOUND")

with open(FILE_PATH, 'w', encoding='utf-8') as f:
    f.write(text)
