import numpy as np
import pandas as pd
from backtesting import Strategy
from typing import Dict, Any, Optional
from quant_engine.risk.sizer import PositionSizer
from quant_engine.risk.trailing_stop import TrailingStopEngine

class QuantStrategy(Strategy):
    """
    Base Strategy for QuantBacktestEngine extending backtesting.Strategy.
    Integrates institutional PositionSizer and multi-stage TrailingStopEngine.
    """
    
    # Class attributes (overridden by child strategies or optimizer)
    sizer_type: str = "atr_risk"
    risk_pct: float = 0.015
    atr_multiplier: float = 3.0
    atr_period: int = 14
    breakeven_trigger_r: float = 1.0
    drawdown_guard: bool = True
    max_position_pct: float = 0.25
    
    def init(self):
        """Initializes indicators, position sizer, and trailing stop state."""
        # 1. Compute ATR indicator
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        close = pd.Series(self.data.Close)
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        self.atr = self.I(lambda: tr.ewm(span=self.atr_period, adjust=False).mean().to_numpy(), name="ATR")
        
        # 2. Instantiate Position Sizer and Trailing Stop Engine
        self.sizer = PositionSizer(
            sizing_type=self.sizer_type,
            risk_pct=self.risk_pct,
            atr_multiplier=self.atr_multiplier,
            max_position_pct=self.max_position_pct,
            drawdown_guard=self.drawdown_guard
        )
        
        self.trailing_engine = TrailingStopEngine(
            atr_multiplier=self.atr_multiplier,
            breakeven_trigger_r=self.breakeven_trigger_r
        )
        
        self.peak_equity = float(self.equity)

    def next(self):
        """Called bar-by-bar during backtesting execution."""
        current_equity = float(self.equity)
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        curr_close = self.data.Close[-1]
        curr_high = self.data.High[-1]
        curr_low = self.data.Low[-1]
        curr_atr = self.atr[-1] if len(self.atr) > 0 and not np.isnan(self.atr[-1]) else curr_close * 0.01

        # 1. Manage active position trailing stop
        if self.position:
            stop_price, exit_trade, reason = self.trailing_engine.update_bar(
                high=curr_high,
                low=curr_low,
                close=curr_close,
                atr=curr_atr
            )
            
            if exit_trade:
                self.position.close()
                self.trailing_engine.reset()
                return

        # 2. Subclasses implement custom signal logic in on_bar()
        self.on_bar()

    def on_bar(self):
        """Override this method in concrete strategy subclasses to define trade entry signals."""
        pass

    def enter_long(self, sl: Optional[float] = None):
        """Enters long position with dynamic position sizing and trailing stop initialization."""
        if self.position:
            return

        curr_close = self.data.Close[-1]
        curr_atr = self.atr[-1] if len(self.atr) > 0 and not np.isnan(self.atr[-1]) else curr_close * 0.01

        shares = self.sizer.calculate_shares(
            equity=float(self.equity),
            price=curr_close,
            atr=curr_atr,
            peak_equity=self.peak_equity
        )

        if shares <= 0:
            # Fallback to at least 1 share if account capital allows
            shares = 1.0 if float(self.equity) >= curr_close else 0.0

        if shares <= 0:
            return

        initial_stop = sl if sl is not None else (curr_close - (curr_atr * self.atr_multiplier))
        self.trailing_engine.initialize_trade(
            entry_price=curr_close,
            is_long=True,
            initial_stop=initial_stop,
            atr=curr_atr
        )

        # Calculate share count integer or equity fraction
        if shares >= 1.0:
            order_size = int(shares)
        else:
            order_size = min((shares * curr_close) / float(self.equity), 0.95)

        if order_size > 0:
            self.buy(size=order_size)
