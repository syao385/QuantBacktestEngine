# QuantBacktestEngine 📈🚀

An elegant, reusable, scalable, fast, and customizable **Backtesting, Optimization & Strategy Management Platform** for stock and ETF equity trading.

Inspired by [`backtesting.py`](https://github.com/kernc/backtesting.py), `QuantBacktestEngine` combines vector-assisted event simulation speed with institutional risk management, state-of-the-art multi-stage trailing stops, Optuna Bayesian hyperparameter optimization, declarative strategy versioning, and a rich interactive web UI dashboard.

---

## 🌟 Key Features

### 1. ⚙️ Core Engine & Vector-Event Hybrid
- Built on `backtesting.py` core for ultra-fast bar execution and clean Pythonic strategy definition.
- Native support for market, limit, stop orders, fractional shares, slippage, and commissions.
- High-performance vector metrics computation (Sharpe, Sortino, Calmar, SQN, Profit Factor, Max Drawdown).

### 2. 🛡️ Institutional Position Sizing & Risk Management
- **ATR / Volatility Risk Sizing**: Dynamic share count calculation based on account risk % divided by ATR stop distance.
- **Fractional Kelly Criterion**: Automated bet sizing derived from rolling win rate and win/loss ratio.
- **Volatility Parity**: Risk allocation inversely proportional to historical volatility.
- **Equity Drawdown Guard**: Automated risk throttling during equity drawdowns (e.g. 50% risk scaling when drawdown > 10%).

### 3. 🎯 State-of-the-Art Trailing Stop Engine
- **Multi-Stage Ratchet Mechanics**:
  - *Hard Initial Stop*: ATR-based or percentage distance from entry.
  - *Break-Even Ratchet*: Auto-shifts stop loss to entry price + fees at $+1.0\text{R}$ profit.
  - *Chandelier Exit*: Continuous high-water mark trailing offset by $K \times \text{ATR}$.
  - *Multi-Tier Profit Lock*: Tightens trailing multiplier dynamically as profit reaches $+2\text{R}, +3\text{R}, +4\text{R}$ targets.
  - *Time-Decay Exit*: Exits flat positions after $N$ bars of non-performance.

### 4. 🧬 Strategy Versioning & Lifecycle Repository
- **Declarative & Code Strategies**: Define strategies in Python code or as YAML/JSON specs.
- **Version Control & Lineage**: SQLite metadata store (`strategies.db`) maintaining strategy version history (`v1.0` -> `v1.1`), parameter diffs, and execution run logs.
- **Multi-Version Matrix Comparator**: Side-by-side performance comparison and trade correlation matrix across multiple strategy versions.

### 5. 🔍 Multiprocessing & Optuna Bayesian Optimization
- **Parallel Grid Search**: Multi-core CPU parameter grid exploration.
- **Optuna TPE Optimization**: Tree-structured Parzen Estimator Bayesian optimization with early pruning for high-dimensional search spaces.
- **Target Metrics**: Optimize for Sharpe Ratio, Sortino Ratio, Calmar Ratio, SQN, or custom risk-adjusted return functions.

### 6. 📊 Rich Interactive Visualization UI
- Built-in web dashboard accessible via `quant-engine ui` (`http://localhost:8500`).
- **Interactive Equity & Underwater Drawdown Charts**.
- **Strategy Version Side-by-Side Comparison Overlay**.
- **3D/2D Optuna Parameter Optimization Surface Explorer**.
- **MAE / MFE (Maximum Adverse / Favorable Excursion) Analytics**.

---

## 🛠️ Architecture & Package Layout

```
QuantBacktestEngine/
├── pyproject.toml / setup.py       # Package distribution definition
├── README.md                       # Complete documentation & quickstart
├── implementation_plan.md          # Technical design & research specification
├── quant_engine/                   # Core Python Package
│   ├── __init__.py
│   ├── api.py                      # Main Python API entrypoint (Engine, Strategy, Optimizer)
│   ├── core/                       # Execution & simulation core
│   │   ├── runner.py               # Vectorized event runner wrapping backtesting.py
│   │   ├── data.py                 # Universal data loader (yfinance, CSV, Parquet, Alpaca)
│   │   └── metrics.py              # Performance calculations (Sharpe, Sortino, Calmar, SQN)
│   ├── risk/                       # Risk management modules
│   │   ├── sizer.py                # Position sizer (ATR, Fractional Kelly, Risk Parity)
│   │   └── trailing_stop.py        # Multi-stage trailing stop engine
│   ├── strategy/                   # Strategy management & versioning
│   │   ├── base.py                 # Base Strategy class
│   │   ├── declarative.py          # YAML/JSON strategy spec parser
│   │   ├── repository.py           # Strategy DB & version control manager
│   │   └── comparator.py           # Multi-strategy performance comparator
│   ├── optimization/               # Parameter tuning
│   │   ├── grid.py                 # Multi-core parallel grid search
│   │   └── optuna_tpe.py           # Optuna Bayesian optimization & pruning
│   └── server/                     # Standalone REST API & UI Server
│       ├── app.py                  # FastAPI web server
│       └── static/                 # Rich Visualization Dashboard (HTML5 / JS / Canvas)
├── tests/                          # Unit & integration test suite
└── examples/                       # Example strategies & usage scripts
```

---

## 🚀 Quickstart & Usage

### 1. Installation
```bash
cd QuantBacktestEngine
pip install -e .
```

### 2. Standalone UI Dashboard
```bash
quant-engine ui --port 8500
```
Navigate to `http://localhost:8500` to access the interactive backtesting dashboard, strategy version comparator, and parameter surface explorer.

---

## 📜 Repository Information
- **GitHub Repository**: [https://github.com/syao385/QuantBacktestEngine](https://github.com/syao385/QuantBacktestEngine)
- **License**: MIT
