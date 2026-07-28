import yaml
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Union, Type
from quant_engine.strategy.base import QuantStrategy

class DeclarativeStrategyParser:
    """
    Parses YAML/JSON Strategy Specifications into dynamically compiled QuantStrategy classes.
    """

    @staticmethod
    def parse_spec(spec_source: Union[str, Dict[str, Any]]) -> Type[QuantStrategy]:
        """
        Parses a YAML/JSON string, dict, or file path into a dynamic QuantStrategy subclass.
        """
        if isinstance(spec_source, str):
            if spec_source.endswith(".yaml") or spec_source.endswith(".yml"):
                with open(spec_source, "r", encoding="utf-8") as f:
                    spec_dict = yaml.safe_load(f)
            elif spec_source.endswith(".json"):
                with open(spec_source, "r", encoding="utf-8") as f:
                    spec_dict = json.load(f)
            else:
                # Try parsing raw YAML/JSON string
                try:
                    spec_dict = yaml.safe_load(spec_source)
                except Exception:
                    spec_dict = json.loads(spec_source)
        else:
            spec_dict = spec_source

        if not isinstance(spec_dict, dict):
            raise ValueError(f"Invalid strategy specification format: {type(spec_dict)}")

        name = spec_dict.get("name", "DeclarativeStrategy")
        indicators_spec = spec_dict.get("indicators", {})
        position_spec = spec_dict.get("position_sizing", {})
        trailing_spec = spec_dict.get("trailing_stop", {})
        rules_spec = spec_dict.get("rules", {})

        # Define dynamic Strategy class
        class GeneratedDeclarativeStrategy(QuantStrategy):
            sizer_type = position_spec.get("type", "atr_risk")
            risk_pct = float(position_spec.get("risk_pct", 0.015))
            atr_multiplier = float(trailing_spec.get("atr_multiplier", 3.0))
            breakeven_trigger_r = float(trailing_spec.get("breakeven_trigger_r", 1.0))
            drawdown_guard = bool(position_spec.get("drawdown_scaling", True))

            def init(self):
                super().init()
                close = pd.Series(self.data.Close)
                self.ind_map = {}

                # Register indicators defined in spec
                for ind_name, ind_conf in indicators_spec.items():
                    ind_type = str(ind_conf.get("type", "EMA")).upper()
                    period = int(ind_conf.get("period", 14))

                    if ind_type == "EMA":
                        self.ind_map[ind_name] = self.I(lambda p=period: close.ewm(span=p, adjust=False).mean().to_numpy(), name=ind_name)
                    elif ind_type == "SMA":
                        self.ind_map[ind_name] = self.I(lambda p=period: close.rolling(p).mean().to_numpy(), name=ind_name)

            def on_bar(self):
                # Simple rule evaluator (e.g., ema_fast > ema_slow)
                long_rule = rules_spec.get("entry_long", None)
                if long_rule and " > " in long_rule:
                    parts = long_rule.split(" > ")
                    ind1_name, ind2_name = parts[0].strip(), parts[1].strip()
                    if ind1_name in self.ind_map and ind2_name in self.ind_map:
                        ind1 = self.ind_map[ind1_name]
                        ind2 = self.ind_map[ind2_name]
                        if len(ind1) >= 1 and len(ind2) >= 1:
                            if ind1[-1] > ind2[-1] and not self.position:
                                self.enter_long()

        GeneratedDeclarativeStrategy.__name__ = name
        return GeneratedDeclarativeStrategy
