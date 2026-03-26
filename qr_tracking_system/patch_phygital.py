import os
import re

file_path = r"C:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\templates\phygital_dashboard.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add IDs to the KPIs
content = content.replace('<div class="kpi-value">24,731</div>', '<div class="kpi-value" id="val-total">24,731</div>')
content = content.replace('<div class="kpi-value">18,209</div>', '<div class="kpi-value" id="val-unique">18,209</div>')
content = content.replace('<div class="kpi-value">3.8%</div>', '<div class="kpi-value" id="val-conv">3.8%</div>')
content = content.replace('<div class="kpi-value">1m 47s</div>', '<div class="kpi-value" id="val-dur">1m 47s</div>')

# Add the fetch block inside the existing <script>
script_injection = """
async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics/scan-breakdown/CENTAURO_Q1_2026');
        const data = await res.json();
        
        if(data && data.total_visitors !== undefined) {
            document.getElementById('val-total').textContent = data.total_visitors.toLocaleString();
            document.getElementById('val-unique').textContent = data.single_scan_visitors.toLocaleString();
            
            // Just some derived metrics for the mockup completeness
            const conv = ((data.total_visitors / 5000) * 100).toFixed(1);
            document.getElementById('val-conv').textContent = conv + '%';
        }
    } catch(err) {
        console.error('Error loading analytics:', err);
    }
}
loadAnalytics();
"""

content = content.replace('</script>', script_injection + '\n</script>')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("phygital_dashboard.html patched with dynamic IDs and API fetch.")
