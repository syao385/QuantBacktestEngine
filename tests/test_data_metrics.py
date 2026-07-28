import unittest
import pandas as pd
import numpy as np
from quant_engine.core.data import DataLoader
from quant_engine.core.metrics import MetricsCalculator

class TestDataAndMetrics(unittest.TestCase):
    
    def test_data_loader_from_dataframe(self):
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        raw_df = pd.DataFrame({
            "open": [100.0 + i for i in range(10)],
            "high": [105.0 + i for i in range(10)],
            "low": [98.0 + i for i in range(10)],
            "close": [102.0 + i for i in range(10)],
            "volume": [1000 + i for i in range(10)]
        }, index=dates)
        
        cleaned = DataLoader.load_data(raw_df)
        self.assertIn("Open", cleaned.columns)
        self.assertIn("High", cleaned.columns)
        self.assertIn("Low", cleaned.columns)
        self.assertIn("Close", cleaned.columns)
        self.assertIn("Volume", cleaned.columns)
        self.assertEqual(len(cleaned), 10)

    def test_metrics_calculator(self):
        # 100 days of equity growing from 100,000 to 120,000
        equity = [100000.0 * (1.0 + 0.002 * i) for i in range(100)]
        trades = [
            {"pnl": 500.0},
            {"pnl": -200.0},
            {"pnl": 800.0},
            {"pnl": 300.0}
        ]
        
        metrics = MetricsCalculator.calculate_metrics(equity, trades)
        self.assertGreater(metrics["cagr"], 0)
        self.assertGreater(metrics["sharpe_ratio"], 0)
        self.assertEqual(metrics["trade_count"], 4)
        self.assertEqual(metrics["win_rate"], 0.75)
        self.assertGreater(metrics["profit_factor"], 1.0)
        self.assertGreater(metrics["sqn"], 0)

if __name__ == "__main__":
    unittest.main()
