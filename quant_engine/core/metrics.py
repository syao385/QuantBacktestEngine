import numpy as np
import pandas as pd
from typing import Dict, Any, Union

class MetricsCalculator:
    """
    Comprehensive Quantitative Performance Metrics Calculator.
    Calculates CAGR, Sharpe Ratio, Sortino Ratio, Calmar Ratio, SQN, Profit Factor,
    Max Drawdown, Win Rate, and Exposure Time for trade logs and equity curves.
    """
    
    @staticmethod
    def calculate_metrics(
        equity_curve: Union[pd.Series, np.ndarray, list],
        trades: Union[pd.DataFrame, list] = None,
        risk_free_rate: float = 0.04,
        periods_per_year: int = 252
    ) -> Dict[str, Any]:
        """
        Calculates full suite of quantitative backtest metrics.
        
        Args:
            equity_curve: Series or array of portfolio equity values over time.
            trades: DataFrame or list of executed trade dicts.
            risk_free_rate: Annualized risk-free interest rate (default: 4.0%).
            periods_per_year: Trading days per year (252 for daily, 252*6.5 for intraday 1h).
            
        Returns:
            Dictionary containing computed risk-adjusted metrics.
        """
        eq = pd.Series(equity_curve, dtype=float).dropna()
        if len(eq) < 2:
            return MetricsCalculator._empty_metrics()

        start_equity = eq.iloc[0]
        final_equity = eq.iloc[-1]
        total_return = (final_equity - start_equity) / start_equity

        # Returns calculation
        returns = eq.pct_change().dropna()
        
        # Duration in years
        num_periods = len(eq)
        years = max(num_periods / periods_per_year, 1.0 / periods_per_year)

        # 1. Compound Annual Growth Rate (CAGR)
        cagr = (final_equity / start_equity) ** (1.0 / years) - 1.0 if final_equity > 0 else -1.0

        # 2. Drawdown & Max Drawdown
        running_max = eq.cummax()
        drawdowns = (eq - running_max) / running_max
        max_drawdown = float(drawdowns.min()) # Negative value e.g. -0.15 for -15%

        # 3. Volatility (Annualized)
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / periods_per_year) - 1.0
        excess_returns = returns - daily_rf
        ann_vol = float(returns.std() * np.sqrt(periods_per_year))

        # 4. Sharpe Ratio
        sharpe_ratio = 0.0
        if ann_vol > 1e-9:
            sharpe_ratio = float((returns.mean() - daily_rf) / (returns.std() + 1e-9) * np.sqrt(periods_per_year))

        # 5. Sortino Ratio (Downside Volatility)
        sortino_ratio = 0.0
        downside_returns = returns[returns < daily_rf] - daily_rf
        downside_std = float(downside_returns.std() * np.sqrt(periods_per_year))
        if downside_std > 1e-9:
            sortino_ratio = float((returns.mean() - daily_rf) * np.sqrt(periods_per_year) / (downside_std + 1e-9))

        # 6. Calmar Ratio
        calmar_ratio = 0.0
        if abs(max_drawdown) > 1e-9:
            calmar_ratio = float(cagr / abs(max_drawdown))

        # Trade Log Metrics
        trade_count = 0
        win_rate = 0.0
        profit_factor = 0.0
        sqn = 0.0
        avg_trade_pnl = 0.0

        if trades is not None and len(trades) > 0:
            if isinstance(trades, list):
                trade_df = pd.DataFrame(trades)
            else:
                trade_df = trades.copy()

            if not trade_df.empty and 'pnl' in trade_df.columns:
                trade_count = len(trade_df)
                pnls = trade_df['pnl'].dropna()
                wins = pnls[pnls > 0]
                losses = pnls[pnls < 0]

                if trade_count > 0:
                    win_rate = float(len(wins) / trade_count)
                    avg_trade_pnl = float(pnls.mean())

                gross_profit = float(wins.sum()) if not wins.empty else 0.0
                gross_loss = float(abs(losses.sum())) if not losses.empty else 0.0

                if gross_loss > 1e-9:
                    profit_factor = gross_profit / gross_loss
                else:
                    profit_factor = 999.0 if gross_profit > 0 else 0.0

                # 7. System Quality Number (SQN) by Van Tharp: sqrt(N) * mean(pnl) / std(pnl)
                if trade_count > 1 and pnls.std() > 1e-9:
                    sqn = float(np.sqrt(trade_count) * pnls.mean() / (pnls.std() + 1e-9))

        return {
            "start_equity": float(start_equity),
            "final_equity": float(final_equity),
            "total_return": float(total_return),
            "cagr": float(cagr),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "calmar_ratio": float(calmar_ratio),
            "max_drawdown": float(max_drawdown),
            "volatility": float(ann_vol),
            "trade_count": int(trade_count),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "sqn": float(sqn),
            "avg_trade_pnl": float(avg_trade_pnl)
        }

    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        return {
            "start_equity": 0.0,
            "final_equity": 0.0,
            "total_return": 0.0,
            "cagr": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "trade_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "sqn": 0.0,
            "avg_trade_pnl": 0.0
        }
