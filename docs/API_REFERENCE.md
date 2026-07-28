# QuantBacktestEngine API Reference

## 1. Engine Runner (`quant_engine.core.runner`)

### `EngineRunner.run_backtest(strategy_class, source, symbol="SPY", start_date=None, end_date=None, cash=100000.0, commission=0.0005, strategy_params=None)`
Executes backtest simulation for a strategy.

- **Parameters**:
  - `strategy_class`: Class inheriting from `QuantStrategy` or parsed from `DeclarativeStrategyParser`.
  - `source`: Symbol string, file path (`.csv`, `.parquet`), or DataFrame.
  - `symbol`: Ticker symbol name.
  - `cash`: Initial account equity in dollars.
  - `commission`: Order fee fraction (0.0005 = 0.05%).
- **Returns**: `BacktestResult` object with `metrics`, `equity_curve`, and `trades`.

---

## 2. Risk Sizer (`quant_engine.risk.sizer`)

### `PositionSizer(sizing_type="atr_risk", risk_pct=0.015, atr_multiplier=2.0, kelly_fraction=0.5, drawdown_guard=True)`
Institutional position sizer computing optimal share counts.

- **Sizing Types**:
  - `"atr_risk"`: Shares = (Equity * Risk %) / (ATR * Multiplier)
  - `"fractional_kelly"`: Shares sized via Kelly Criterion ($f^* = p - \frac{1-p}{b}$) scaled by `kelly_fraction`.
  - `"volatility_parity"`: Allocation inversely proportional to asset volatility.
  - `"fixed_pct"`: Fixed percentage of portfolio equity.

---

## 3. Trailing Stop Engine (`quant_engine.risk.trailing_stop`)

### `TrailingStopEngine(stop_type="chandelier_ratchet", atr_multiplier=3.0, breakeven_trigger_r=1.0, profit_lock_tiers=None)`
State-machine trailing stop manager.

- **Ratchet Stages**:
  - **Stage 0**: Hard initial stop loss.
  - **Stage 1**: Break-even ratchet (+1.0R profit).
  - **Stage 2+**: Chandelier high-water mark trailing with profit lock tightening (+2.0R, +3.0R).

---

## 4. Optuna Optimizer (`quant_engine.optimization.optuna_tpe`)

### `OptunaOptimizer.optimize(strategy_class, source, param_bounds, symbol="SPY", target_metric="sharpe_ratio", n_trials=30)`
Runs Tree-structured Parzen Estimator (TPE) Bayesian hyperparameter optimization.
