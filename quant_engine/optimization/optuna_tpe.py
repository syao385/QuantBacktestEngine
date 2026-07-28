import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Type, Union, Optional
from quant_engine.core.runner import EngineRunner, BacktestResult

# Suppress verbose Optuna logs by default
optuna.logging.set_verbosity(optuna.logging.WARNING)

class OptunaOptimizer:
    """
    Optuna Bayesian Optimization Engine for QuantBacktestEngine.
    Uses Tree-structured Parzen Estimator (TPE) sampling with Median Pruning
    for continuous & high-dimensional strategy hyperparameter optimization.
    """

    @staticmethod
    def optimize(
        strategy_class: Type,
        source: Union[str, pd.DataFrame],
        param_bounds: Dict[str, Tuple[Union[int, float], Union[int, float]]],
        symbol: str = "SPY",
        target_metric: str = "sharpe_ratio",
        n_trials: int = 30,
        cash: float = 100000.0,
        commission: float = 0.0005
    ) -> Dict[str, Any]:
        """
        Executes Optuna TPE Bayesian optimization.
        
        Args:
            strategy_class: Target QuantStrategy.
            source: Data source.
            param_bounds: Dict specifying bounds e.g. {'fast_period': (3, 20), 'atr_multiplier': (1.5, 4.5)}
            symbol: Ticker symbol.
            target_metric: Objective function to maximize ('sharpe_ratio', 'cagr', 'calmar_ratio', 'sqn').
            n_trials: Number of Bayesian trials to execute (default: 30).
            
        Returns:
            Dictionary containing best_params, best_value, trials_df, and optuna_study object.
        """
        def objective(trial: optuna.Trial) -> float:
            p_dict = {}
            for param_name, bounds in param_bounds.items():
                low, high = bounds[0], bounds[1]
                if isinstance(low, int) and isinstance(high, int):
                    p_dict[param_name] = trial.suggest_int(param_name, low, high)
                else:
                    p_dict[param_name] = trial.suggest_float(param_name, float(low), float(high))

            try:
                res = EngineRunner.run_backtest(
                    strategy_class=strategy_class,
                    source=source,
                    symbol=symbol,
                    cash=cash,
                    commission=commission,
                    strategy_params=p_dict
                )
                val = float(res.metrics.get(target_metric, -999999.0))
                if np.isnan(val) or np.isinf(val):
                    return -999999.0
                return val
            except Exception:
                return -999999.0

        study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=n_trials)

        best_params = study.best_params
        best_value = study.best_value

        # Run final backtest with best parameters to get full BacktestResult
        best_result = EngineRunner.run_backtest(
            strategy_class=strategy_class,
            source=source,
            symbol=symbol,
            cash=cash,
            commission=commission,
            strategy_params=best_params
        )

        trials_df = study.trials_dataframe()

        return {
            "best_params": best_params,
            "best_value": best_value,
            "best_result": best_result,
            "trials_df": trials_df,
            "n_trials": n_trials,
            "study": study
        }
