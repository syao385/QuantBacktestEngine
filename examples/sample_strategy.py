import pandas as pd
from quant_engine.strategy.base import QuantStrategy
from quant_engine.core.runner import EngineRunner

class GEXBreakoutStrategy(QuantStrategy):
    """
    Sample GEX Breakout Strategy showcasing QuantBacktestEngine.
    """
    sizer_type = "atr_risk"
    risk_pct = 0.015
    atr_multiplier = 3.0
    breakeven_trigger_r = 1.0

    fast_period = 10
    slow_period = 30

    def init(self):
        super().init()
        close = pd.Series(self.data.Close)
        self.fast_ema = self.I(lambda: close.ewm(span=self.fast_period, adjust=False).mean().to_numpy(), name="FastEMA")
        self.slow_ema = self.I(lambda: close.ewm(span=self.slow_period, adjust=False).mean().to_numpy(), name="SlowEMA")

    def on_bar(self):
        if len(self.fast_ema) < 2 or len(self.slow_ema) < 2:
            return
        
        # Long entry on EMA breakout
        if self.fast_ema[-2] <= self.slow_ema[-2] and self.fast_ema[-1] > self.slow_ema[-1]:
            self.enter_long()

def main():
    print("Running sample GEX Breakout backtest on SPY...")
    result = EngineRunner.run_backtest(
        strategy_class=GEXBreakoutStrategy,
        source="SPY",
        symbol="SPY",
        cash=100000.0,
        start_date="2023-01-01",
        end_date="2024-01-01"
    )

    print("\n--- BACKTEST RESULTS ---")
    print(f"Strategy:       {result.strategy_name}")
    print(f"Symbol:         {result.symbol}")
    print(f"CAGR:           {result.metrics['cagr']*100:.2f}%")
    print(f"Sharpe Ratio:   {result.metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:  {result.metrics['sortino_ratio']:.2f}")
    print(f"Max Drawdown:   {result.metrics['max_drawdown']*100:.2f}%")
    print(f"Trade Count:    {result.metrics['trade_count']}")
    print(f"Win Rate:       {result.metrics['win_rate']*100:.1f}%")
    print(f"Profit Factor:  {result.metrics['profit_factor']:.2f}")

if __name__ == "__main__":
    main()
