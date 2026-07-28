import unittest
import pandas as pd
import numpy as np
from quant_engine.strategy.base import QuantStrategy
from quant_engine.optimization.grid import GridOptimizer
from quant_engine.optimization.optuna_tpe import OptunaOptimizer

class TestStrategyForOptimization(QuantStrategy):
    fast_period = 5
    slow_period = 15

    def init(self):
        super().init()
        close = pd.Series(self.data.Close)
        self.fast_ma = self.I(lambda: close.rolling(int(self.fast_period)).mean().to_numpy(), name="FastMA")
        self.slow_ma = self.I(lambda: close.rolling(int(self.slow_period)).mean().to_numpy(), name="SlowMA")

    def on_bar(self):
        if len(self.fast_ma) < 2 or len(self.slow_ma) < 2:
            return
        if self.fast_ma[-2] <= self.slow_ma[-2] and self.fast_ma[-1] > self.slow_ma[-1]:
            self.enter_long()

class TestOptimizer(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range("2023-01-01", periods=60, freq="D")
        np.random.seed(42)
        price = 100.0 + np.cumsum(np.random.normal(0.1, 0.5, 60))
        self.df = pd.DataFrame({
            "Open": price,
            "High": price + 0.5,
            "Low": price - 0.5,
            "Close": price,
            "Volume": 1000.0
        }, index=dates)

    def test_grid_optimizer(self):
        param_grid = {
            "fast_period": [3, 5],
            "slow_period": [10, 15]
        }
        res = GridOptimizer.optimize(
            strategy_class=TestStrategyForOptimization,
            source=self.df,
            param_grid=param_grid,
            symbol="TEST"
        )
        
        self.assertIn("fast_period", res["best_params"])
        self.assertIn("slow_period", res["best_params"])
        self.assertEqual(res["total_trials"], 4)

    def test_optuna_optimizer(self):
        param_bounds = {
            "fast_period": (3, 7),
            "slow_period": (10, 20)
        }
        res = OptunaOptimizer.optimize(
            strategy_class=TestStrategyForOptimization,
            source=self.df,
            param_bounds=param_bounds,
            symbol="TEST",
            n_trials=10
        )
        
        self.assertIn("fast_period", res["best_params"])
        self.assertIn("slow_period", res["best_params"])
        self.assertEqual(res["n_trials"], 10)
        self.assertIsNotNone(res["best_result"])

if __name__ == "__main__":
    unittest.main()
