import re

with open('static/js/dashboard_logic.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add Leaflet + Radar Chart definitions at the top
init_globals = """
        // =============================================
        // CONFIGURACIÓN GLOBAL & ADVANCED CHARTS
        // =============================================
        const API_BASE = window.location.origin + '/api';
        let scansChart = null;
        let deviceRadarChart = null;
        let geoMap = null;
        let heatLayer = null;
"""
js = re.sub(r'// =============================================\s*// CONFIGURACIÓN GLOBAL\s*// =============================================\s*const API_BASE = .*?;', init_globals, js, flags=re.DOTALL)

init_charts = """
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
"""
js = re.sub(r'function initializeChart\(\) \{.*?(?=function updateChartData)', init_charts, js, flags=re.DOTALL)


update_stats = """
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
"""
js = re.sub(r'async function loadStats\(\) \{.*?(?=async function loadScans\(\))', update_stats, js, flags=re.DOTALL)

with open('static/js/dashboard_logic.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("JS updated successfully.")
