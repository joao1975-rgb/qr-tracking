
        
        // =============================================
        // CONFIGURACIÓN GLOBAL & ADVANCED CHARTS
        // =============================================
        const API_BASE = window.location.origin + '/api';
        let scansChart = null;
        let deviceRadarChart = null;
        let geoMap = null;
        let heatLayer = null;

        let scansChart = null;
        let autoRefreshInterval = null;
        let currentFilters = {
            startDate: null,
            endDate: null,
            campaign: null,
            device: null,
            client: null
        };

        // =============================================
        // INICIALIZACIÓN
        // =============================================
        document.addEventListener('DOMContentLoaded', function () {
            initializeDates();
            initializeChart();
            loadAllData();
            startAutoRefresh();

            console.log('📊 Dashboard QR Tracking System v2.5.1');
            console.log('🔄 Auto-refresh activo cada 30 segundos');
        });

        function initializeDates() {
            const today = new Date();
            const pastDate = new Date(today);
            pastDate.setDate(pastDate.getDate() - 90); // default to 90 days for historical visibility

            document.getElementById('filterEndDate').value = today.toISOString().split('T')[0];
            document.getElementById('filterStartDate').value = pastDate.toISOString().split('T')[0];
        }

        function startAutoRefresh() {
            autoRefreshInterval = setInterval(() => {
                loadScans();
                loadStats();
            }, 30000); // Cada 30 segundos
        }

        // =============================================
        // CARGA DE DATOS
        // =============================================
        async function loadAllData() {
            await Promise.all([
                loadStats(),
                loadScans(),
                loadFilters(),
                loadAnalytics(),
                loadClientReports()
            ]);
        }

        async function refreshAllData() {
            const btn = document.getElementById('refreshBtn');
            btn.classList.add('spinning');

            await loadAllData();

            setTimeout(() => {
                btn.classList.remove('spinning');
            }, 500);
        }

        
        async function loadStats() {
            try {
                const response = await fetch(`${API_BASE}/analytics/dashboard`);
                const data = await response.json();

                if (data.success) {
                    updateStatsCards(data.stats);
                    updateTopCampaigns(data.campaigns);
                    updateTopPhysicalDevices(data.physical_devices);
                    updateTopVenues(data.venues);
                    loadDeviceHierarchy();
                    updateRadarChart();
                    updateGeoMap(data.physical_devices);
                }
            } catch (error) {
                console.error('Error loading stats:', error);
                showFallbackStats();
            }
        }

        async function updateRadarChart() {
            try {
                const response = await fetch(`${API_BASE}/analytics/device-hierarchy`);
                const data = await response.json();
                if(data.success && deviceRadarChart) {
                    const mobile = data.hierarchy.find(h => h.name === 'Mobile');
                    const desktop = data.hierarchy.find(h => h.name === 'Desktop');
                    
                    let ios = 0, android = 0, windows = 0, mac = 0, other = 0;
                    
                    if(mobile && mobile.brands) {
                        const apple = mobile.brands.find(b => b.name === 'Apple');
                        if (apple) ios = apple.count;
                        // Approximate android as mobile minus apple
                        android = mobile.count - ios;
                    }
                    if(desktop && desktop.brands) {
                        const appleDesk = desktop.brands.find(b => b.name === 'Apple');
                        if (appleDesk) mac = appleDesk.count;
                        windows = desktop.count - mac;
                    }
                    
                    deviceRadarChart.data.datasets[0].data = [ios, android, windows, mac, other];
                    deviceRadarChart.update();
                }
            } catch (e) {}
        }

        function updateGeoMap(devices) {
            if(!geoMap || !devices) return;
            
            // Clear existing markers
            geoMap.eachLayer((layer) => {
                if (layer instanceof L.CircleMarker) {
                    geoMap.removeLayer(layer);
                }
            });

            // Hash fake coordinates for visualization based on venue string to keep them consistent
            devices.forEach(d => {
                const venue = d.venue || d.location || 'Unknown';
                let hash = 0;
                for (let i = 0; i < venue.length; i++) hash = venue.charCodeAt(i) + ((hash << 5) - hash);
                
                // Base around Lat 10, Lng -66 (Venezuela area) with some spread
                const lat = 10.0 + (hash % 1000) / 200.0 - 2.5; 
                const lng = -66.0 + ((hash >> 4) % 1000) / 200.0 - 2.5;
                const size = Math.min(Math.max(d.scans / 10, 5), 30);

                L.circleMarker([lat, lng], {
                    radius: size,
                    fillColor: '#00f0ff',
                    color: '#00f0ff',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.4
                }).addTo(geoMap).bindPopup(`<b>${venue}</b><br>Escaneos: ${d.scans}`);
            });
        }
