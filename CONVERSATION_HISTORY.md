# QuantBacktestEngine - Initial Research & Design Conversation Log

## Overview
This document records the full research, user requirements, design interview decisions, and architectural roadmap for `QuantBacktestEngine`.

---

## 1. User Core Requirements & Goals
- **Objective**: Build an elegant, reusable, scalable, fast, and customizable backtest & optimization engine for Stock/ETF equity trading.
- **Reference**: [backtesting.py](https://github.com/kernc/backtesting.py)
- **Key Features**:
  1. Built-in institutional-proven position sizing (ATR Risk Sizing, Fractional Kelly, Volatility Parity, Drawdown scaling).
  2. Advanced Risk Management & State-of-the-Art Trailing Stop Engine (Hard stops, Break-even ratchets, Chandelier exits, Multi-tier profit locks, Time decay exits).
  3. Standalone Architecture: Packaged independently so it can be called by any current or future project (including `GammaGexTrading`).
  4. Strategy Management & Versioning: Declarative YAML/JSON strategy specs, SQLite strategy metadata registry (`strategies.db`), and side-by-side strategy version matrix comparator.
  5. Rich Visualization UI: Modern Web Dashboard (`quant-engine ui`) for equity/drawdown charting, version overlays, Optuna 3D parameter surface exploration, and MAE/MFE analytics.

---

## 2. Design Interview Decisions (Grill-Me Summary)

| Design Topic | Selected Option | Description |
| :--- | :--- | :--- |
| **Engine Architecture** | **Custom Hybrid Engine (`backtesting.py` Core)** | Wraps `backtesting.py` for speed & clean API, enriched with modular institutional risk & position sizing extensions. |
| **Position Sizing** | **Multi-Strategy Suite** | Supports ATR Risk Sizing (% risk / ATR distance), Fractional Kelly, Volatility Parity, and dynamic risk reduction during drawdowns. |
| **Trailing Stop Engine** | **Multi-Stage Modular Trailing Stop** | Includes hard ATR stop, break-even ratchet at +1R, high-water mark Chandelier exits, multi-tier profit locks (+2R/+3R), and time decay exits. |
| **Optimization Engine** | **Hybrid Grid + Optuna Bayesian** | Multi-core parallel grid search for smaller parameter spaces; Optuna TPE Bayesian optimization with early pruning for high-dimensional spaces. |
| **Delivery & Scope** | **Standalone Package & Dashboard** | Built as a standalone repository (`QuantBacktestEngine`) with `pyproject.toml`, REST API server, and rich interactive web dashboard. |

---

## 3. Project File Tree Layout

```
QuantBacktestEngine/
├── pyproject.toml / setup.py       # Package distribution definition
├── README.md                       # Complete documentation & quickstart
├── implementation_plan.md          # Technical design & research specification
├── CONVERSATION_HISTORY.md         # Full research & interview transcript
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

## 4. How to Continue Development
1. **Option A (In this current chat)**: You can approve starting implementation, and I will begin writing the core modules inside `QuantBacktestEngine`.
2. **Option B (Opening the project folder)**: Open `C:\Users\jfan\Documents\QuantBacktestEngine` in VS Code / Antigravity IDE (**File -> Open Folder**). Start a new chat prompt there, and the AI assistant will read `CONVERSATION_HISTORY.md` and `implementation_plan.md` automatically.
