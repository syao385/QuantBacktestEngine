import unittest
import os
import tempfile
import pandas as pd
from quant_engine.strategy.declarative import DeclarativeStrategyParser
from quant_engine.strategy.repository import StrategyRepository
from quant_engine.core.runner import EngineRunner

class TestRepositoryAndDeclarative(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.repo = StrategyRepository(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_save_and_retrieve_strategy(self):
        spec = {
            "name": "EMA_Cross_Spec",
            "version": "1.0.0",
            "indicators": {
                "ema_fast": {"type": "EMA", "period": 10},
                "ema_slow": {"type": "EMA", "period": 30}
            },
            "rules": {
                "entry_long": "ema_fast > ema_slow"
            }
        }
        
        self.repo.save_strategy(name="EMA_Cross_Spec", version="1.0.0", spec=spec, description="Initial release")
        retrieved = self.repo.get_strategy("EMA_Cross_Spec", "1.0.0")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "EMA_Cross_Spec")
        self.assertEqual(retrieved["version"], "1.0.0")
        self.assertEqual(retrieved["spec"]["indicators"]["ema_fast"]["period"], 10)

    def test_declarative_parsing_and_execution(self):
        spec = {
            "name": "DeclarativeEMABreakout",
            "version": "1.1.0",
            "indicators": {
                "ema_fast": {"type": "EMA", "period": 5},
                "ema_slow": {"type": "EMA", "period": 15}
            },
            "rules": {
                "entry_long": "ema_fast > ema_slow"
            }
        }
        
        strategy_class = DeclarativeStrategyParser.parse_spec(spec)
        
        # Test executing compiled declarative strategy on synthetic data
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        df = pd.DataFrame({
            "Open": 100.0,
            "High": 102.0,
            "Low": 99.0,
            "Close": [100.0 + i for i in range(50)],
            "Volume": 1000.0
        }, index=dates)
        
        result = EngineRunner.run_backtest(strategy_class=strategy_class, source=df, symbol="TEST")
        self.assertEqual(result.strategy_name, "DeclarativeEMABreakout")
        self.assertIn("cagr", result.metrics)

if __name__ == "__main__":
    unittest.main()
