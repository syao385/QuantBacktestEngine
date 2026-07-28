import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union
from quant_engine.core.runner import BacktestResult

class StrategyComparator:
    """
    Multi-Strategy & Version Comparison Engine for QuantBacktestEngine.
    Generates side-by-side metrics matrices, equity curve overlay series,
    and identifies top-performing strategy versions according to risk-adjusted return criteria.
    """

    @staticmethod
    def compare(
        results: List[Union[BacktestResult, Dict[str, Any]]],
        benchmark_name: str = "SPY"
    ) -> Dict[str, Any]:
        """
        Compares multiple BacktestResult objects or metric dictionaries.
        
        Returns:
            Dictionary containing:
            - 'metrics_table': pandas DataFrame / dict of side-by-side performance metrics.
            - 'equity_overlay': pandas DataFrame of aligned equity curves.
            - 'best_sharpe': Name/version of top Sharpe Ratio strategy.
            - 'best_cagr': Name/version of top CAGR strategy.
            - 'best_calmar': Name/version of top Calmar Ratio strategy.
        """
        if not results:
            return {"metrics_table": {}, "equity_overlay": {}, "best_sharpe": None}

        comparison_list = []
        equity_dict = {}

        for i, res in enumerate(results):
            if isinstance(res, BacktestResult):
                name = f"{res.strategy_name} ({res.symbol})" if res.strategy_name else f"Strategy_{i+1}"
                if res.parameters and "version" in res.parameters:
                    name = f"{res.strategy_name} v{res.parameters['version']}"
                
                metrics = res.metrics.copy()
                metrics["strategy_key"] = name
                metrics["symbol"] = res.symbol
                comparison_list.append(metrics)

                if not res.equity_curve.empty:
                    equity_dict[name] = res.equity_curve
            elif isinstance(res, dict):
                name = res.get("strategy_name", res.get("name", f"Strategy_{i+1}"))
                metrics = res.get("metrics", res).copy()
                metrics["strategy_key"] = name
                comparison_list.append(metrics)
                
                if "equity_curve" in res and isinstance(res["equity_curve"], pd.Series):
                    equity_dict[name] = res["equity_curve"]

        df_metrics = pd.DataFrame(comparison_list)
        if "strategy_key" in df_metrics.columns:
            df_metrics = df_metrics.set_index("strategy_key")

        # Combine equity curves into a single DataFrame if timestamps align
        df_equity = pd.DataFrame(equity_dict) if equity_dict else pd.DataFrame()
        if not df_equity.empty:
            df_equity = df_equity.ffill().bfill()

        # Identify top performers
        best_sharpe = df_metrics["sharpe_ratio"].idxmax() if "sharpe_ratio" in df_metrics.columns and not df_metrics.empty else None
        best_cagr = df_metrics["cagr"].idxmax() if "cagr" in df_metrics.columns and not df_metrics.empty else None
        best_calmar = df_metrics["calmar_ratio"].idxmax() if "calmar_ratio" in df_metrics.columns and not df_metrics.empty else None

        return {
            "metrics_table": df_metrics.to_dict(orient="index"),
            "metrics_df": df_metrics,
            "equity_overlay": df_equity,
            "best_sharpe": best_sharpe,
            "best_cagr": best_cagr,
            "best_calmar": best_calmar,
            "count": len(results)
        }
