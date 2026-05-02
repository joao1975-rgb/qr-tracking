const data = {
    daily_scans: [
        {date: '2026-03-03', scans: 19, unique_scans: 7},
        {date: '2026-03-04', scans: 9, unique_scans: 6}
    ],
    stats: { total_scans: 59 },
    success: true
};

const chartData = {
    '7d': {labels: [], scans: []},
    '1d': {labels: [], scans: []}
};

let mainChart = {
    data: {
        labels: [],
        datasets: [{data: []}, {data: []}, {data: []}, {data: []}]
    },
    update: function(arg) { console.log('Chart updated with arg:', arg); }
};

function updateMainChart(range) {
  if (!mainChart) return;
  const d = chartData[range] || chartData['7d'];
  mainChart.data.labels = d.labels;
  mainChart.data.datasets[0].data = d.multiAvg;
  mainChart.data.datasets[1].data = d.scans;
  mainChart.data.datasets[2].data = d.unique;
  mainChart.data.datasets[3].data = d.bench;
  mainChart.update('active');
}

async function runTest() {
    try {
        if (data.daily_scans && mainChart) {
            let labels = [], scans = [], unique = [];
            data.daily_scans.forEach(row => {
                labels.push(row.date.substring(5)); // Extraemos 'MM-DD'
                scans.push(row.scans);
                unique.push(row.unique_scans);
            });
            // Blindar todos los selectores de tiempo para forzar la muestra real
            Object.keys(chartData).forEach(key => {
                chartData[key] = {
                    labels: labels,
                    scans: scans,
                    unique: unique,
                    bench: new Array(labels.length).fill(null), // Anular benchmark simulado
                    multiAvg: new Array(labels.length).fill(null) // Anular barras mock secundarias
                };
            });
            updateMainChart('7d'); // Refresca lienzo
        }
        console.log('Test success!');
    } catch(e) {
        console.error('ERROR:', e);
    }
}

runTest();
