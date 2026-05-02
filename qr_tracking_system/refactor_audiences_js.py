import re

file_path = "templates/dashboard_antigravity_v28.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add IDs to the containers so we can populate them from JS
html = html.replace('<div class="segment-list">', '<div class="segment-list" id="dynamic-segments">')
html = html.replace('<div class="signal-list">', '<div class="signal-list" id="dynamic-signals">')

# 2. JS Injection at the end of loadLiveStats()
old_js = """createDonut();
         buildHeatmap();
         chartsConfigured = true;
      }"""

new_js = """createDonut();
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
      }"""

if old_js in html:
    html = html.replace(old_js, new_js)
    print("Injected Audience JS logic successfully.")
else:
    print("Could not find old_js anchor for audience insertion")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