async function loadScans() {
            try {
                let url = `${API_BASE}/scans?limit=50`;

                if (currentFilters.startDate) {
                    url += `&start_date=${currentFilters.startDate}`;
                }
                if (currentFilters.endDate) {
                    url += `&end_date=${currentFilters.endDate}`;
                }
                if (currentFilters.campaign) {
                    url += `&campaign_code=${currentFilters.campaign}`;
                }
                if (currentFilters.device) {
                    url += `&device_id=${currentFilters.device}`;
                }

                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    renderScansTable(data.scans);
                    updateLastUpdate();
                }
            } catch (error) {
                console.error('Error loading scans:', error);
                renderEmptyScansTable();
            }
        }

        // =============================================
        // COMPARATIVE ANALYTICS
        // =============================================
        async function loadComparativeData() {
            const cmpSource = document.getElementById('compareSourceCampaign')?.value;
            const cmpTarget = document.getElementById('compareTargetOption')?.value;
            const resultsDiv = document.getElementById('comparativeResults');
            const loadDiv = document.getElementById('comparativeLoading');

            if (!cmpSource) {
                if (resultsDiv) resultsDiv.style.display = 'none';
                return;
            }

            if (resultsDiv) resultsDiv.style.display = 'none';
            if (loadDiv) loadDiv.style.display = 'block';

            try {
                const endpoint = cmpTarget === 'benchmark' 
                    ? `/analytics/compare/vs-benchmark/${cmpSource}` 
                    : `/analytics/compare/vs-previous/${cmpSource}`;
                const response = await fetch(`${API_BASE}${endpoint}`);
                const data = await response.json();
                
                if (loadDiv) loadDiv.style.display = 'none';
                
                if (data.status === 'no_previous' || data.status === 'no_benchmark') {
                    document.getElementById('comparativeSubtitle').textContent = `⚠️ ${data.message}`;
                    document.getElementById('comparativeDeltasGrid').innerHTML = "";
                    if (resultsDiv) resultsDiv.style.display = 'block';
                    return;
                }

                let subtitle = "";
                if (cmpTarget === 'benchmark') {
                    subtitle = `Comparado vs Mejor Campaña de Industria (${data.benchmark_best?.campaign_type || 'N/A'})`;
                } else {
                    subtitle = `Comparado vs ${data.previous?.campaign_type || 'N/A'} (Histórico)`;
                }
                document.getElementById('comparativeSubtitle').textContent = subtitle;

                const grid = document.getElementById('comparativeDeltasGrid');
                grid.innerHTML = "";
                
                const makeCard = (label, delta) => {
                    const d = delta || 0;
                    const isPos = d >= 0;
                    const color = isPos ? 'var(--success)' : 'var(--danger)';
                    const sign = isPos ? '+' : '';
                    return `
                    <div class="stat-card" style="border-left: 3px solid ${color}">
                        <div class="stat-label">${label} Diferencia</div>
                        <div class="stat-value" style="color: ${color}; font-size: 1.8rem;">${sign}${d}%</div>
                    </div>`;
                };

                const deltas = data.deltas || data.deltas_vs_best || {};
                const safeFloat = val => val !== null && val !== undefined ? parseFloat(val) : 0;
                
                grid.innerHTML += makeCard("Total Escaneos", safeFloat(deltas.scans_delta_pct));
                grid.innerHTML += makeCard("Usuarios Únicos", safeFloat(deltas.unique_delta_pct !== undefined ? deltas.unique_delta_pct : deltas.scans_delta_pct));
                grid.innerHTML += makeCard("Duración Promedio", safeFloat(deltas.duration_delta_pct));

                if (resultsDiv) resultsDiv.style.display = 'block';

            } catch (error) {
                console.error(error);
                if (loadDiv) loadDiv.style.display = 'none';
                if (resultsDiv) {
                    document.getElementById('comparativeSubtitle').textContent = "⚠️ Error consultando benchmarks.";
                    document.getElementById('comparativeDeltasGrid').innerHTML = "";
                    resultsDiv.style.display = 'block';
                }
            }
        }

        async function loadFilters() {
            try {
                // Cargar campañas
                const campaignsRes = await fetch(`${API_BASE}/campaigns`);
                const campaignsData = await campaignsRes.json();

                if (campaignsData.success) {
                    populateSelect('filterCampaign', campaignsData.campaigns, 'campaign_code', 'campaign_code', 'client');

                    const cmpSelect = document.getElementById('compareSourceCampaign');
                    if (cmpSelect) {
                        cmpSelect.innerHTML = '<option value="">Seleccione campaña a analizar...</option>';
                        campaignsData.campaigns.forEach(c => {
                            const opt = document.createElement('option');
                            opt.value = c.campaign_code;
                            opt.textContent = `${c.campaign_code}`;
                            cmpSelect.appendChild(opt);
                        });
                    }

                    // Extraer clientes únicos
                    const clients = [...new Set(campaignsData.campaigns.map(c => c.client))];
                    populateClientSelect('filterClient', clients);
                }

                // Cargar dispositivos
                const devicesRes = await fetch(`${API_BASE}/devices`);
                const devicesData = await devicesRes.json();

                if (devicesData.success) {
                    populateSelect('filterDevice', devicesData.devices, 'device_id', 'device_name', 'venue');
                }
            } catch (error) {
                console.error('Error loading filters:', error);
            }
        }

        async function loadAnalytics() {
            try {
                const response = await fetch(`${API_BASE}/analytics/dashboard`);
                const data = await response.json();

                if (data.success) {
                    // Cargar gráfico con período seleccionado
                    await updateChart();
                }
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }

        async function loadClientReports() {
            try {
                const response = await fetch(`${API_BASE}/clients`);
                const data = await response.json();

                if (data.success && data.clients) {
                    renderClientReports(data.clients);
                } else {
                    renderEmptyClientReports();
                }
            } catch (error) {
                console.error('Error loading client reports:', error);
                renderEmptyClientReports();
            }
        }

        function renderClientReports(clients) {
            const container = document.getElementById('clientReportsGrid');

            if (!clients || clients.length === 0) {
                renderEmptyClientReports();
                return;
            }

            container.innerHTML = clients.slice(0, 8).map(client => `
                <div class="client-report-card" onclick="window.location.href='/reports?client=${encodeURIComponent(client.client)}'">
                    <div class="client-report-header">
                        <div class="client-report-icon">🏢</div>
                        <div class="client-report-name">${client.client}</div>
                    </div>
                    <div class="client-report-stats">
                        <div class="client-stat">
                            <div class="client-stat-value">${(client.scans_count || 0).toLocaleString()}</div>
                            <div class="client-stat-label">Escaneos</div>
                        </div>
                        <div class="client-stat">
                            <div class="client-stat-value">${client.campaigns_count || 0}</div>
                            <div class="client-stat-label">Campañas</div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function renderEmptyClientReports() {
            const container = document.getElementById('clientReportsGrid');
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-state-icon">📊</div>
                    <h3>Sin datos de clientes</h3>
                    <p>Los reportes aparecerán cuando haya campañas registradas</p>
                </div>
            `;
        }

        // =============================================
        // ACTUALIZACIÓN DE UI
        // =============================================
        function updateStatsCards(stats) {
            animateNumber('totalScans', stats.total_scans || 0);
            // scans_24h viene del backend, NO usar total_scans como fallback
            animateNumber('scansToday', stats.scans_24h || 0);
            animateNumber('uniqueDevices', stats.unique_visitors || 0);
            animateNumber('totalClients', stats.total_clients || 0);
            animateNumber('activeCampaigns', stats.active_campaigns || 0);
            animateNumber('activeDevices', stats.active_devices || 0);
            animateDecimal('avgDuration', stats.avg_duration || 0, 's');
            animateDecimal('iosPct', stats.ios_pct || 0, '%');
        }

        function animateDecimal(elementId, targetValue, suffix) {
            const element = document.getElementById(elementId);
            if (!element) return;
            const startValue = parseFloat(element.textContent) || 0;
            const duration = 500;
            const startTime = performance.now();

            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                const currentValue = startValue + (targetValue - startValue) * progress;
                element.textContent = currentValue.toFixed(1) + suffix;

                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            }

            requestAnimationFrame(update);
        }

        function animateNumber(elementId, targetValue) {
            const element = document.getElementById(elementId);
            const startValue = parseInt(element.textContent) || 0;
            const duration = 500;
            const startTime = performance.now();

            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                const currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
                element.textContent = currentValue.toLocaleString();

                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            }

            requestAnimationFrame(update);
        }

        // Función para cambiar pestañas de dispositivos
        function showDeviceTab(tabName) {
            // Desactivar todas las pestañas
            document.querySelectorAll('.device-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.device-tab-panel').forEach(panel => panel.classList.remove('active'));

            // Activar la pestaña seleccionada
            document.getElementById('tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1)).classList.add('active');
            document.getElementById('panel' + tabName.charAt(0).toUpperCase() + tabName.slice(1)).classList.add('active');
        }

        // Función para navegar a campaña
        function goToCampaign(campaignCode) {
            if (campaignCode) {
                window.location.href = `/admin/campaigns?search=${encodeURIComponent(campaignCode)}`;
            }
        }

        // Función para navegar a dispositivo
        function goToDevice(deviceId) {
            if (deviceId) {
                window.location.href = `/devices?search=${encodeURIComponent(deviceId)}`;
            }
        }

        // =============================================
        // CASCADA JERÁRQUICA DE DISPOSITIVOS
        // =============================================

        // Iconos y colores por tipo/marca
        const hierarchyStyles = {
            types: {
                'Mobile': { icon: '📱', color: '#3b82f6' },
                'Desktop': { icon: '💻', color: '#8b5cf6' },
                'Tablet': { icon: '📲', color: '#f59e0b' },
                'Unknown': { icon: '❓', color: '#64748b' }
            },
            brands: {
                'Samsung': { icon: '📱', color: '#1428a0' },
                'Apple': { icon: '🍎', color: '#333333' },
                'Xiaomi': { icon: '📱', color: '#ff6700' },
                'Huawei': { icon: '📱', color: '#cf0921' },
                'Motorola': { icon: '📱', color: '#0077b6' },
                'Google': { icon: '📱', color: '#4285f4' },
                'OnePlus': { icon: '📱', color: '#eb001b' },
                'Oppo': { icon: '📱', color: '#1ea050' },
                'Vivo': { icon: '📱', color: '#4169e1' },
                'Nokia': { icon: '📱', color: '#124191' },
                'Other': { icon: '📱', color: '#64748b' },
                'Unknown': { icon: '❓', color: '#94a3b8' }
            }
        };

        function getHierarchyStyle(level, name) {
            if (level === 1) return hierarchyStyles.types[name] || { icon: '📱', color: '#64748b' };
            if (level === 2) return hierarchyStyles.brands[name] || { icon: '📱', color: '#64748b' };
            if (level === 3) return { icon: '📋', color: '#10b981' };
            if (level === 4) return { icon: '🌐', color: '#6366f1' };
            return { icon: '•', color: '#64748b' };
        }

        function renderHierarchyItem(item, level, expanded = false) {
            const hasChildren = (item.brands && item.brands.length > 0) ||
                (item.models && item.models.length > 0) ||
                (item.browsers && item.browsers.length > 0);
            const style = getHierarchyStyle(level, item.name);
            const expandedClass = expanded ? 'expanded' : '';
            const childrenKey = level === 1 ? 'brands' : (level === 2 ? 'models' : 'browsers');
            const children = item[childrenKey] || [];

            let childrenHtml = '';
            if (children.length > 0) {
                // Nivel 1 y 2 están expandidos por defecto
                const childExpanded = level < 2;
                childrenHtml = `
                    <div class="hierarchy-children ${expandedClass}">
                        ${children.map(child => renderHierarchyItem(child, level + 1, childExpanded)).join('')}
                    </div>
                `;
            }

            return `
                <div class="hierarchy-item hierarchy-level-${level}">
                    <div class="hierarchy-header" onclick="toggleHierarchy(this)">
                        <span class="hierarchy-toggle ${expandedClass}">${hasChildren ? '▶' : ''}</span>
                        <span class="hierarchy-icon">${style.icon}</span>
                        <span class="hierarchy-name">${item.name}</span>
                        <span class="hierarchy-count">${item.count.toLocaleString()}</span>
                    </div>
                    ${childrenHtml}
                </div>
            `;
        }

        function toggleHierarchy(header) {
            const toggle = header.querySelector('.hierarchy-toggle');
            const children = header.nextElementSibling;

            if (children && children.classList.contains('hierarchy-children')) {
                toggle.classList.toggle('expanded');
                children.classList.toggle('expanded');
            }
        }

        async function loadDeviceHierarchy() {
            const container = document.getElementById('deviceHierarchy');

            try {
                const response = await fetch(`${API_BASE}/analytics/device-hierarchy`);
                const data = await response.json();

                if (data.success && data.hierarchy && data.hierarchy.length > 0) {
                    // Renderizar con niveles 1 y 2 expandidos
                    container.innerHTML = data.hierarchy.map(item =>
                        renderHierarchyItem(item, 1, true)
                    ).join('');

                    // Expandir nivel 2 automáticamente
                    container.querySelectorAll('.hierarchy-level-1 > .hierarchy-children').forEach(el => {
                        el.classList.add('expanded');
                        el.previousElementSibling?.querySelector('.hierarchy-toggle')?.classList.add('expanded');
                    });
                } else {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📱</div>
                            <h3>Sin datos de dispositivos</h3>
                            <p style="font-size: 0.85rem; color: var(--text-muted);">Los datos aparecerán con los escaneos</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error cargando jerarquía:', error);
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h3>Error cargando datos</h3>
                    </div>
                `;
            }
        }

        function updateTopCampaigns(campaigns) {
            const container = document.getElementById('topCampaigns');

            if (!campaigns || campaigns.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🎯</div>
                        <h3>Sin datos de campañas</h3>
                    </div>
                `;
                return;
            }

            const rankClasses = ['gold', 'silver', 'bronze'];

            container.innerHTML = campaigns.slice(0, 5).map((campaign, index) => {
                const campaignCode = campaign.campaign || campaign.campaign_code;
                return `
                    <div class="top-item" onclick="goToCampaign('${campaignCode}')" style="cursor: pointer;" title="Clic para ver campaña">
                        <div class="top-rank ${rankClasses[index] || ''}">${index + 1}</div>
                        <div class="top-info">
                            <div class="top-name">${campaignCode}</div>
                            <div class="top-meta">${campaign.client || 'Sin cliente'}</div>
                        </div>
                        <div class="top-value">${campaign.scans || 0}</div>
                    </div>
                `;
            }).join('');
        }

        function updateTopPhysicalDevices(devices) {
            const container = document.getElementById('topPhysicalDevices');

            if (!devices || devices.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🖥️</div>
                        <h3>Sin datos de dispositivos</h3>
                    </div>
                `;
                return;
            }

            const rankClasses = ['gold', 'silver', 'bronze'];

            container.innerHTML = devices.slice(0, 5).map((device, index) => {
                const deviceId = device.device_id || '';
                return `
                    <div class="top-item" onclick="goToDevice('${deviceId}')" style="cursor: pointer;" title="Clic para ver dispositivo">
                        <div class="top-rank ${rankClasses[index] || ''}">${index + 1}</div>
                        <div class="top-info">
                            <div class="top-name">${device.device_name || device.device_id || 'Sin nombre'}</div>
                            <div class="top-meta">${device.venue || device.location || 'Sin ubicación'}</div>
                        </div>
                        <div class="top-value">${device.scans || 0}</div>
                    </div>
                `;
            }).join('');
        }

        function updateTopVenues(venues) {
            const container = document.getElementById('topVenues');

            if (!venues || venues.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🏢</div>
                        <h3>Sin datos de ubicaciones</h3>
                    </div>
                `;
                return;
            }

            const rankClasses = ['gold', 'silver', 'bronze'];

            container.innerHTML = venues.slice(0, 5).map((venue, index) => `
                <div class="top-item">
                    <div class="top-rank ${rankClasses[index] || ''}">${index + 1}</div>
                    <div class="top-info">
                        <div class="top-name">${venue.venue || 'Sin nombre'}</div>
                        <div class="top-meta">${venue.devices_count || 0} dispositivos</div>
                    </div>
                    <div class="top-value">${venue.scans || 0}</div>
                </div>
            `).join('');
        }

        function renderScansTable(scans) {
            const tbody = document.getElementById('scansTableBody');

            if (!scans || scans.length === 0) {
                renderEmptyScansTable();
                return;
            }

            // Guardar los scans para acceso desde toggle
            window.scansData = scans;

            tbody.innerHTML = scans.map((scan, index) => {
                const date = new Date(scan.scan_timestamp);
                const formattedDate = date.toLocaleDateString('es-ES', {
                    day: '2-digit',
                    month: '2-digit',
                    year: '2-digit'
                });
                const formattedTime = date.toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit'
                });

                const deviceBadge = getDeviceBadge(scan.user_device_type);

                // Formatear duración
                let durationText = '-';
                let durationClass = '';
                if (scan.duration_seconds !== null && scan.duration_seconds !== undefined) {
                    const duration = parseFloat(scan.duration_seconds);
                    if (duration < 60) {
                        durationText = duration.toFixed(1) + 's';
                    } else {
                        durationText = (duration / 60).toFixed(1) + 'm';
                    }
                    durationClass = duration < 10 ? 'success' : (duration < 60 ? 'warning' : '');
                }

                // Estado de conexión
                const connected = scan.redirect_completed ?
                    '<span class="badge badge-success">SÍ</span>' :
                    '<span class="badge badge-pending">NO</span>';

                // Marca del dispositivo
                const deviceBrand = scan.device_brand || scan.ua_brand || '-';
                const brandStyle = getBrandColor(deviceBrand);

                // Formatear fecha completa para el detalle
                const fullDate = date.toLocaleDateString('es-ES', {
                    weekday: 'long',
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric'
                });
                const fullTime = date.toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                // Tipo de conexión con icono
                let connectionIcon = '📶';
                let connectionType = scan.connection_generation || scan.connection_type || 'No detectado';
                if (connectionType.toLowerCase().includes('wifi')) connectionIcon = '📶';
                else if (connectionType.toLowerCase().includes('4g') || connectionType.toLowerCase().includes('3g') || connectionType.toLowerCase().includes('5g')) connectionIcon = '📱';

                // ISP/Operadora con colores
                let ispDisplay = scan.isp_carrier || 'No detectado';
                if (ispDisplay.includes('Digitel')) ispDisplay = '<span style="color: #00a651; font-weight: 600;">📱 Digitel</span>';
                else if (ispDisplay.includes('Movistar')) ispDisplay = '<span style="color: #019df4; font-weight: 600;">📱 Movistar</span>';
                else if (ispDisplay.includes('Movilnet')) ispDisplay = '<span style="color: #ff6600; font-weight: 600;">📱 Movilnet</span>';

                return `
                    <tr class="scan-row" onclick="toggleScanDetail(${index})" title="Clic para ver más detalles">
                        <td class="mono">${formattedDate} ${formattedTime}</td>
                        <td class="highlight">${scan.campaign_code || '-'}</td>
                        <td>${scan.client || '-'}</td>
                        <td>${scan.device_name || scan.device_id || '-'}</td>
                        <td>${deviceBadge}</td>
                        <td>${scan.browser || '-'}</td>
                        <td class="mono">${durationText}</td>
                        <td>${connected}</td>
                        <td style="${brandStyle}">${deviceBrand}</td>
                        <td>${connectionIcon} ${connectionType} <br><small>${ispDisplay}</small></td>
                    </tr>
                    <tr class="scan-detail" id="scan-detail-${index}">
                        <td colspan="10">
                            <div class="scan-detail-content">
                                <div class="detail-item">
                                    <div class="detail-label">🕐 Fecha y Hora</div>
                                    <div class="detail-value">${fullDate}<br>${fullTime}</div>
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
                                    <div class="detail-label">💻 Sistema Operativo</div>
                                    <div class="detail-value">${scan.operating_system || '-'}</div>
                                </div>
                                <div class="detail-item ${durationClass}">
                                    <div class="detail-label">⏱️ Duración</div>
                                    <div class="detail-value">${durationText}</div>
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
                                    <div class="detail-value mono">${scan.ip_address || '-'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">🔑 ID Escaneo</div>
                                    <div class="detail-value mono">#${scan.id || '-'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">🔐 Fingerprint</div>
                                    <div class="detail-value mono">${scan.device_fingerprint || '-'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">⚙️ Hardware</div>
                                    <div class="detail-value">${scan.cpu_cores ? scan.cpu_cores + ' cores' : '-'}${scan.device_memory ? ' • ' + scan.device_memory + 'GB RAM' : ''}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">🎮 GPU</div>
                                    <div class="detail-value" style="font-size: 0.75rem;">${scan.webgl_renderer || '-'}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">🔋 Batería</div>
                                    <div class="detail-value">${scan.battery_level !== null ? scan.battery_level + '%' : '-'}${scan.battery_charging ? ' ⚡' : ''}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">📱 Sensores</div>
                                    <div class="detail-value">${[scan.has_gyroscope ? '🔄Gyro' : '', scan.has_accelerometer ? '📐Accel' : '', scan.has_geolocation ? '📍GPS' : ''].filter(Boolean).join(' ') || '-'}</div>
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        // Función para expandir/contraer detalle de escaneo
        function toggleScanDetail(index) {
            const row = document.querySelector(`tr.scan-row:nth-child(${index * 2 + 1})`);
            const detailRow = document.getElementById(`scan-detail-${index}`);

            if (detailRow) {
                const isExpanded = detailRow.classList.contains('show');

                // Cerrar todos los demás detalles abiertos
                document.querySelectorAll('tr.scan-detail.show').forEach(tr => tr.classList.remove('show'));
                document.querySelectorAll('tr.scan-row.expanded').forEach(tr => tr.classList.remove('expanded'));

                // Toggle del detalle actual
                if (!isExpanded) {
                    detailRow.classList.add('show');
                    row.classList.add('expanded');
                }
            }
        }

        function renderEmptyScansTable() {
            const tbody = document.getElementById('scansTableBody');
            tbody.innerHTML = `
                <tr>
                    <td colspan="9">
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <h3>No hay escaneos registrados</h3>
                            <p>Los escaneos aparecerán aquí cuando los usuarios escaneen códigos QR</p>
                        </div>
                    </td>
                </tr>
            `;
        }

        function getBrandColor(brand) {
            if (!brand || brand === '-') return '';

            const brandColors = {
                'Samsung': 'color: #1428a0; font-weight: 600;',
                'Apple': 'color: #333333; font-weight: 600;',
                'Xiaomi': 'color: #ff6700; font-weight: 600;',
                'Huawei': 'color: #cf0921; font-weight: 600;',
                'Motorola': 'color: #0077b6; font-weight: 600;',
                'Google': 'color: #4285f4; font-weight: 600;',
                'OnePlus': 'color: #eb001b; font-weight: 600;',
                'Oppo': 'color: #1ea050; font-weight: 600;',
                'Vivo': 'color: #4169e1; font-weight: 600;',
                'LG': 'color: #a11c37; font-weight: 600;',
                'Sony': 'color: #000000; font-weight: 600;',
                'Nokia': 'color: #124191; font-weight: 600;',
                'Realme': 'color: #ffc600; font-weight: 600;',
                'Tecno': 'color: #0066cc; font-weight: 600;',
                'Infinix': 'color: #f58220; font-weight: 600;',
                'ZTE': 'color: #0066cc; font-weight: 600;',
                'Honor': 'color: #00a3e0; font-weight: 600;'
            };

            // Buscar coincidencia parcial
            for (const [key, value] of Object.entries(brandColors)) {
                if (brand.toLowerCase().includes(key.toLowerCase())) {
                    return value;
                }
            }
            return 'font-weight: 500;';
        }

        function getDeviceBadge(deviceType) {
            const types = {
                'Mobile': 'badge-mobile',
                'Desktop': 'badge-desktop',
                'Tablet': 'badge-tablet'
            };
            const badgeClass = types[deviceType] || 'badge-mobile';
            return `<span class="badge ${badgeClass}">${deviceType || 'Unknown'}</span>`;
        }

        function updateLastUpdate() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('lastUpdate').textContent = `Actualizado: ${timeStr}`;
        }

        // =============================================
        // GRÁFICO
        // =============================================
        
        function initializeChart() {
            const ctx = document.getElementById('scansChart').getContext('2d');

            scansChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Escaneos',
                        data: [],
                        borderColor: '#00f0ff', // Neon Cyan
                        backgroundColor: 'rgba(0, 240, 255, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#00f0ff',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { mode: 'index', intersect: false, backgroundColor: 'rgba(0,0,0,0.8)', titleColor: '#00f0ff', bodyColor: '#fff' }
                    },
                    scales: {
                        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#a1a1aa' } },
                        y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#a1a1aa', stepSize: 1 } }
                    }
                }
            });

            // Initialize Radar Chart
            const ctxRadar = document.getElementById('deviceChart').getContext('2d');
            deviceRadarChart = new Chart(ctxRadar, {
                type: 'radar',
                data: {
                    labels: ['iOS', 'Android', 'Windows', 'Mac', 'Unknown'],
                    datasets: [{
                        label: 'Distribución SO',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(112, 0, 255, 0.2)', // Purple Glow
                        borderColor: '#7000ff',
                        pointBackgroundColor: '#7000ff',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#7000ff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            pointLabels: { color: '#a1a1aa', font: { size: 12 } },
                            ticks: { display: false }
                        }
                    },
                    plugins: { legend: { display: false } }
                }
            });

            // Initialize Leaflet Map (Dark Cyberpunk Theme)
            if (document.getElementById('geoMap')) {
                geoMap = L.map('geoMap', {
                    center: [10.4806, -66.9036], // Caracas, VE default
                    zoom: 5,
                    zoomControl: false,
                    attributionControl: false
                });

                // CartoDB Dark Matter tiles for modern look
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                    subdomains: 'abcd',
                    maxZoom: 19
                }).addTo(geoMap);
            }
        }
function updateChartData(chartData) {
            if (!scansChart || !chartData) return;

            const labels = chartData.map(d => d.label);
            const data = chartData.map(d => d.value);

            scansChart.data.labels = labels;
            scansChart.data.datasets[0].data = data;
            scansChart.update();
        }

        async function updateChart() {
            const period = document.getElementById('chartPeriod').value;
            try {
                const response = await fetch(`${API_BASE}/analytics/chart?period=${period}`);
                const result = await response.json();

                if (result.success && result.data) {
                    updateChartData(result.data);
                }
            } catch (error) {
                console.error('Error loading chart:', error);
            }
        }

        // =============================================
        // FILTROS
        // =============================================
        function populateSelect(selectId, items, valueKey, labelKey, subtitleKey = null) {
            const select = document.getElementById(selectId);
            const firstOption = select.options[0];
            select.innerHTML = '';
            select.appendChild(firstOption);

            items.forEach(item => {
                const option = document.createElement('option');
                option.value = item[valueKey];
                option.textContent = subtitleKey
                    ? `${item[labelKey]} (${item[subtitleKey]})`
                    : item[labelKey];
                select.appendChild(option);
            });
        }

        function populateClientSelect(selectId, clients) {
            const select = document.getElementById(selectId);
            const firstOption = select.options[0];
            select.innerHTML = '';
            select.appendChild(firstOption);

            clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client;
                option.textContent = client;
                select.appendChild(option);
            });
        }

        function applyFilters() {
            currentFilters = {
                startDate: document.getElementById('filterStartDate').value || null,
                endDate: document.getElementById('filterEndDate').value || null,
                campaign: document.getElementById('filterCampaign').value || null,
                device: document.getElementById('filterDevice').value || null,
                client: document.getElementById('filterClient').value || null
            };

            loadScans();
        }

        // =============================================
        // FALLBACKS
        // =============================================
        function showFallbackStats() {
            document.getElementById('totalScans').textContent = '0';
            document.getElementById('scansToday').textContent = '0';
            document.getElementById('uniqueDevices').textContent = '0';
            document.getElementById('totalClients').textContent = '0';
            document.getElementById('activeCampaigns').textContent = '0';
            document.getElementById('activeDevices').textContent = '0';
            document.getElementById('avgDuration').textContent = '0.0s';
            document.getElementById('iosPct').textContent = '0.0%';
        }

        // =============================================
        // UTILIDADES
        // =============================================
        window.addEventListener('beforeunload', () => {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
            }
        });

        // Atajos de teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                refreshAllData();
            }
        });

        console.log('⌨️ Atajo: Ctrl+R para refrescar datos');
    