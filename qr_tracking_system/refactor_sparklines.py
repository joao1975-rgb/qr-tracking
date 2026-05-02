import re

file_path = "templates/dashboard_antigravity_v28.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove static sparklines init block
old_spark = """const sparkData = {
    total:  [1240,1580,1320,1960,2380,1840,2120,2480,1960,2731],
    unique: [930,1190,990,1470,1780,1380,1590,1860,1470,2050],
    ctr:    [2.8,3.1,2.9,3.2,2.6,2.9,3.1,2.8,2.7,2.76],
    dur:    [48,52,45,58,62,54,60,55,58,62]
  };
  drawSparkline('spark-total',  sparkData.total,  '#00CFFF');
  drawSparkline('spark-unique', sparkData.unique, '#00E5A0');
  drawSparkline('spark-ctr',    sparkData.ctr,    '#FFAD33');
  drawSparkline('spark-dur',    sparkData.dur,    '#A855F7');"""

new_spark = """const sparkData = { total: [0,0], unique: [0,0] };
  // Sparklines will be drawn when loadLiveStats injects them"""

if old_spark in html:
    html = html.replace(old_spark, new_spark)
    print("Sparkline DOM block removed.")
else:
    print("Could not find old sparkline block.")

# Add to the dynamic segment
old_js = """chartsConfigured = true;
      }"""

new_js = """chartsConfigured = true;
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
      }"""

if old_js in html:
    html = html.replace(old_js, new_js)
    print("Sparkline JS block injected.")
else:
    print("Could not find old_js anchor for sparklines.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
