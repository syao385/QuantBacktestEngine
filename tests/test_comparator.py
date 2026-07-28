import unittest
import pandas as pd
from quant_engine.core.runner import BacktestResult
from quant_engine.strategy.comparator import StrategyComparator

class TestStrategyComparator(unittest.TestCase):

    def test_compare_multiple_results(self):
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        eq1 = pd.Series([100, 102, 104, 103, 105, 107, 106, 108, 110, 112], index=dates)
        eq2 = pd.Series([100, 101, 101, 102, 102, 103, 103, 104, 104, 105], index=dates)

        res1 = BacktestResult(
            metrics={"cagr": 0.20, "sharpe_ratio": 1.8, "calmar_ratio": 2.5, "max_drawdown": -0.05},
            equity_curve=eq1,
            trades=pd.DataFrame(),
            symbol="SPY",
            strategy_name="GEX_Breakout",
            parameters={"version": "1.0.0"}
        )

        res2 = BacktestResult(
            metrics={"cagr": 0.10, "sharpe_ratio": 0.9, "calmar_ratio": 1.1, "max_drawdown": -0.08},
            equity_curve=eq2,
            trades=pd.DataFrame(),
            symbol="SPY",
            strategy_name="GEX_Breakout",
            parameters={"version": "1.1.0"}
        )

        comp = StrategyComparator.compare([res1, res2])
        self.assertEqual(comp["count"], 2)
        self.assertEqual(comp["best_sharpe"], "GEX_Breakout v1.0.0")
        self.assertEqual(comp["best_cagr"], "GEX_Breakout v1.0.0")
        self.assertIn("GEX_Breakout v1.0.0", comp["metrics_table"])
        self.assertIn("GEX_Breakout v1.1.0", comp["metrics_table"])

if __name__ == "__main__":
    unittest.main()
