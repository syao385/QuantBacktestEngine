import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple

class TrailingStopEngine:
    """
    State-of-the-Art Multi-Stage Trailing Stop Engine for QuantBacktestEngine.
    Implements dynamic ratchet mechanics bar-by-bar:
    - Initial Hard Stop (ATR / % offset)
    - Break-Even Ratchet (moves stop loss to entry at +1.0R or specified profit trigger)
    - Chandelier High-Water Mark Trailing (highest high since entry minus K * ATR)
    - Multi-Tier Profit Lock Tightening (tightens trailing offset as trade hits +2R, +3R)
    - Time-Decay Stale Trade Exit (closes trade after N flat bars)
    """

    def __init__(
        self,
        stop_type: str = "chandelier_ratchet",
        atr_multiplier: float = 3.0,
        breakeven_trigger_r: float = 1.0,
        profit_lock_tiers: Optional[List[Dict[str, float]]] = None,
        max_bars_in_trade: Optional[int] = None
    ):
        """
        Args:
            stop_type: 'chandelier_ratchet', 'atr_trailing', or 'fixed_pct'
            atr_multiplier: Base ATR multiplier for trailing stop (default: 3.0)
            breakeven_trigger_r: R-multiple profit trigger to move stop to breakeven (default: +1.0R)
            profit_lock_tiers: List of tier dicts e.g. [{'r_multiple': 2.0, 'atr_multiplier': 2.0}, {'r_multiple': 3.0, 'atr_multiplier': 1.5}]
            max_bars_in_trade: Maximum bars to hold a stagnant position before time-decay exit
        """
        self.stop_type = stop_type.lower()
        self.base_atr_multiplier = atr_multiplier
        self.breakeven_trigger_r = breakeven_trigger_r
        self.profit_lock_tiers = profit_lock_tiers or [
            {"r_multiple": 2.0, "atr_multiplier": 2.0},
            {"r_multiple": 3.0, "atr_multiplier": 1.5}
        ]
        # Sort tiers by r_multiple ascending
        self.profit_lock_tiers.sort(key=lambda x: x.get("r_multiple", 0.0))
        self.max_bars_in_trade = max_bars_in_trade

        # State variables per trade
        self.reset()

    def reset(self):
        """Resets engine state for a new trade entry."""
        self.entry_price: float = 0.0
        self.initial_risk_r: float = 0.0
        self.current_stop: float = 0.0
        self.peak_price: float = 0.0
        self.bars_in_trade: int = 0
        self.stage: int = 0  # 0: Initial, 1: Break-even, 2+: Tiered Profit Locks
        self.is_active: bool = False
        self.is_long: bool = True

    def initialize_trade(
        self,
        entry_price: float,
        is_long: bool = True,
        initial_stop: Optional[float] = None,
        atr: Optional[float] = None
    ) -> float:
        """
        Initializes trailing stop state for a newly entered position.
        
        Returns:
            Initial stop loss price.
        """
        self.reset()
        self.entry_price = entry_price
        self.is_long = is_long
        self.is_active = True
        self.peak_price = entry_price
        self.bars_in_trade = 0

        if initial_stop is not None and initial_stop > 0:
            self.current_stop = initial_stop
            self.initial_risk_r = abs(entry_price - initial_stop)
        elif atr is not None and atr > 0:
            self.initial_risk_r = atr * self.base_atr_multiplier
            self.current_stop = entry_price - self.initial_risk_r if is_long else entry_price + self.initial_risk_r
        else:
            # Fallback 2% stop loss
            self.initial_risk_r = entry_price * 0.02
            self.current_stop = entry_price * 0.98 if is_long else entry_price * 1.02

        if self.initial_risk_r <= 0:
            self.initial_risk_r = entry_price * 0.01

        return self.current_stop

    def update_bar(
        self,
        high: float,
        low: float,
        close: float,
        atr: Optional[float] = None
    ) -> Tuple[float, bool, str]:
        """
        Updates trailing stop ratchet state on each new bar.
        
        Returns:
            Tuple of (updated_stop_price, should_exit_trade, exit_reason)
        """
        if not self.is_active:
            return 0.0, False, ""

        self.bars_in_trade += 1

        # 1. Update High-Water Mark peak price
        if self.is_long:
            if high > self.peak_price:
                self.peak_price = high
            unrealized_profit = self.peak_price - self.entry_price
        else:
            if low < self.peak_price or self.peak_price == 0:
                self.peak_price = low
            unrealized_profit = self.entry_price - self.peak_price

        current_r = unrealized_profit / (self.initial_risk_r + 1e-9)

        # 2. Check for Time Decay / Stale Trade Exit
        if self.max_bars_in_trade is not None and self.bars_in_trade >= self.max_bars_in_trade:
            if current_r < self.breakeven_trigger_r:
                return self.current_stop, True, "time_decay_exit"

        # 3. Determine active ATR multiplier based on profit tiers
        active_multiplier = self.base_atr_multiplier
        for tier in self.profit_lock_tiers:
            if current_r >= tier.get("r_multiple", 999.0):
                active_multiplier = tier.get("atr_multiplier", active_multiplier)
                self.stage = max(self.stage, 2)

        # 4. Check for Break-Even Ratchet stage
        if current_r >= self.breakeven_trigger_r and self.stage < 1:
            self.stage = 1
            if self.is_long:
                self.current_stop = max(self.current_stop, self.entry_price)
            else:
                self.current_stop = min(self.current_stop, self.entry_price)

        # 5. Calculate Chandelier Trailing Stop update
        curr_atr = atr if atr is not None and atr > 0 else (self.initial_risk_r / self.base_atr_multiplier)

        if self.is_long:
            new_stop = self.peak_price - (curr_atr * active_multiplier)
            # Stop loss only moves up, never down!
            if new_stop > self.current_stop:
                self.current_stop = new_stop

            # Check if current bar triggered stop loss
            if low <= self.current_stop:
                self.is_active = False
                return self.current_stop, True, f"trailing_stop_hit_stage_{self.stage}"
        else:
            new_stop = self.peak_price + (curr_atr * active_multiplier)
            # Stop loss only moves down for shorts
            if new_stop < self.current_stop or self.current_stop == 0:
                self.current_stop = new_stop

            if high >= self.current_stop:
                self.is_active = False
                return self.current_stop, True, f"trailing_stop_hit_stage_{self.stage}"

        return self.current_stop, False, ""
