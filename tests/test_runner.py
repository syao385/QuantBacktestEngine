import unittest
import pandas as pd
import numpy as np
from quant_engine.strategy.base import QuantStrategy
from quant_engine.core.runner import EngineRunner

class MovingAverageCrossStrategy(QuantStrategy):
    """Simple Moving Average Crossover strategy extending QuantStrategy for testing."""
    fast_period = 5
    slow_period = 15

    def init(self):
        super().init()
        close = pd.Series(self.data.Close)
        self.fast_ma = self.I(lambda: close.rolling(self.fast_period).mean().to_numpy(), name="FastMA")
        self.slow_ma = self.I(lambda: close.rolling(self.slow_period).mean().to_numpy(), name="SlowMA")

    def on_bar(self):
        if len(self.fast_ma) < 2 or len(self.slow_ma) < 2:
            return
            
        # Bullish crossover: Fast MA crosses above Slow MA
        if self.fast_ma[-2] <= self.slow_ma[-2] and self.fast_ma[-1] > self.slow_ma[-1]:
            self.enter_long()

class TestEngineRunner(unittest.TestCase):

    def setUp(self):
        # Generate 100 days of trending synthetic OHLCV data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        price = 100.0 + np.cumsum(np.random.normal(0.2, 1.0, 100))
        
        self.df = pd.DataFrame({
            "Open": price - 0.2,
            "High": price + 1.0,
            "Low": price - 1.0,
            "Close": price,
            "Volume": 10000.0
        }, index=dates)

    def test_runner_execution(self):
        result = EngineRunner.run_backtest(
            strategy_class=MovingAverageCrossStrategy,
            source=self.df,
            symbol="TEST",
            cash=100000.0
        )
        
        self.assertEqual(result.symbol, "TEST")
        self.assertEqual(result.strategy_name, "MovingAverageCrossStrategy")
        self.assertIn("cagr", result.metrics)
        self.assertIn("sharpe_ratio", result.metrics)
        self.assertGreater(len(result.equity_curve), 0)

if __name__ == "__main__":
    unittest.main()
