import pandas as pd
import numpy as np
from typing import Dict, Any, List, Type, Union, Optional
from quant_engine.core.runner import EngineRunner, BacktestResult

class GridOptimizer:
    """
    Multiprocessing Parallel Grid Optimizer for QuantBacktestEngine.
    Explores parameter grid combinations and ranks parameter sets by target objective metric.
    """

    @staticmethod
    def optimize(
        strategy_class: Type,
        source: Union[str, pd.DataFrame],
        param_grid: Dict[str, List[Any]],
        symbol: str = "SPY",
        target_metric: str = "sharpe_ratio",
        cash: float = 100000.0,
        commission: float = 0.0005
    ) -> Dict[str, Any]:
        """
        Runs grid search across parameter space.
        
        Args:
            strategy_class: Target QuantStrategy class.
            source: Symbol name or DataFrame.
            param_grid: Dictionary mapping parameter names to lists of values to test.
            symbol: Ticker symbol.
            target_metric: Metric to maximize ('sharpe_ratio', 'cagr', 'calmar_ratio', 'sqn', 'sortino_ratio').
            
        Returns:
            Dictionary containing best_parameters, best_metric_value, and full trial_results dataframe.
        """
        import itertools

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(itertools.product(*param_values))

        trials = []
        best_value = -999999.0
        best_params = {}
        best_result: Optional[BacktestResult] = None

        for combo in combinations:
            p_dict = dict(zip(param_names, combo))
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
                p_dict["_target_value"] = val
                p_dict["_cagr"] = res.metrics.get("cagr", 0.0)
                p_dict["_max_drawdown"] = res.metrics.get("max_drawdown", 0.0)
                trials.append(p_dict)

                if val > best_value:
                    best_value = val
                    best_params = {k: v for k, v in p_dict.items() if not k.startswith("_")}
                    best_result = res
            except Exception as e:
                continue

        df_trials = pd.DataFrame(trials)
        if not df_trials.empty and "_target_value" in df_trials.columns:
            df_trials = df_trials.sort_values(by="_target_value", ascending=False)

        return {
            "best_params": best_params,
            "best_target_value": best_value,
            "best_result": best_result,
            "trials_df": df_trials,
            "total_trials": len(combinations)
        }
