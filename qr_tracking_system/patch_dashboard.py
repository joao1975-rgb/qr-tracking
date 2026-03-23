import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Insert HTML Comparative Analytics Section
html_section = """
        <!-- Fifth Row: Advanced Comparative Analytics -->
        <div class="content-grid" style="margin-top: 24px;">
            <div class="card" style="grid-column: 1 / -1; border-top: 4px solid var(--accent-primary);">
                <div class="card-header">
                    <h2 class="card-title">🔬 Análisis Comparativo Avanzado</h2>
                </div>
                <div class="card-body">
                    <div class="filters-row" style="margin-bottom: 20px;">
                        <div class="filter-group">
                            <label class="filter-label">Campaña a Analizar</label>
                            <select class="filter-select" id="compareSourceCampaign" onchange="loadComparativeData()">
                                <option value="">Seleccione una campaña...</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label class="filter-label">Comparar Contra</label>
                            <select class="filter-select" id="compareTargetOption" onchange="loadComparativeData()">
                                <option value="benchmark">Promedio de la Industria (Benchmarks)</option>
                                <option value="previous">Campaña Histórica (Mismo Cliente)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div id="comparativeResults" style="display: none; padding-top: 15px; border-top: 1px solid var(--border-color);">
                        <h3 id="comparativeSubtitle" style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 15px;">Comparando...</h3>
                        <div class="stats-grid" id="comparativeDeltasGrid">
                            <!-- JS injected Deltas -->
                        </div>
                    </div>
                    
                    <div id="comparativeLoading" style="display: none; padding: 20px; text-align: center;">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
            </div>
        </div>
"""

# Insert right before the last closing div of the main dashboard div
html = html.replace('<!-- Fourth Row: Client Reports Section -->', html_section + '\n\n        <!-- Fourth Row: Client Reports Section -->')

# 2. Insert JavaScript functions
js_logic = """
        // =============================================
        // COMPARATIVE ANALYTICS
        // =============================================
        async function loadComparativeData() {
            const cmpSource = document.getElementById('compareSourceCampaign').value;
            const cmpTarget = document.getElementById('compareTargetOption').value;
            const resultsDiv = document.getElementById('comparativeResults');
            const loadDiv = document.getElementById('comparativeLoading');

            if (!cmpSource) {
                resultsDiv.style.display = 'none';
                return;
            }

            resultsDiv.style.display = 'none';
            loadDiv.style.display = 'block';

            try {
                const endpoint = cmpTarget === 'benchmark' ? `/analytics/compare/vs-benchmark/${cmpSource}` : `/analytics/compare/vs-previous/${cmpSource}`;
                const response = await fetch(`${API_BASE}${endpoint}`);
                
                const data = await response.json();
                loadDiv.style.display = 'none';
                
                if (data.status === 'no_previous' || data.status === 'no_benchmark') {
                    document.getElementById('comparativeSubtitle').innerHTML = `⚠️ ${data.message}`;
                    document.getElementById('comparativeDeltasGrid').innerHTML = "";
                    resultsDiv.style.display = 'block';
                    return;
                }

                let subtitle = "";
                if (cmpTarget === 'benchmark') {
                    subtitle = `Comparado vs Mejor Campaña de Industria (${data.benchmark_best?.campaign_type || 'N/A'})`;
                } else {
                    subtitle = `Comparado vs ${data.previous?.campaign_type || 'N/A'} (Anterior del cliente)`;
                }
                document.getElementById('comparativeSubtitle').textContent = subtitle;

                const grid = document.getElementById('comparativeDeltasGrid');
                grid.innerHTML = "";
                
                const makeCard = (label, delta) => {
                    const d = delta || 0;
                    const isPos = d >= 0;
                    const color = isPos ? 'var(--success)' : 'var(--danger)';
                    const sign = isPos ? '+' : '';
                    return `\\n                    <div class="stat-card" style="border-left: 3px solid ${color}">\\n                        <div class="stat-label">${label} Diferencia</div>\\n                        <div class="stat-value" style="color: ${color}; font-size: 1.8rem;">${sign}${d}%</div>\\n                    </div>`;
                };

                const deltas = data.deltas || data.deltas_vs_best || {};
                grid.innerHTML += makeCard("Total Escaneos", deltas.scans_delta_pct);
                grid.innerHTML += makeCard("Usuarios Únicos", deltas.unique_delta_pct !== undefined ? deltas.unique_delta_pct : deltas.scans_delta_pct);
                grid.innerHTML += makeCard("Duración Promedio", deltas.duration_delta_pct);

                resultsDiv.style.display = 'block';

            } catch (error) {
                console.error(error);
                loadDiv.style.display = 'none';
                document.getElementById('comparativeSubtitle').textContent = "⚠️ Ocurrió un error consultando los benchmarks para esta campaña.";
                document.getElementById('comparativeDeltasGrid').innerHTML = "";
                resultsDiv.style.display = 'block';
            }
        }
"""

html = html.replace('async function loadFilters() {', js_logic + '\n        async function loadFilters() {')


# 3. Inject drop-down population inside loadFilters data loop
dropdown_injector = """
                const cmpSelect = document.getElementById('compareSourceCampaign');
                if (cmpSelect) {
                    cmpSelect.innerHTML = '<option value="">Seleccione campaña a analizar...</option>';
                    data.campaigns.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.code || c.campaign_code;
                        opt.textContent = `${c.code || c.campaign_code}`;
                        cmpSelect.appendChild(opt);
                    });
                }
"""

# Find place in loadFilters
html = re.sub(
    r"(const campaignSelect = document\.getElementById\('filterCampaign'\);.*?data\.campaigns\.forEach.*?\}\);)",
    r"\1" + dropdown_injector,
    html,
    flags=re.DOTALL
)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
