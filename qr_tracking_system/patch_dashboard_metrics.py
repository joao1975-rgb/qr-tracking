import os

file_path = "templates/dashboard_antigravity_v28.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update Avg. Engagement HTML
old_engagement = """    <div class="kpi-card" style="--card-accent:#A855F7;--card-glow:rgba(168,85,247,0.05);">
      <div class="kpi-label"><span class="kpi-label-icon">⏱</span> Avg. Engagement</div>
      <div class="kpi-value" id="kpi-dur">0<span class="unit">seg</span></div>
      <div class="kpi-footer">
        <span class="kpi-delta up">▲ 8s más</span>
        <span class="kpi-compare">sector: 50s</span>
        <canvas class="kpi-sparkline" id="spark-dur"></canvas>
      </div>"""

new_engagement = """    <div class="kpi-card" style="--card-accent:#A855F7;--card-glow:rgba(168,85,247,0.05);">
      <div class="kpi-label kpi-tooltip-wrapper">
        <span class="kpi-label-icon">⏱</span> Avg. Engagement
        <div class="kpi-tooltip" style="--accent: #A855F7;">
          <span class="kpi-tooltip-title">Cálculo: Suma Tiempo de Estadía / Escaneos</span>
          Promedio de tiempo orgánico que el usuario pasa explorando la experiencia web posterior al escaneo (antes de rebotar o completar conversión).
        </div>
      </div>
      <div class="kpi-value" id="kpi-dur">0<span class="unit">s</span></div>
      <div class="kpi-footer" id="kpi-dur-footer">
        <span class="kpi-delta" id="kpi-dur-delta"></span>
        <span class="kpi-compare" id="kpi-dur-bench"></span>
        <canvas class="kpi-sparkline" id="spark-dur"></canvas>
      </div>"""

html = html.replace(old_engagement, new_engagement)

# 2. Update Tasa de Recurrencia HTML
old_recurrence_footer = """      <div class="kpi-footer">
        <span class="kpi-delta up">Scans / Usuario</span>
        <span class="kpi-compare">Lealtad y Engagement</span>
      </div>"""

new_recurrence_footer = """      <div class="kpi-footer">
        <span class="kpi-delta up">Global (Promedio)</span>
        <span class="kpi-compare" id="kpi-rec-bench">Lealtad y Engagement</span>
      </div>"""

html = html.replace(old_recurrence_footer, new_recurrence_footer)

old_recurrence_tooltip = """        <div class="kpi-tooltip" style="--accent: #00E5A0;">
          <span class="kpi-tooltip-title">Cálculo: Escaneos Totales / Usuarios Únicos</span>
          Mide la frecuencia promedio con la que un mismo usuario interactúa de forma orgánica. Demuestra lealtad e involucramiento (engagement) continuo a la campaña.
        </div>"""

new_recurrence_tooltip = """        <div class="kpi-tooltip" style="--accent: #00E5A0;">
          <span class="kpi-tooltip-title">Multiscan Core + Promedio Global</span>
          El valor grande es el Promedio Global (Escaneos Totales / Usuarios Únicos). El texto debajo es el <b>Multiscan Core</b>, calculado únicamente con los usuarios leales que te escanearon más de 1 vez, descartando a los rebotados simples.
        </div>"""

html = html.replace(old_recurrence_tooltip, new_recurrence_tooltip)

# 3. Update Javascript for Recurrence and Engagement
js_old_dur = """        // Duration
        const durEl = document.getElementById('kpi-dur');
        if (durEl) animateCounter(durEl, Math.floor(duration), 1600, 0);"""

js_new_dur = """        // Duration
        const durEl = document.getElementById('kpi-dur');
        const durFooter = document.getElementById('kpi-dur-footer');
        if (durEl) {
            let durValue = Math.floor(duration);
            if (durValue <= 0) {
                // Not enough tracking data
                durEl.innerHTML = '<span style="font-size:16px; letter-spacing:0; font-weight:600; color:var(--text-3);">Sin info suficiente</span>';
                if (document.getElementById('kpi-dur-delta')) document.getElementById('kpi-dur-delta').style.display = 'none';
                if (document.getElementById('kpi-dur-bench')) document.getElementById('kpi-dur-bench').textContent = 'Esperando métricas...';
            } else {
                animateCounter(durEl, durValue, 1600, 0);
            }
        }"""

html = html.replace(js_old_dur, js_new_dur)

js_old_rec = """        // Tasa de Recurrencia
        const recEl = document.getElementById('kpi-rec');
        if (recEl) {
          // Si no hay únicos, devolvemos 0, sino scans/uniques (e.g 58/25 = 2.3)
          const recValue = stats.unique_visitors && stats.unique_visitors > 0 ? (stats.total_scans / stats.unique_visitors) : 0;
          let v = 0;
          const iv = setInterval(() => {
            v = Math.min(v + (recValue/30), recValue);
            recEl.childNodes[0].textContent = v.toFixed(1);
            if (v >= recValue) {
              clearInterval(iv);
              recEl.childNodes[0].textContent = recValue.toFixed(1);
            }
          }, 40);
        }"""

js_new_rec = """        // Tasa de Recurrencia
        const recEl = document.getElementById('kpi-rec');
        const recBenchEl = document.getElementById('kpi-rec-bench');
        if (recEl) {
          // Si no hay únicos, devolvemos 0, sino scans/uniques (e.g 58/25 = 2.3)
          const recValue = stats.unique_visitors && stats.unique_visitors > 0 ? (stats.total_scans / stats.unique_visitors) : 0;
          let v = 0;
          const coreRec = stats.core_recurrence ? stats.core_recurrence : 0;
          const iv = setInterval(() => {
            v = Math.min(v + (recValue/30), recValue);
            recEl.childNodes[0].textContent = v.toFixed(1);
            if (v >= recValue) {
              clearInterval(iv);
              recEl.childNodes[0].textContent = recValue.toFixed(1);
              if(recBenchEl) recBenchEl.innerHTML = `<span style="color:var(--accent);">Core: ${coreRec}x</span>`;
            }
          }, 40);
        }"""

html = html.replace(js_old_rec, js_new_rec)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
print("Patch successfully applied!")
