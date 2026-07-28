import unittest
from quant_engine.risk.trailing_stop import TrailingStopEngine

class TestTrailingStopEngine(unittest.TestCase):

    def test_initial_stop_and_breakeven_ratchet(self):
        engine = TrailingStopEngine(
            atr_multiplier=2.0,
            breakeven_trigger_r=1.0,
            profit_lock_tiers=[{"r_multiple": 2.0, "atr_multiplier": 1.5}]
        )
        
        # Entry at $100, initial stop at $96 (R = $4)
        init_stop = engine.initialize_trade(entry_price=100.0, is_long=True, initial_stop=96.0)
        self.assertEqual(init_stop, 96.0)
        self.assertEqual(engine.stage, 0)
        
        # Bar 1: Price rises to High=103.5 (Profit = 3.5, < 1.0R (4.0)), Low=101.0
        stop, exited, reason = engine.update_bar(high=103.5, low=101.0, close=103.0, atr=2.0)
        self.assertFalse(exited)
        self.assertEqual(engine.stage, 0)
        
        # Bar 2: Price reaches High=105.0 (+1.25R -> triggers Break-Even Ratchet!)
        stop, exited, reason = engine.update_bar(high=105.0, low=102.0, close=104.0, atr=2.0)
        self.assertFalse(exited)
        self.assertGreaterEqual(engine.stage, 1)
        self.assertGreaterEqual(stop, 100.0) # Stop moved to at least entry!

    def test_tiered_profit_lock_tightening(self):
        engine = TrailingStopEngine(
            atr_multiplier=3.0,
            breakeven_trigger_r=1.0,
            profit_lock_tiers=[{"r_multiple": 2.0, "atr_multiplier": 1.5}]
        )
        # Entry at 100, Initial stop at 95 (R = 5.0)
        engine.initialize_trade(entry_price=100.0, is_long=True, initial_stop=95.0)
        
        # Rally to 112 (Low=110.0) (+2.4R profit -> triggers 1.5 ATR trailing tier!)
        stop, exited, reason = engine.update_bar(high=112.0, low=110.0, close=111.0, atr=2.0)
        self.assertFalse(exited)
        self.assertEqual(engine.stage, 2)
        # Expected trailing stop: Peak(112) - 1.5*2.0 = 109.0
        self.assertAlmostEqual(stop, 109.0, places=2)
        
        # Next bar pulls back to Low=108.5 (below 109.0 stop -> triggers exit!)
        stop, exited, reason = engine.update_bar(high=110.0, low=108.5, close=108.5, atr=2.0)
        self.assertTrue(exited)
        self.assertIn("trailing_stop_hit", reason)

if __name__ == "__main__":
    unittest.main()
