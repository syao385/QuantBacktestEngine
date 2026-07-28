import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from quant_engine import __version__
from quant_engine.core.runner import EngineRunner
from quant_engine.strategy.declarative import DeclarativeStrategyParser
from quant_engine.strategy.repository import StrategyRepository
from quant_engine.strategy.comparator import StrategyComparator
from quant_engine.optimization.optuna_tpe import OptunaOptimizer
from quant_engine.optimization.grid import GridOptimizer

app = FastAPI(
    title="QuantBacktestEngine REST API",
    description="Standalone Backtesting, Strategy Management & Optimization Service",
    version=__version__
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repo = StrategyRepository()

class BacktestRequest(BaseModel):
    symbol: str = "SPY"
    cash: float = 100000.0
    commission: float = 0.0005
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strategy_spec: Optional[Union[Dict[str, Any], str]] = None
    parameters: Optional[Dict[str, Any]] = None

class StrategySaveRequest(BaseModel):
    name: str
    version: str
    spec: Dict[str, Any]
    description: Optional[str] = ""

class OptimizeRequest(BaseModel):
    symbol: str = "SPY"
    method: str = "optuna"
    n_trials: int = 20
    target_metric: str = "sharpe_ratio"
    strategy_spec: Union[Dict[str, Any], str]
    param_bounds: Dict[str, Any]

@app.get("/api/health")
def healthcheck():
    return {"status": "ok", "version": __version__}

@app.get("/api/strategies")
def list_strategies():
    return {"strategies": repo.list_strategies()}

@app.post("/api/strategies")
def save_strategy(req: StrategySaveRequest):
    row_id = repo.save_strategy(name=req.name, version=req.version, spec=req.spec, description=req.description or "")
    return {"status": "success", "id": row_id, "name": req.name, "version": req.version}

@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    try:
        spec = req.strategy_spec or {
            "name": "DefaultEMACross",
            "indicators": {
                "ema_fast": {"type": "EMA", "period": 10},
                "ema_slow": {"type": "EMA", "period": 30}
            },
            "rules": {"entry_long": "ema_fast > ema_slow"}
        }
        
        strategy_class = DeclarativeStrategyParser.parse_spec(spec)
        result = EngineRunner.run_backtest(
            strategy_class=strategy_class,
            source=req.symbol,
            symbol=req.symbol,
            cash=req.cash,
            commission=req.commission,
            start_date=req.start_date,
            end_date=req.end_date,
            strategy_params=req.parameters
        )
        
        spec_name = spec.get("name", "Strategy") if isinstance(spec, dict) else "DeclarativeStrategy"
        spec_ver = spec.get("version", "1.0.0") if isinstance(spec, dict) else "1.0.0"
        
        repo.save_run(
            strategy_name=spec_name,
            version=spec_ver,
            symbol=req.symbol,
            parameters=req.parameters or {},
            metrics=result.metrics
        )
        
        eq_list = []
        if isinstance(result.equity_curve, pd.Series):
            for ts, val in result.equity_curve.items():
                eq_list.append({"time": str(ts.date() if hasattr(ts, 'date') else ts), "value": float(val)})

        return {
            "symbol": req.symbol,
            "strategy_name": result.strategy_name,
            "metrics": result.metrics,
            "equity_curve": eq_list,
            "trade_count": len(result.trades)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/optimize")
def run_optimization(req: OptimizeRequest):
    try:
        strategy_class = DeclarativeStrategyParser.parse_spec(req.strategy_spec)
        
        if req.method.lower() == "optuna":
            opt_res = OptunaOptimizer.optimize(
                strategy_class=strategy_class,
                source=req.symbol,
                param_bounds=req.param_bounds,
                symbol=req.symbol,
                target_metric=req.target_metric,
                n_trials=req.n_trials
            )
            return {
                "method": "optuna",
                "best_params": opt_res["best_params"],
                "best_value": opt_res["best_value"],
                "best_metrics": opt_res["best_result"].metrics if opt_res["best_result"] else {}
            }
        else:
            grid_res = GridOptimizer.optimize(
                strategy_class=strategy_class,
                source=req.symbol,
                param_grid=req.param_bounds,
                symbol=req.symbol,
                target_metric=req.target_metric
            )
            return {
                "method": "grid",
                "best_params": grid_res["best_params"],
                "best_target_value": grid_res["best_target_value"]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
