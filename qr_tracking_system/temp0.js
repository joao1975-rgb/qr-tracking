
/* ═══════════════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════════════ */
function switchTab(tab, el) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const content = document.getElementById('tab-' + tab);
  if (content) content.classList.add('active');
  el.classList.add('active');
}

function setRange(btn, range) {
  document.querySelectorAll('.chart-controls .chart-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  updateMainChart(range);
}

function setBenchTab(tab, btn) {
  document.querySelectorAll('#bench-global,#bench-latam,#bench-docs').forEach(el => el.style.display = 'none');
  document.getElementById('bench-' + tab).style.display = 'block';
  document.querySelectorAll('.chart-controls .chart-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function setCompareMode(mode, btn) {
  document.querySelectorAll('.compare-mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  ['prev','bench','select'].forEach(m => {
    const el = document.getElementById('cmp-' + m);
    if (el) el.style.display = m === mode ? (m === 'prev' ? 'grid' : 'block') : 'none';
  });
  if (mode !== 'prev') animateBars();
}

/* ═══════════════════════════════════════════════
   ANIMATED NUMBER COUNTER
═══════════════════════════════════════════════ */
function animateCounter(el, target, duration, decimals = 0, suffix = '') {
  if (!el) return;
  const start = performance.now();
  const easeOutExpo = t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  function update(time) {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easeOutExpo(progress);
    const current = target * eased;
    el.childNodes[0].textContent = decimals > 0
      ? current.toFixed(decimals)
      : Math.floor(current).toLocaleString('es-ES');
    if (progress < 1) requestAnimationFrame(update);
    else el.childNodes[0].textContent = decimals > 0
      ? target.toFixed(decimals)
      : target.toLocaleString('es-ES');
  }
  requestAnimationFrame(update);
}

/* ═══════════════════════════════════════════════
   SPARKLINES (mini charts inside KPI cards)
═══════════════════════════════════════════════ */
function drawSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width = 80;
  const H = canvas.height = 28;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  ctx.clearRect(0, 0, W, H);

  // Gradient fill
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, color + '40');
  grad.addColorStop(1, color + '00');

  const pts = data.map((v, i) => ({
    x: (i / (data.length - 1)) * W,
    y: H - ((v - min) / range) * (H - 4) - 2
  }));

  ctx.beginPath();
  ctx.moveTo(pts[0].x, H);
  pts.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(pts[pts.length-1].x, H);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  pts.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Last dot
  const last = pts[pts.length - 1];
  ctx.beginPath();
  ctx.arc(last.x, last.y, 2.5, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}

/* ═══════════════════════════════════════════════
   MAIN LINE CHART
═══════════════════════════════════════════════ */
let mainChart = null;

const chartData = {
  '7d': {
    labels: ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'],
    scans:  [1840, 2120, 1960, 2380, 3240, 2860, 1980],
    unique: [1380, 1590, 1470, 1780, 2430, 2140, 1490],
    bench:  [1600, 1600, 1600, 1600, 1600, 1600, 1600],
    multiAvg: [3.1, 3.4, 3.2, 3.8, 4.9, 4.3, 3.6]
  },
  '1d': {
    labels: ['00h','03h','06h','09h','12h','15h','18h','21h'],
    scans:  [82, 34, 28, 410, 890, 760, 1240, 820],
    unique: [62, 26, 22, 310, 670, 570, 930, 620],
    bench:  [300, 300, 300, 300, 300, 300, 300, 300],
    multiAvg: [1.8, 1.5, 1.4, 2.6, 3.9, 3.5, 4.2, 3.8]
  },
  '30d': {
    labels: Array.from({length:10}, (_,i) => `D${i*3+1}`),
    scans:  [620, 840, 790, 1120, 1480, 1360, 1820, 2140, 1960, 2380],
    unique: [470, 630, 590, 840, 1110, 1020, 1360, 1600, 1470, 1780],
    bench:  [900,900,900,900,900,900,900,900,900,900],
    multiAvg: [2.4, 2.8, 2.6, 3.1, 3.5, 3.3, 3.7, 4.1, 3.9, 4.2]
  },
  'all': {
    labels: ['Ene','Feb','Mar','Abr','May','Jun'],
    scans:  [8400, 11200, 14600, 18400, 22100, 24731],
    unique: [6300, 8400, 10900, 13800, 16600, 18209],
    bench:  [8000,8000,8000,8000,8000,8000],
    multiAvg: [2.9, 3.2, 3.5, 3.7, 4.0, 4.2]
  }
};

