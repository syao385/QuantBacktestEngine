import unittest
from quant_engine.risk.sizer import PositionSizer

class TestPositionSizer(unittest.TestCase):

    def test_atr_risk_sizing(self):
        sizer = PositionSizer(sizing_type="atr_risk", risk_pct=0.02, atr_multiplier=2.0, max_position_pct=0.50)
        equity = 100000.0
        price = 100.0
        atr = 2.50 # Stop distance = 2.5 * 2.0 = 5.0
        # Risk amount = 100000 * 0.02 = 2000
        # Expected shares = 2000 / 5.0 = 400 shares
        
        shares = sizer.calculate_shares(equity=equity, price=price, atr=atr)
        self.assertAlmostEqual(shares, 400.0, places=2)

    def test_fractional_kelly_sizing(self):
        sizer = PositionSizer(sizing_type="fractional_kelly", kelly_fraction=0.50, max_position_pct=0.25)
        equity = 100000.0
        price = 50.0
        # Win rate 60%, Win/Loss ratio 2.0 -> Full Kelly = 0.6 - 0.4 / 2.0 = 0.4 (40%)
        # Half Kelly = 20% allocation -> $20,000 -> 400 shares
        shares = sizer.calculate_shares(equity=equity, price=price, win_rate=0.60, win_loss_ratio=2.0)
        self.assertAlmostEqual(shares, 400.0, places=2)

    def test_drawdown_guard(self):
        sizer = PositionSizer(
            sizing_type="atr_risk",
            risk_pct=0.02,
            atr_multiplier=2.0,
            drawdown_guard=True,
            drawdown_threshold=0.10, # 10% DD threshold
            drawdown_penalty=0.50   # 50% penalty
        )
        peak_equity = 100000.0
        current_equity = 88000.0 # 12% drawdown -> triggers penalty
        price = 100.0
        atr = 2.0 # stop dist = 4.0
        
        # Risk amount = 88000 * (0.02 * 0.5) = 880
        # Expected shares = 880 / 4.0 = 220 shares
        shares = sizer.calculate_shares(equity=current_equity, price=price, atr=atr, peak_equity=peak_equity)
        self.assertAlmostEqual(shares, 220.0, places=2)

if __name__ == "__main__":
    unittest.main()
