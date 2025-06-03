// chart.js


const rawData = JSON.parse(document.getElementById("risk-data").textContent);

const riskTrendData = {
    dates: rawData.map(item => item.date),
    values: rawData.map(item => item.risk_level)
};

const pointColors = rawData.map(item => {
    const risk = item.risk_level;
    if (risk < 30) return 'green';
    if (risk < 60) return 'orange';
    return 'red';
});

const ctx = document.getElementById('riskChart').getContext('2d');
const riskChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: riskTrendData.dates,
        datasets: [{
            label: 'Risk Level',
            data: riskTrendData.values,
            backgroundColor: pointColors,
            borderColor: 'rgba(13, 148, 136, 1)',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 5,
            pointBackgroundColor: pointColors
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                max: 100
            }
        },
        plugins: {
            legend: {
                display: true
            }
        }
    }
});
