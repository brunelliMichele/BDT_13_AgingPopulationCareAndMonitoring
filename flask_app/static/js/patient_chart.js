// chart.js
const rawData = JSON.parse(document.getElementById("risk-data").textContent);
console.log("📊 riskChart rawData:", rawData);

const labels = rawData.dates || [];
const data = rawData.values || [];

const ctx = document.getElementById('riskChart').getContext('2d');
const riskChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
            label: 'Risk Level',
            data: data,
            backgroundColor: 'rgba(13, 148, 136, 0.2)',
            borderColor: 'rgba(13, 148, 136, 1)',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 3
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