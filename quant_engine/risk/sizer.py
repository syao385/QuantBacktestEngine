import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class PositionSizer:
    """
    Institutional Position Sizing Engine for QuantBacktestEngine.
    Calculates share count / contract sizing using proven quantitative models:
    - ATR Volatility Risk Sizing
    - Fractional Kelly Criterion
    - Volatility Parity
    - Fixed Percent / Fixed Risk
    - Equity Drawdown Regime Guard
    """

    def __init__(
        self,
        sizing_type: str = "atr_risk",
        risk_pct: float = 0.015,
        atr_multiplier: float = 2.0,
        kelly_fraction: float = 0.5,
        max_position_pct: float = 0.25,
        drawdown_guard: bool = True,
        drawdown_threshold: float = 0.10,
        drawdown_penalty: float = 0.50
    ):
        """
        Args:
            sizing_type: 'atr_risk', 'fractional_kelly', 'volatility_parity', or 'fixed_pct'
            risk_pct: Account risk % per trade (e.g. 0.015 = 1.5% of total equity)
            atr_multiplier: ATR multiplier distance to stop loss (default: 2.0)
            kelly_fraction: Kelly fraction scale factor (e.g., 0.5 = Half-Kelly, 0.25 = Quarter-Kelly)
            max_position_pct: Max portfolio equity fraction allocated to a single position (default: 25%)
            drawdown_guard: Enable automatic risk reduction during drawdown regimes
            drawdown_threshold: Equity drawdown threshold triggering risk reduction (e.g. 0.10 = -10%)
            drawdown_penalty: Risk multiplier applied during drawdown regime (e.g. 0.50 = 50% risk cap)
        """
        self.sizing_type = sizing_type.lower()
        self.risk_pct = risk_pct
        self.atr_multiplier = atr_multiplier
        self.kelly_fraction = kelly_fraction
        self.max_position_pct = max_position_pct
        self.drawdown_guard = drawdown_guard
        self.drawdown_threshold = drawdown_threshold
        self.drawdown_penalty = drawdown_penalty

    def calculate_shares(
        self,
        equity: float,
        price: float,
        atr: Optional[float] = None,
        peak_equity: Optional[float] = None,
        win_rate: Optional[float] = 0.50,
        win_loss_ratio: Optional[float] = 1.5,
        asset_volatility: Optional[float] = 0.20,
        target_portfolio_vol: Optional[float] = 0.15
    ) -> float:
        """
        Calculates recommended share count based on active sizing model and equity guardrails.
        """
        if equity <= 0 or price <= 0:
            return 0.0

        # 1. Apply Equity Drawdown Guard penalty if applicable
        effective_risk_pct = self.risk_pct
        if self.drawdown_guard and peak_equity is not None and peak_equity > 0:
            current_drawdown = (peak_equity - equity) / peak_equity
            if current_drawdown >= self.drawdown_threshold:
                effective_risk_pct *= self.drawdown_penalty

        raw_shares = 0.0

        # 2. Sizing Methodology Execution
        if self.sizing_type == "atr_risk":
            if atr is None or atr <= 0:
                # Fallback to 2% price distance if ATR not supplied
                stop_distance = price * 0.02
            else:
                stop_distance = atr * self.atr_multiplier
                
            risk_amount = equity * effective_risk_pct
            raw_shares = risk_amount / (stop_distance + 1e-9)

        elif self.sizing_type == "fractional_kelly":
            # Kelly formula: f* = p - (1 - p) / b
            p = win_rate if win_rate is not None else 0.50
            b = win_loss_ratio if win_loss_ratio is not None and win_loss_ratio > 0 else 1.0
            
            kelly_pct = p - (1.0 - p) / b
            if kelly_pct <= 0:
                return 0.0
                
            allocation_pct = min(kelly_pct * self.kelly_fraction, self.max_position_pct)
            if self.drawdown_guard and peak_equity is not None and peak_equity > 0:
                current_drawdown = (peak_equity - equity) / peak_equity
                if current_drawdown >= self.drawdown_threshold:
                    allocation_pct *= self.drawdown_penalty

            dollar_allocation = equity * allocation_pct
            raw_shares = dollar_allocation / price

        elif self.sizing_type == "volatility_parity":
            vol = asset_volatility if asset_volatility is not None and asset_volatility > 0 else 0.20
            target_vol = target_portfolio_vol if target_portfolio_vol is not None else 0.15
            
            vol_scale = target_vol / (vol + 1e-9)
            allocation_pct = min(vol_scale * effective_risk_pct * 10, self.max_position_pct)
            dollar_allocation = equity * allocation_pct
            raw_shares = dollar_allocation / price

        elif self.sizing_type == "fixed_pct":
            dollar_allocation = equity * effective_risk_pct
            raw_shares = dollar_allocation / price

        else:
            # Default fallback
            dollar_allocation = equity * 0.05
            raw_shares = dollar_allocation / price

        # 3. Apply Max Position Cap (Never allocate more than max_position_pct of total equity to a single trade)
        max_dollar = equity * self.max_position_pct
        max_allowed_shares = max_dollar / price
        
        final_shares = min(raw_shares, max_allowed_shares)
        return max(float(final_shares), 0.0)
