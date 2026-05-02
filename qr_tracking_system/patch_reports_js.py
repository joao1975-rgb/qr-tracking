import re

with open('templates/reports.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the call
content = content.replace("updateScansTable();", "updateCampaignsBreakdown();")

# The block to remove starts exactly at:
#         // =============================================
#         // FUNCIONES DE ORDENAMIENTO Y FILTRADO DE TABLA
#         // =============================================
# and ends right before:
#         // =============================================
#         // FUNCIÓN PARA COLORES DE MARCA
#         // =============================================

pattern = re.compile(
    r"// =============================================\s*// FUNCIONES DE ORDENAMIENTO Y FILTRADO DE TABLA.*?// =============================================\s*// FUNCIÓN PARA COLORES DE MARCA", 
    re.DOTALL
)

new_code = """// =============================================
        // DESGLOSE POR CAMPAÑAS (NEURODISEÑO)
        // =============================================

        function updateCampaignsBreakdown() {
            const container = document.getElementById('campaignsBreakdownContainer');
            const campaigns = reportData.campaigns || [];
            const allScans = reportData.client_scans || [];

            if (campaigns.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🎯</div>
                        <h3>Sin campañas registradas</h3>
                    </div>
                `;
                return;
            }

            let html = '';

            // Renderizamos una tarjeta detallada por cada campaña
            campaigns.forEach(campaign => {
                const campScans = allScans.filter(s => s.campaign_code === campaign.campaign_code);
                const convRate = campaign.scans > 0 ? Math.round((campaign.completions / campaign.scans) * 100) : 0;
                
                // Extraer el top DOOH
                let doohCounts = {};
                campScans.forEach(s => {
                    const name = s.device_name || s.device_id || 'Desconocido';
                    doohCounts[name] = (doohCounts[name] || 0) + 1;
                });
                const topDooh = Object.keys(doohCounts).sort((a,b) => doohCounts[b] - doohCounts[a]).slice(0,3);

                html += `
                    <div style="border: 1px solid var(--border-color); border-radius: 16px; overflow: hidden; background: #fff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                        <!-- Header Campaña -->
                        <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 20px 24px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                            <div>
                                <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                                    ${campaign.active ? '🟢' : '⚪'} ${campaign.campaign_code}
                                </h3>
                                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px; max-width: 500px;">
                                    ${campaign.description || 'Sin descripción'}
                                </p>
                                <a href="${campaign.destination}" target="_blank" style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.85rem; color: var(--accent-primary); text-decoration: none; margin-top: 8px;">
                                    🔗 Link de Destino
                                </a>
                            </div>
                            <!-- KPIs Campaña -->
                            <div style="display: flex; gap: 16px;">
                                <div style="background: #fff; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); text-align: center; min-width: 100px;">
                                    <div style="font-size: 1.5rem; font-weight: 800; color: var(--primary);">${campaign.scans}</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Escaneos</div>
                                </div>
                                <div style="background: #fff; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); text-align: center; min-width: 100px;">
                                    <div style="font-size: 1.5rem; font-weight: 800; color: ${convRate >= 50 ? 'var(--success)' : 'var(--warning)'};">${convRate}%</div>
                                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Conversión</div>
                                </div>
                            </div>
                        </div>

                        <!-- Panel de Datos -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
                            
                            <!-- Perfil de Audiencia (OS/Marcas) -->
                            <div style="padding: 20px 24px; border-right: 1px solid var(--border-color);">
                                <h4 style="font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px;">👥 Perfil de Audiencia</h4>
                                <div style="display: flex; flex-direction: column; gap: 12px;">
                                    ${ renderCampDevices(campScans) }
                                </div>
                            </div>

                            <!-- Distribución Física (DOOH/Venues) -->
                            <div style="padding: 20px 24px; border-right: 1px solid var(--border-color);">
                                <h4 style="font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px;">📍 Principales DOOH</h4>
                                ${topDooh.length > 0 ? topDooh.map(d => `<div style="padding: 8px 12px; background: var(--bg-secondary); border-radius: 6px; font-size: 0.85rem; font-weight: 500; margin-bottom: 8px;">🖥️ ${d}</div>`).join('') : '<span style="color:var(--text-muted); font-size:0.85rem;">No hay datos DOOH</span>'}
                            </div>

                            <!-- Resumen de Escaneos (mini tabla) -->
                            <div style="padding: 20px 24px;">
                                <h4 style="font-size: 0.95rem; color: var(--text-secondary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px;">⏱️ Últimas interacciones</h4>
                                <div style="font-size: 0.8rem; display: flex; flex-direction: column; gap: 8px;">
                                    ${campScans.slice(0,4).map(s => {
                                        const d = new Date(s.scan_timestamp);
                                        return `<div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--bg-secondary); padding-bottom: 4px;">
                                            <span style="color: var(--text-muted);">${d.getDate()}/${d.getMonth()+1} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}</span>
                                            <span style="font-weight: 500; color: ${s.redirect_completed ? 'var(--success)' : 'var(--text-primary)'}">${s.user_device_type || 'Desconocido'}</span>
                                        </div>`;
                                    }).join('')}
                                    ${campScans.length > 4 ? `<div style="text-align:center; color: var(--text-muted); font-size: 0.75rem; margin-top: 4px;">y ${campScans.length - 4} más...</div>` : ''}
                                    ${campScans.length === 0 ? '<span style="color:var(--text-muted);">Sin datos</span>' : ''}
                                </div>
                            </div>

                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        function renderCampDevices(scans) {
            if (scans.length === 0) return '<span style="color:var(--text-muted); font-size:0.85rem;">Sin datos de dispositivos</span>';
            
            let counts = { 'Mobile': 0, 'Desktop': 0, 'Tablet': 0 };
            scans.forEach(s => { counts[s.user_device_type || 'Mobile'] = (counts[s.user_device_type || 'Mobile'] || 0) + 1; });
            
            let total = scans.length;
            return Object.keys(counts).filter(k => counts[k] > 0).map(k => {
                let pct = Math.round((counts[k]/total)*100);
                return `
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem;">
                        <span style="display:flex; align-items:center; gap:6px;">${k==='Mobile'?'📱':k==='Desktop'?'💻':'📲'} ${k}</span>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-weight: 600;">${pct}%</span>
                            <div style="width: 60px; height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden;">
                                <div style="height: 100%; width: ${pct}%; background: var(--primary);"></div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // =============================================
        // FUNCIÓN PARA COLORES DE MARCA
"""

content = pattern.sub(new_code, content)

with open('templates/reports.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