function buildGradient(ctx, color) {
  const grad = ctx.createLinearGradient(0, 0, 0, 200);
  grad.addColorStop(0, color + '30');
  grad.addColorStop(1, color + '00');
  return grad;
}

function createMainChart() {
  const ctx = document.getElementById('mainChart').getContext('2d');
  const d = chartData['7d'];
  mainChart = new Chart(ctx, {
    type: 'bar',          // base type; lines override per-dataset
    data: {
      labels: d.labels,
      datasets: [
        // DATASET 0 — Avg multi-scan BARS (secondary LEFT axis)
        {
          type: 'bar',
          label: 'Avg multi-scan',
          data: d.multiAvg,
          backgroundColor: 'rgba(168,85,247,0.22)',
          borderColor: 'rgba(168,85,247,0.55)',
          borderWidth: 1,
          borderRadius: 3,
          yAxisID: 'yLeft',
          order: 2,
        },
        // DATASET 1 — Total scans line (primary RIGHT axis)
        {
          type: 'line',
          label: 'Escaneos',
          data: d.scans,
          borderColor: '#00CFFF',
          backgroundColor: buildGradient(ctx, '#00CFFF'),
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#00CFFF',
          tension: 0.4,
          fill: true,
          yAxisID: 'yRight',
          order: 1,
        },
        // DATASET 2 — Unique line (primary RIGHT axis)
        {
          type: 'line',
          label: 'Únicos',
          data: d.unique,
          borderColor: '#00E5A0',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          pointRadius: 2,
          pointBackgroundColor: '#00E5A0',
          tension: 0.4,
          yAxisID: 'yRight',
          order: 1,
        },
        // DATASET 3 — Benchmark dashed line (primary RIGHT axis)
        {
          type: 'line',
          label: 'Benchmark',
          data: d.bench,
          borderColor: 'rgba(255,173,51,0.5)',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 4],
          pointRadius: 0,
          tension: 0,
          yAxisID: 'yRight',
          order: 1,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#131B2A',
          borderColor: 'rgba(0,207,255,0.2)',
          borderWidth: 1,
          titleColor: 'rgba(255,255,255,0.9)',
          bodyColor: 'rgba(255,255,255,0.6)',
          titleFont: { family: "'JetBrains Mono', monospace", size: 11 },
          bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
          callbacks: {
            label: ctx => {
              if (ctx.dataset.label === 'Avg multi-scan')
                return `  ◈ Avg multi-scan: ${ctx.parsed.y.toFixed(1)}x`;
              return `  ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('es-ES')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
          ticks: { color: 'rgba(255,255,255,0.30)', font: { family: "'JetBrains Mono', monospace", size: 10 } },
          border: { display: false }
        },
        // LEFT Y-axis — for avg multi-scan bars
        yLeft: {
          position: 'left',
          grid: { color: 'rgba(168,85,247,0.06)', drawBorder: false },
          ticks: {
            color: 'rgba(168,85,247,0.55)',
            font: { family: "'JetBrains Mono', monospace", size: 9 },
            callback: v => v.toFixed(1) + 'x',
            maxTicksLimit: 5,
          },
          border: { display: false },
          title: {
            display: true,
            text: 'avg scans/retornante',
            color: 'rgba(168,85,247,0.45)',
            font: { family: "'JetBrains Mono', monospace", size: 9 },
          }
        },
        // RIGHT Y-axis — for scan volume lines
        yRight: {
          position: 'right',
          grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
          ticks: {
            color: 'rgba(255,255,255,0.30)',
            font: { family: "'JetBrains Mono', monospace", size: 10 },
            callback: v => v >= 1000 ? (v/1000).toFixed(1)+'K' : v
          },
          border: { display: false }
        }
      }
    }
  });
}

function updateMainChart(range) {
  if (!mainChart) return;
  const d = chartData[range] || chartData['7d'];
  mainChart.data.labels = d.labels;
  mainChart.data.datasets[0].data = d.multiAvg;  // bars: avg multi-scan (LEFT axis)
  mainChart.data.datasets[1].data = d.scans;      // line: total (RIGHT axis)
  mainChart.data.datasets[2].data = d.unique;     // line: unique (RIGHT axis)
  mainChart.data.datasets[3].data = d.bench;      // line: benchmark (RIGHT axis)
  mainChart.update('active');
}

/* ═══════════════════════════════════════════════
   DONUT CHART
═══════════════════════════════════════════════ */
function createDonut() {
  const ctx = document.getElementById('donutChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: window.sysData ? window.sysData.map(d => d.count) : [44, 29, 27],
        backgroundColor: ['#00CFFF', '#00E5A0', '#A855F7', '#FFAD33', 'rgba(255,255,255,0.12)'],
        labels: window.sysData ? window.sysData.map(d => d.operating_system) : ['OS A','OS B','OS C'],
        borderColor: '#0C1018',
        borderWidth: 3,
        hoverBorderWidth: 3,
      }]
    },
    options: {
      responsive: false,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: {
        backgroundColor: '#131B2A',
        borderColor: 'rgba(0,207,255,0.2)',
        borderWidth: 1,
        bodyColor: 'rgba(255,255,255,0.8)',
        bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
        callbacks: { label: ctx => `  ${ctx.label}: ${ctx.parsed}%` }
      }},
      animation: { animateRotate: true, duration: 1200 }
    }
  });
}

/* ═══════════════════════════════════════════════
   HEATMAP
═══════════════════════════════════════════════ */
const heatData = [
  [0.1, 0.2, 0.15, 0.25, 0.35, 0.55, 0.30],
  [0.3, 0.5, 0.45, 0.70, 0.80, 0.60, 0.35],
  [0.5, 0.8, 0.75, 1.00, 0.90, 0.65, 0.40],
  [0.4, 0.7, 0.65, 0.85, 0.75, 0.55, 0.30],
  [0.3, 0.5, 0.55, 0.65, 0.70, 0.85, 0.60],
  [0.2, 0.3, 0.35, 0.45, 0.55, 0.90, 0.70],
];
const heatLabels = ['00–05h','07–09h','10–12h','12–15h','15–18h','18–22h'];
const dayLabels  = ['','L','M','X','J','V','S','D'];

function buildHeatmap() {
  const container = document.getElementById('heatmapContainer');
  if (!container) return;
  // Day row
  const dayRow = document.createElement('div');
  dayRow.className = 'heatmap-days';
  dayLabels.forEach(d => {
    const lbl = document.createElement('div');
    lbl.className = 'hm-day-label';
    lbl.textContent = d;
    dayRow.appendChild(lbl);
  });
  container.appendChild(dayRow);

  // Grid
  const grid = document.createElement('div');
  grid.className = 'heatmap-grid';
  heatData.forEach((row, ri) => {
    const tl = document.createElement('div');
    tl.className = 'hm-time-label';
    tl.textContent = heatLabels[ri];
    grid.appendChild(tl);

    row.forEach((v, ci) => {
      const cell = document.createElement('div');
      cell.className = 'hm-cell';
      
      // Thermal Gradient Calculation
      let bgColor;
      if (v >= 0.85) {
        bgColor = `rgba(255, 30, 30, ${v})`;     // Rojo intenso
      } else if (v >= 0.60) {
        bgColor = `rgba(255, 120, 0, ${v})`;    // Naranja
      } else if (v >= 0.35) {
        bgColor = `rgba(255, 210, 0, ${v + 0.1})`;  // Amarillo
      } else {
        bgColor = `rgba(255, 255, 255, ${Math.max(0.06, v + 0.2)})`; // Blanco translúcido
      }
      
      cell.style.background = bgColor;
      cell.style.animationDelay = `${(ri * 7 + ci) * 20}ms`;
      const hrs = Math.round(v * 320);
      cell.setAttribute('data-tooltip', `${heatLabels[ri]} ${dayLabels[ci+1]} · ${hrs} scans`);
      grid.appendChild(cell);
    });
  });
  container.appendChild(grid);
}

/* ═══════════════════════════════════════════════
   GAUGE ANIMATION
═══════════════════════════════════════════════ */
function animateGauge(arcId, pctId, valId, targetPct, currentVal, maxVal, suffix = '') {
  const arc = document.getElementById(arcId);
  const pctEl = document.getElementById(pctId);
  const valEl = document.getElementById(valId);
  if (!arc) return;
  const circumference = 175.9;
  const offset = circumference - (targetPct / 100) * circumference;
  setTimeout(() => {
    arc.style.strokeDashoffset = offset;
  }, 100);
  // Animate percentage text
  const start = performance.now();
  const ease = t => 1 - Math.pow(2, -10 * t);
  function tick(now) {
    const p = Math.min((now - start) / 1800, 1);
    const e = ease(p);
    if (pctEl) pctEl.textContent = Math.floor(targetPct * e) + '%';
    if (valEl) valEl.textContent = suffix
      ? (currentVal * e).toFixed(2) + suffix
      : Math.floor(currentVal * e).toLocaleString('es-ES');
    if (p < 1) requestAnimationFrame(tick);
    else {
      if (pctEl) pctEl.textContent = targetPct + '%';
      if (valEl) valEl.textContent = suffix
        ? currentVal.toFixed(2) + suffix
        : currentVal.toLocaleString('es-ES');
    }
  }
  requestAnimationFrame(tick);
}

/* ═══════════════════════════════════════════════
   ANIMATE PROGRESS BARS
═══════════════════════════════════════════════ */
function animateBars() {
  document.querySelectorAll('.kpi-progress-fill').forEach(el => {
    const pct = el.dataset.pct || 0;
    setTimeout(() => el.style.width = pct + '%', 200);
  });
  document.querySelectorAll('.compare-bar-fill').forEach(el => {
    const pct = el.dataset.pct || 0;
    setTimeout(() => el.style.width = pct + '%', 300);
  });
  document.querySelectorAll('.signal-bar-fill').forEach((el, i) => {
    const pct = el.dataset.pct || 0;
    const vals = ['63','52','48','61','29'];
    setTimeout(() => {
      el.style.width = pct + '%';
      const sigEl = document.getElementById('sig' + (i+1));
      if (sigEl) sigEl.textContent = pct + '%';
    }, 400 + i * 80);
  });
}

/* ═══════════════════════════════════════════════
   SEGMENT PERCENTAGE ANIMATION
═══════════════════════════════════════════════ */
function animateSegments() {
  const segs = [{id:'seg1-pct',val:38},{id:'seg2-pct',val:24},{id:'seg3-pct',val:21},{id:'seg4-pct',val:17}];
  segs.forEach((s, i) => {
    const el = document.getElementById(s.id);
    if (!el) return;
    let current = 0;
    const step = s.val / 30;
    setTimeout(() => {
      const interval = setInterval(() => {
        current = Math.min(current + step, s.val);
        el.textContent = Math.floor(current) + '%';
        if (current >= s.val) clearInterval(interval);
      }, 33);
    }, 600 + i * 100);
  });
}

/* ═══════════════════════════════════════════════
   BENCHMARK NEEDLES ANIMATION
═══════════════════════════════════════════════ */
function animateBenchmarks() {
  // CTR: 2.76% on scale 0.5-4.5+ → roughly at 56%
  setTimeout(() => {
    const bm1 = document.getElementById('bm1-needle');
    if (bm1) bm1.style.left = '56%';
    const bm1v = document.getElementById('bm1-val');
    if (bm1v) bm1v.textContent = '2.76%';
  }, 800);
  // Duration: 62s on scale 15-100+ → roughly at 55%
  setTimeout(() => {
    const bm2 = document.getElementById('bm2-needle');
    if (bm2) bm2.style.left = '55%';
    const bm2v = document.getElementById('bm2-val');
    if (bm2v) bm2v.textContent = '62s';
  }, 1000);
  // Unique ratio: 73.6% on scale 40-90 → roughly at 67%
  setTimeout(() => {
    const bm3 = document.getElementById('bm3-needle');
    if (bm3) bm3.style.left = '67%';
    const bm3v = document.getElementById('bm3-val');
    if (bm3v) bm3v.textContent = '73.6%';
  }, 1200);
  // Recurrence: 4.2x on scale 1-6+ → roughly at 65%
  setTimeout(() => {
    const bm4 = document.getElementById('bm4-needle');
    if (bm4) bm4.style.left = '65%';
    const bm4v = document.getElementById('bm4-val');
    if (bm4v) bm4v.textContent = '4.2x';
  }, 1400);

  // NSE
  setTimeout(() => {
    const nse = document.getElementById('nse-pct');
    if (nse) {
      let v = 0;
      const iv = setInterval(() => {
        v = Math.min(v + 2, 67);
        nse.textContent = v;
        if (v >= 67) clearInterval(iv);
      }, 30);
    }
  }, 1000);
}

/* ═══════════════════════════════════════════════
   LIVE DATA FLOW STREAM
═══════════════════════════════════════════════ */
async function loadLiveScans() {
  try {
    const res = await fetch('/api/scans?limit=60');
    const data = await res.json();
    const tbody = document.getElementById('scansTableBody');
    const lastUp = document.getElementById('lastUpdate');
    
    if (data.success && data.scans.length > 0) {
      tbody.innerHTML = data.scans.map((scan, index) => {
        const date = new Date(scan.scan_timestamp);
        const timeStr = date.toLocaleTimeString('es-ES', {hour: '2-digit', minute:'2-digit', second:'2-digit'});
        const fullDate = date.toLocaleDateString('es-ES', {weekday: 'long', day: '2-digit', month: 'long', year: 'numeric'});
        const dur = scan.duration_seconds || 0;
        const durStr = dur < 60 ? dur.toFixed(1) + 's' : (dur/60).toFixed(1) + 'm';
        
        let connectionIcon = '📶';
        let connectionType = scan.connection_type || 'No detectado';
        if (connectionType.toLowerCase().includes('4g') || connectionType.toLowerCase().includes('3g')) connectionIcon = '📱';
        
        let ispDisplay = scan.isp_carrier || 'No detectado';
        if (ispDisplay.includes('Digitel')) ispDisplay = '<span style="color:#00E5A0;">📱 Digitel</span>';
        else if (ispDisplay.includes('Movistar')) ispDisplay = '<span style="color:#00CFFF;">📱 Movistar</span>';
        else if (ispDisplay.includes('Movilnet')) ispDisplay = '<span style="color:#FFAD33;">📱 Movilnet</span>';

        return `
        <tr class="scan-row" onclick="toggleScanDetail(${index})" title="Clic para ver fingerprint detalledes" style="border-bottom: 1px solid var(--border); transition: background 0.2s;">
            <td style="padding:12px 16px;font-family:var(--mono);">
                <span style="color:var(--text);">${date.toLocaleDateString('es-ES')}</span><br>
                <span style="color:var(--text-3);font-size:10px;">${timeStr}</span>
            </td>
            <td style="padding:12px 16px;color:var(--accent);font-weight:600;">${scan.campaign_code || '-'}</td>
            <td style="padding:12px 16px;">${scan.client || '-'}</td>
            <td style="padding:12px 16px;">
                <span style="color:var(--text);">${scan.device_name || scan.device_id || '-'}</span><br>
                <span style="color:var(--text-3);font-size:10px;">${scan.venue || '-'}</span>
            </td>
            <td style="padding:12px 16px;font-family:var(--mono);">${scan.device_brand || scan.ua_brand || '-'}</td>
            <td style="padding:12px 16px;">
                <span style="color:var(--text);">${scan.operating_system || '-'}</span><br>
                <span style="color:var(--text-3);font-size:10px;">${connectionType}</span>
            </td>
            <td style="padding:12px 16px;font-family:var(--mono);color:var(--green);">${durStr}</td>
            <td style="padding:12px 16px;">
                ${scan.redirect_completed ? '<span style="color:#00E5A0;font-weight:600;">SÍ</span>' : '<span style="color:var(--amber);font-weight:600;">NO</span>'}
            </td>
        </tr>
        <tr class="scan-detail" id="scan-detail-${index}">
            <td colspan="8" style="padding:0; border-bottom:1px solid var(--border);">
                <div class="scan-detail-content">
                    <div class="detail-item">
                        <div class="detail-label">🕐 Fecha y Hora</div>
                        <div class="detail-value">${fullDate}<br>${timeStr}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">📍 Ubicación DOOH</div>
                        <div class="detail-value">${scan.location || '-'}<br>${scan.venue || '-'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🏭 Marca / Modelo</div>
                        <div class="detail-value">${scan.device_brand || scan.ua_brand || '-'}<br>${scan.ua_model || scan.device_model || '-'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">💻 OS</div>
                        <div class="detail-value">${scan.operating_system || '-'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">${connectionIcon} Tipo Conexión</div>
                        <div class="detail-value">${connectionType}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">📡 Operadora / ISP</div>
                        <div class="detail-value">${ispDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🌐 Dirección IP</div>
                        <div class="detail-value" style="font-family:var(--mono);">${scan.ip_address || '-'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🔐 Fingerprint</div>
                        <div class="detail-value" style="font-family:var(--mono); font-size:11px;">${scan.device_fingerprint || '-'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">⚙️ Hardware</div>
                        <div class="detail-value">${scan.cpu_cores ? scan.cpu_cores + ' cores' : '-'}${scan.device_memory ? ' • ' + scan.device_memory + 'GB RAM' : ''}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🔋 Estado de Batería</div>
                        <div class="detail-value">${scan.battery_level !== null ? scan.battery_level + '%' : '-'}${scan.battery_charging ? ' ⚡' : ''}</div>
                    </div>
                </div>
            </td>
        </tr>
        `;
      }).join('');
      if (lastUp) {
        lastUp.textContent = "Última sincronización: " + new Date().toLocaleTimeString('es-ES');
      }
    } else {
      tbody.innerHTML = '<tr><td colspan="8" style="padding:24px;text-align:center;color:var(--text-3);">Sin escaneos recientes...</td></tr>';
    }
  } catch (e) {
    console.error("Error fetching live stream:", e);
  }
}

function toggleScanDetail(index) {
  const row = document.querySelector(`tr.scan-row:nth-child(${index * 2 + 1})`);
  const detailRow = document.getElementById(`scan-detail-${index}`);

  if (detailRow) {
      const isExpanded = detailRow.classList.contains('show');
      
      // Contraer otras
      document.querySelectorAll('tr.scan-detail.show').forEach(tr => tr.classList.remove('show'));
      document.querySelectorAll('tr.scan-row.expanded').forEach(tr => tr.classList.remove('expanded'));

      // Abrir la seleccionada
      if (!isExpanded) {
          detailRow.classList.add('show');
          row.classList.add('expanded');
      }
  }
}

/* ═══════════════════════════════════════════════
   MAIN INIT — IntersectionObserver for entry
═══════════════════════════════════════════════ */
let chartsConfigured = false;
document.addEventListener('DOMContentLoaded', () => {
  loadLiveScans();
  setInterval(loadLiveScans, 15000);
  loadLiveStats();

  const sparkData = { total: [0,0], unique: [0,0] };
  // Sparklines will be drawn when loadLiveStats injects them

  // Real Data KPI Stats Animation
  async function loadLiveStats() {
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
         
         // Build dynamic Audiences and Signals based on real OS strings
         let iosCount = 0; let androidCount = 0; let otherCount = 0;
         if(window.sysData) {
             window.sysData.forEach(d => {
                 let os = d.operating_system.toLowerCase();
                 if(os.includes("ios") || os.includes("mac")) iosCount += d.count;
                 else if(os.includes("android")) androidCount += d.count;
                 else otherCount += d.count;
             });
         }
         let totalSys = iosCount + androidCount + otherCount;
         let iosPct = totalSys > 0 ? ((iosCount / totalSys)*100).toFixed(0) : 0;
         let andPct = totalSys > 0 ? ((androidCount / totalSys)*100).toFixed(0) : 0;
         
         const segContainer = document.getElementById("dynamic-segments");
         if(segContainer && totalSys > 0) {
             segContainer.innerHTML = ''; // clear mock
             if(iosCount > 0) {
                 segContainer.innerHTML += `
                 <div class="segment-item" style="--seg-color:#00CFFF;--seg-bg:rgba(0,207,255,0.08);">
                    <div class="segment-avatar">A1</div>
                    <div class="segment-info">
                        <div class="segment-name">Perfil Entusiasta / Premium</div>
                        <div class="segment-detail">Ecosistema Apple detectado</div>
                    </div>
                    <div class="segment-pct">${iosPct}%</div>
                 </div>`;
             }
             if(androidCount > 0) {
                 segContainer.innerHTML += `
                 <div class="segment-item" style="--seg-color:#00E5A0;--seg-bg:rgba(0,229,160,0.08);">
                    <div class="segment-avatar">B2</div>
                    <div class="segment-info">
                        <div class="segment-name">Perfil Práctico / Diverso</div>
                        <div class="segment-detail">Ecosistema Android y genéricos</div>
                    </div>
                    <div class="segment-pct">${andPct}%</div>
                 </div>`;
             }
         }
         
         const sigContainer = document.getElementById("dynamic-signals");
         if(sigContainer && totalSys > 0) {
             sigContainer.innerHTML = '';
             if(iosCount > 0) {
                 sigContainer.innerHTML += `
                 <div class="signal-row">
                    <div class="signal-icon" style="--sig-bg:rgba(0,207,255,0.08);">📱</div>
                    <div class="signal-meta">
                        <div class="signal-name">iOS OS Detectado</div>
                        <div class="signal-bar-wrap">
                            <div class="signal-bar-bg"><div class="signal-bar-fill" style="width:${iosPct}%; --sig-color:#00CFFF;"></div></div>
                            <div class="signal-val">${iosPct}%</div>
                        </div>
                    </div>
                 </div>`;
             }
             if(androidCount > 0) {
                 sigContainer.innerHTML += `
                 <div class="signal-row">
                    <div class="signal-icon" style="--sig-bg:rgba(0,229,160,0.08);">📱</div>
                    <div class="signal-meta">
                        <div class="signal-name">Android OS Detectado</div>
                        <div class="signal-bar-wrap">
                            <div class="signal-bar-bg"><div class="signal-bar-fill" style="width:${andPct}%; --sig-color:#00E5A0;"></div></div>
                            <div class="signal-val">${andPct}%</div>
                        </div>
                    </div>
                 </div>`;
             }
         }

         chartsConfigured = true;
      }
      
      if(data.daily_scans && data.daily_scans.length > 0) {
          let sTot=[], sUq=[], sCtr=[], sDur=[];
          data.daily_scans.forEach(d => {
              sTot.push(d.scans); sUq.push(d.unique_scans); 
              let tdur = stats.avg_duration || 0; 
              sCtr.push(stats.ctr || 0); sDur.push(tdur);
          });
          drawSparkline('spark-total',  sTot,  '#00CFFF');
          drawSparkline('spark-unique', sUq, '#00E5A0');
          drawSparkline('spark-ctr',    sCtr,    '#FFAD33');
          drawSparkline('spark-dur',    sDur,    '#A855F7');
      }
        const total = stats.total_scans || 0;
        const unique = stats.unique_visitors || 0;
        const duration = stats.avg_duration || 0;
        const redirects = stats.completed_redirects || 0;
        const ctr = total > 0 ? (redirects / total) * 100 : 0;
        
        // Populate core numbers
        animateCounter(document.getElementById('kpi-total'), total, 2000, 0);
        
        // Populate Targets explicitly from backend DB target goals
        let targetTotal = data.targets ? data.targets.target_scans : 100;
        let targetUnique = data.targets ? data.targets.target_unique_visitors : 50;
        let targetCtr = data.targets ? data.targets.target_ctr_pct : 2.5;
        
        document.getElementById('pg-tot-ui').textContent = total;
        document.getElementById('pg-tot-target').textContent = `Meta: ${targetTotal}`;
        document.querySelector('#pg-tot-ui').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((total/targetTotal)*100, 100) + '%';
        
        document.getElementById('pg-uq-ui').textContent = unique;
        document.getElementById('pg-uq-target').textContent = `Alcanzados: ${targetUnique}`;
        document.querySelector('#pg-uq-ui').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((unique/targetUnique)*100, 100) + '%';
        
        document.getElementById('pg-ctr-ui').textContent = ctr.toFixed(1) + '%';
        document.getElementById('pg-ctr-target').textContent = `Objetivo: ${targetCtr}%`;
        document.querySelector('#pg-ctr-ui').nextElementSibling.nextElementSibling.querySelector('div').style.width = Math.min((ctr/targetCtr)*100, 100) + '%';

        animateCounter(document.getElementById('kpi-unique'), unique, 2000, 0);
        
        // Breakdown logic (single vs multi)
        const single = stats.single_scanners !== undefined ? stats.single_scanners : 0;
        const multi  = stats.multi_scanners !== undefined ? stats.multi_scanners : 0;
        animateCounter(document.getElementById('kpi-single'), single, 1800, 0);
        animateCounter(document.getElementById('kpi-multi'), multi, 1800, 0);
        
        const spEl = document.getElementById('kpi-single-pct');
        const mpEl = document.getElementById('kpi-multi-pct');
        if (spEl) spEl.textContent = unique > 0 ? `${Math.round((single/unique)*100)}% de únicos` : '0% de únicos';
        if (mpEl) mpEl.textContent = unique > 0 ? `${Math.round((multi/unique)*100)}% · retornaron` : '0% retornaron';
        
        // CTR and Averages
        const avgMult = stats.core_recurrence ? stats.core_recurrence : 0;
        
        // CTR
        const ctrEl = document.getElementById('kpi-ctr');
        if (ctrEl) {
          let v = 0;
          const iv = setInterval(() => {
            v = Math.min(v + (ctr/30), ctr);
            ctrEl.childNodes[0].textContent = v.toFixed(2);
            if (v >= ctr) clearInterval(iv);
          }, 40);
        }
        
        // Duration
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
        }
        
        // Average Scans per Returner vs Benchmark
        const avgEl = document.getElementById('kpi-avg-multi');
        const avgDeltaEl = document.getElementById('kpi-avg-delta');
        if (avgEl) {
          let v = 0;
          const iv = setInterval(() => {
            v = Math.min(v + (avgMult/30), avgMult);
            avgEl.textContent = v.toFixed(1) + 'x';
            if (v >= avgMult) { 
                clearInterval(iv); 
                avgEl.textContent = avgMult.toFixed(1) + 'x'; 
                if (avgDeltaEl && avgMult > 0) {
                     const diff = ((avgMult - 3.8) / 3.8) * 100;
                     avgDeltaEl.textContent = (diff > 0 ? '▲ ' : '▼ ') + Math.abs(diff).toFixed(1) + '%';
                     avgDeltaEl.className = 'kpi-delta ' + (diff > 0 ? 'up' : 'down');
                }
            }
          }, 40);
        }
        
        // --- Inteligencia DOOH Inferior ---

        // Índice Audiencia Premium (IAP) - Porcentaje de iOS
        const iapValue = stats.ios_pct ? Math.round(Number(stats.ios_pct)) : 0;
        animateCounter(document.getElementById('kpi-iap'), iapValue, 1600, 0);

        // Tasa de Recurrencia
        const recEl = document.getElementById('kpi-rec');
        const recBenchEl = document.getElementById('kpi-rec-bench');
        if (recEl) {
          // Si no hay únicos, devolvemos 0, sino scans/uniques (e.g 58/25 = 2.3)
          const recValue = stats.unique_visitors && stats.unique_visitors > 0 ? (stats.total_scans / stats.unique_visitors) : 0;
          let vRec = 0;
          const coreRec = stats.core_recurrence ? stats.core_recurrence : 0;
          const ivRec = setInterval(() => {
            vRec = Math.min(vRec + (recValue/30), recValue);
            recEl.childNodes[0].textContent = vRec.toFixed(1);
            if (vRec >= recValue) {
               clearInterval(ivRec);
               recEl.childNodes[0].textContent = recValue.toFixed(1);
               if(recBenchEl) recBenchEl.innerHTML = `<span style="color:var(--accent); font-weight:600;">Core Multiscan: ${coreRec}x</span>`;
            }
          }, 40);
        }

        // Impactos DOOH Estimados (Reach)
        const reachEl = document.getElementById('kpi-reach');
        if (reachEl) {
          const uqParams = stats.unique_visitors || 0;
          const totalReach = Math.round(uqParams * 85); // Factor demográfico CTR ~1.1%
          
          if (totalReach > 1000) {
             animateCounter(reachEl, totalReach/1000, 1800, 1);
             reachEl.querySelector('.unit').textContent = 'K';
          } else {
             animateCounter(reachEl, totalReach, 1800, 0);
             reachEl.querySelector('.unit').textContent = '';
          }
        }

        // Data Completeness Score (AIS)
        // Puntaje de salud de metadata, logarítmico sobre muestra
        const samples = stats.unique_visitors || 0;
        const baseScore = samples === 0 ? 0 : 40;
        const addScore = Math.min(60, samples * 1.5);
        const aisValue = Math.round(baseScore + addScore);
        
        animateCounter(document.getElementById('kpi-ais'), aisValue, 1600, 0);
      }
    } catch (e) {
      console.warn("Could not fetch KPI stats");
    }
  }
  
  // Initialize Stats
  loadLiveStats();
  // Progress bars
  setTimeout(animateBars, 600);

  // Gauges
  setTimeout(() => {
    animateGauge('gauge1-arc', 'gauge1-pct', 'gauge1-val', 82, 12309, 15000);
    animateGauge('gauge2-arc', 'gauge2-pct', 'gauge2-val', 90, 8980, 10000);
    animateGauge('gauge3-arc', 'gauge3-pct', 'gauge3-val', 79, 2.76, 3.5, '%');
  }, 500);

  // Segments
  animateSegments();

  // Benchmarks
  animateBenchmarks();
});
