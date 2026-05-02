import re
import os

reports_file = 'templates/reports.html'
with open(reports_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Make sure not to double inject
if 'id="goal-gauge1-arc"' not in html:
    gauges_html = '''
    <!-- GOAL GAUGES -->
    <div class="section-header" style="margin-top:24px; margin-bottom:16px;">
      <span class="section-title">Progreso hacia metas</span>
      <span class="section-hint">Datos Históricos · Meta Base: 100 Escaneos</span>
    </div>
    <div class="gauges-row" style="margin-bottom:24px;">

      <div class="gauge-card">
        <div class="gauge-svg-wrap">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(0,207,255,0.08)" stroke-width="6"/>
            <circle id="goal-gauge1-arc" cx="36" cy="36" r="28" fill="none" stroke="#00CFFF" stroke-width="6"
              stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9"
              transform="rotate(-90 36 36)" style="transition:stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1);"/>
          </svg>
          <div class="gauge-center-text">
            <span class="gauge-pct" id="goal-gauge1-pct" style="color:#00CFFF;">0%</span>
          </div>
        </div>
        <div class="gauge-info">
          <div class="gauge-name">Escaneos</div>
          <div class="gauge-sub" style="font-size:10px; color:var(--text-3); margin-bottom:4px;">Meta de la campaña</div>
          <div class="gauge-current" id="goal-gauge1-val" style="font-family:var(--mono); color:var(--text); font-weight:700; font-size:14px;">0</div>
          <div class="gauge-target" id="goal-gauge1-target" style="font-size:10px; color:var(--text-3);">de 100 objetivo</div>
        </div>
      </div>

      <div class="gauge-card">
        <div class="gauge-svg-wrap">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(0,229,160,0.08)" stroke-width="6"/>
            <circle id="goal-gauge2-arc" cx="36" cy="36" r="28" fill="none" stroke="#00E5A0" stroke-width="6"
              stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9"
              transform="rotate(-90 36 36)" style="transition:stroke-dashoffset 1.5s 0.3s cubic-bezier(0.4,0,0.2,1);"/>
          </svg>
          <div class="gauge-center-text">
            <span class="gauge-pct" id="goal-gauge2-pct" style="color:#00E5A0;">0%</span>
          </div>
        </div>
        <div class="gauge-info">
          <div class="gauge-name">Visitantes Únicos</div>
          <div class="gauge-sub" style="font-size:10px; color:var(--text-3); margin-bottom:4px;">Meta de alcance</div>
          <div class="gauge-current" id="goal-gauge2-val" style="font-family:var(--mono); color:var(--text); font-weight:700; font-size:14px;">0</div>
          <div class="gauge-target" id="goal-gauge2-target" style="font-size:10px; color:var(--text-3);">de 80 objetivo</div>
        </div>
      </div>

      <div class="gauge-card">
        <div class="gauge-svg-wrap">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(255,173,51,0.08)" stroke-width="6"/>
            <circle id="goal-gauge3-arc" cx="36" cy="36" r="28" fill="none" stroke="#FFAD33" stroke-width="6"
              stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9"
              transform="rotate(-90 36 36)" style="transition:stroke-dashoffset 1.5s 0.6s cubic-bezier(0.4,0,0.2,1);"/>
          </svg>
          <div class="gauge-center-text">
            <span class="gauge-pct" id="goal-gauge3-pct" style="color:#FFAD33;">0%</span>
          </div>
        </div>
        <div class="gauge-info">
          <div class="gauge-name">CTR Objetivo</div>
          <div class="gauge-sub" style="font-size:10px; color:var(--text-3); margin-bottom:4px;">vs. 3.5% meta</div>
          <div class="gauge-current" id="goal-gauge3-val" style="font-family:var(--mono); color:var(--text); font-weight:700; font-size:14px;">0%</div>
          <div class="gauge-target" style="font-size:10px; color:var(--text-3);">benchmark sector: 3.5%</div>
        </div>
      </div>

    </div>
'''

    # Insert the gauges before CHARTS LAYER
    html = html.replace('<!-- CHARTS LAYER -->', gauges_html + '\\n    <!-- CHARTS LAYER -->')

    # Now add the javascript logic explicitly replacing // Gauges
    js_logic = '''
        // Update Goal Gauges
        const R = 175.9; // Circumference of r=28
        let targetScans = 100;
        let targetUnique = 80;
        let targetCTR = 3.5;
        
        let scansPct = Math.min((stats.total_scans / targetScans) * 100, 100) || 0;
        let uniquePct = Math.min(((stats.unique_visitors||0) / targetUnique) * 100, 100) || 0;
        let ctrPctNum = Math.min((((stats.total_scans*100) / 10000 || 2.76) / targetCTR) * 100, 100);
        
        document.getElementById('goal-gauge1-val').textContent = stats.total_scans || 0;
        document.getElementById('goal-gauge1-pct').textContent = Math.round(scansPct) + "%";
        if(document.getElementById('goal-gauge1-arc')) document.getElementById('goal-gauge1-arc').style.strokeDashoffset = R - (scansPct/100)*R;
        
        document.getElementById('goal-gauge2-val').textContent = stats.unique_visitors || 0;
        document.getElementById('goal-gauge2-pct').textContent = Math.round(uniquePct) + "%";
        if(document.getElementById('goal-gauge2-arc')) document.getElementById('goal-gauge2-arc').style.strokeDashoffset = R - (uniquePct/100)*R;
        
        document.getElementById('goal-gauge3-val').textContent = ((stats.total_scans*100)/10000 || 2.76).toFixed(1) + "%";
        document.getElementById('goal-gauge3-pct').textContent = Math.round(ctrPctNum) + "%";
        if(document.getElementById('goal-gauge3-arc')) document.getElementById('goal-gauge3-arc').style.strokeDashoffset = R - (ctrPctNum/100)*R;

        // Gauges'''

    html = html.replace('// Gauges', js_logic)

    with open(reports_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Injected Goal Gauges into reports.html")
else:
    print("Gauges already in reports!")
