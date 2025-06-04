// chart.js
const rawData = JSON.parse(document.getElementById("risk-data").textContent);

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
            pointBackgroundColor: data.map(value => {
                if (value > 60) return 'rgba(239, 68, 68, 1)';    // 🔴 High risk
                if (value > 30) return 'rgba(234, 179, 8, 1)';     // 🟡 Medium risk
                return 'rgba(34, 197, 94, 1)';                     // 🟢 Low risk
            }),
            borderColor: 'rgba(13, 148, 136, 1)',
            backgroundColor: 'rgba(13, 148, 136, 0.2)',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 6
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
                display: true,
                labels: {
                    generateLabels: function(chart) {
                        return [
                            {
                                text: 'Low Risk (≤ 30)',
                                fillStyle: 'rgba(34, 197, 94, 1)',
                                strokeStyle: 'rgba(34, 197, 94, 1)',
                                pointStyle: 'circle'
                            },
                            {
                                text: 'Medium Risk (31 - 60)',
                                fillStyle: 'rgba(234, 179, 8, 1)',
                                strokeStyle: 'rgba(234, 179, 8, 1)',
                                pointStyle: 'circle'
                            },
                            {
                                text: 'High Risk (> 60)',
                                fillStyle: 'rgba(239, 68, 68, 1)',
                                strokeStyle: 'rgba(239, 68, 68, 1)',
                                pointStyle: 'circle'
                            }
                        ];
                    }
                }
            }
        }
    }
});