document.addEventListener('DOMContentLoaded', () => {
    // Navigation Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            item.classList.add('active');
            const targetTab = item.getAttribute('data-tab');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Chart.js Setup
    const ctx = document.getElementById('equityChart').getContext('2d');
    let equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Equity ($)',
                data: [],
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#F3F4F6', font: { family: 'Inter' } } }
            },
            scales: {
                x: { ticks: { color: '#9CA3AF' }, grid: { color: '#232936' } },
                y: { ticks: { color: '#9CA3AF' }, grid: { color: '#232936' } }
            }
        }
    });

    // Run Backtest Handler
    const btnRunBacktest = document.getElementById('btn-run-backtest');
    btnRunBacktest.addEventListener('click', async () => {
        const symbol = document.getElementById('input-symbol').value;
        const cash = parseFloat(document.getElementById('input-cash').value);
        const riskPct = parseFloat(document.getElementById('input-risk-pct').value) / 100.0;
        const sizerType = document.getElementById('input-sizer-type').value;
        const specRaw = document.getElementById('input-spec-editor').value;

        btnRunBacktest.innerText = "⏳ Running Backtest...";

        try {
            // Parse raw spec string or build payload
            let specObj = {};
            try {
                specObj = JSON.parse(specRaw);
            } catch (e) {
                // If YAML string, send as spec or default dict
                specObj = {
                    name: "InteractiveStrategy",
                    indicators: {
                        ema_fast: { type: "EMA", period: 10 },
                        ema_slow: { type: "EMA", period: 30 }
                    },
                    position_sizing: { type: sizerType, risk_pct: riskPct },
                    rules: { entry_long: "ema_fast > ema_slow" }
                };
            }

            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    cash: cash,
                    strategy_spec: specObj
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Backtest failed");

            // Update Metrics Display
            const m = data.metrics;
            document.getElementById('metric-return').innerText = (m.total_return * 100).toFixed(2) + '%';
            document.getElementById('metric-sharpe').innerText = m.sharpe_ratio.toFixed(2);
            document.getElementById('metric-drawdown').innerText = (m.max_drawdown * 100).toFixed(2) + '%';
            document.getElementById('metric-winrate').innerText = (m.win_rate * 100).toFixed(1) + '%';

            // Update Equity Chart
            const labels = data.equity_curve.map(pt => pt.time);
            const values = data.equity_curve.map(pt => pt.value);

            equityChart.data.labels = labels;
            equityChart.data.datasets[0].data = values;
            equityChart.update();

        } catch (err) {
            alert("Backtest Error: " + err.message);
        } finally {
            btnRunBacktest.innerText = "▶ Run Backtest";
        }
    });

    // Run Optuna Handler
    const btnRunOptuna = document.getElementById('btn-run-optuna');
    btnRunOptuna.addEventListener('click', async () => {
        const symbol = document.getElementById('input-symbol').value;
        const outputPre = document.getElementById('optuna-output');

        btnRunOptuna.innerText = "⏳ Running Optuna TPE Search...";
        outputPre.innerText = "Running 20-trial Optuna Bayesian Optimization over parameter space...";

        try {
            const specObj = {
                name: "OptunaTuningStrategy",
                indicators: {
                    ema_fast: { type: "EMA", period: 10 },
                    ema_slow: { type: "EMA", period: 30 }
                },
                rules: { entry_long: "ema_fast > ema_slow" }
            };

            const response = await fetch('/api/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    method: "optuna",
                    n_trials: 20,
                    target_metric: "sharpe_ratio",
                    strategy_spec: specObj,
                    param_bounds: {
                        "risk_pct": [0.01, 0.04],
                        "atr_multiplier": [1.5, 4.0]
                    }
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Optimization failed");

            outputPre.innerText = JSON.stringify(data, null, 2);

        } catch (err) {
            outputPre.innerText = "Optuna Error: " + err.message;
        } finally {
            btnRunOptuna.innerText = "Run 20-Trial Optuna Optimization";
        }
    });

    // Load Strategy Repository on startup
    fetch('/api/strategies')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('repository-list');
            if (data.strategies && data.strategies.length > 0) {
                container.innerHTML = data.strategies.map(s => `
                    <div style="background: #0A0D12; padding: 12px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #232936;">
                        <strong>${s.name}</strong> <span style="color: #3B82F6;">v${s.version}</span>
                        <div style="font-size: 12px; color: #9CA3AF;">Created: ${s.created_at}</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-muted">No strategies stored in repository yet. Save one via API or Spec Editor.</p>';
            }
        })
        .catch(err => console.error("Failed to load strategy repository:", err));
});
