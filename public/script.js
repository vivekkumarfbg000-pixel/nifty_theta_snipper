let equityChart;

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('total-pnl').innerText = `₹${data.total_net_pnl.toLocaleString('en-IN')}`;
        document.getElementById('total-pnl').className = `huge-value ${data.total_net_pnl >= 0 ? 'green' : 'red'}`;
        
        document.getElementById('win-rate').innerText = `Win Rate: ${data.win_rate}%`;
        document.getElementById('best-trade').innerText = `₹${data.best_trade.toLocaleString('en-IN')}`;
        document.getElementById('worst-trade').innerText = `₹${data.worst_trade.toLocaleString('en-IN')}`;
        document.getElementById('total-trades').innerText = data.total_trades;
        document.getElementById('avg-trade').innerText = `₹${data.avg_trade.toLocaleString('en-IN')}`;
        
        updateChart(data.equity_curve);
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchTrades() {
    try {
        const response = await fetch('/api/trades');
        const trades = await response.json();
        
        const tbody = document.getElementById('trade-body');
        tbody.innerHTML = '';
        
        trades.forEach(trade => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${trade.date}</td>
                <td><span class="tag">${trade.strategy}</span></td>
                <td>${trade.strike}</td>
                <td>${trade.points_captured > 0 ? '+' : ''}${trade.points_captured}</td>
                <td class="${trade.net_pnl >= 0 ? 'green' : 'red'}">₹${trade.net_pnl.toLocaleString('en-IN')}</td>
                <td><span class="mode-tag">${trade.is_paper ? 'PAPER' : 'LIVE'}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching trades:', error);
    }
}

function updateChart(curve) {
    const ctx = document.getElementById('equityChart').getContext('2d');
    
    const labels = curve.map(p => p.date);
    const values = curve.map(p => p.value);
    
    if (equityChart) {
        equityChart.destroy();
    }
    
    equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative Net P&L',
                data: values,
                borderColor: '#00f2ff',
                backgroundColor: 'rgba(0, 242, 255, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#00f2ff',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Initial Load
fetchStats();
fetchTrades();

// Refresh every 30 seconds
setInterval(() => {
    fetchStats();
    fetchTrades();
}, 30000);
