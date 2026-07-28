import pandas as pd
import numpy as np
import logging
from backtesting import Backtest
from typing import Dict, Any, Type, Optional, Union
from quant_engine.core.data import DataLoader
from quant_engine.core.metrics import MetricsCalculator

logger = logging.getLogger(__name__)

class BacktestResult:
    """Dataclass holding structured output of a backtest execution."""
    def __init__(
        self,
        metrics: Dict[str, Any],
        equity_curve: pd.Series,
        trades: pd.DataFrame,
        symbol: str,
        strategy_name: str,
        parameters: Dict[str, Any]
    ):
        self.metrics = metrics
        self.equity_curve = equity_curve
        self.trades = trades
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy_name": self.strategy_name,
            "parameters": self.parameters,
            "metrics": self.metrics,
            "trade_count": len(self.trades) if not self.trades.empty else 0
        }

class EngineRunner:
    """
    Core Execution Engine Runner for QuantBacktestEngine.
    Wraps backtesting.Backtest for fast bar processing, risk sizer evaluation,
    and standardized metric compilation.
    """

    @staticmethod
    def run_backtest(
        strategy_class: Type,
        source: Union[str, pd.DataFrame],
        symbol: str = "SPY",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cash: float = 100000.0,
        commission: float = 0.0005, # 0.05% commission
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> BacktestResult:
        """
        Executes backtest for a strategy class against specified data.
        
        Args:
            strategy_class: Class inheriting from QuantStrategy or backtesting.Strategy.
            source: Symbol name, file path, or pandas DataFrame.
            symbol: Ticker symbol string.
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            cash: Initial portfolio equity (default: $100,000)
            commission: Transaction fee fraction (default: 0.05%)
            strategy_params: Dictionary of parameters to override on strategy.
            
        Returns:
            BacktestResult object containing equity curve, trade log, metrics.
        """
        params = strategy_params or {}

        # 1. Load and format OHLCV data
        df = DataLoader.load_data(source=source, symbol=symbol, start_date=start_date, end_date=end_date)
        
        if len(df) < 20:
            raise ValueError(f"Insufficient data bars ({len(df)}) to execute backtest for {symbol}")

        # 2. Configure strategy parameter overrides
        for k, v in params.items():
            if hasattr(strategy_class, k):
                setattr(strategy_class, k, v)

        # 3. Instantiate and run backtesting.Backtest with finalize_trades=True
        bt = Backtest(
            df,
            strategy_class,
            cash=cash,
            commission=commission,
            exclusive_orders=True,
            finalize_trades=True
        )

        stats = bt.run(**params)

        # 4. Extract equity curve and trade logs
        equity_series = stats.get('_equity_curve', pd.DataFrame())
        if not equity_series.empty and 'Equity' in equity_series.columns:
            equity_curve = equity_series['Equity']
        else:
            equity_curve = pd.Series([cash] * len(df), index=df.index)

        raw_trades = stats.get('_trades', pd.DataFrame())
        trades_df = pd.DataFrame()
        if not raw_trades.empty:
            trades_df = raw_trades.copy()
            if 'PnL' in trades_df.columns:
                trades_df['pnl'] = trades_df['PnL']

        # 5. Compute quantitative metrics suite
        metrics = MetricsCalculator.calculate_metrics(
            equity_curve=equity_curve,
            trades=trades_df
        )

        return BacktestResult(
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades_df,
            symbol=symbol,
            strategy_name=strategy_class.__name__,
            parameters=params
        )
