from pydantic import BaseModel

from ..strats import StrategyDefinition


class BacktestDefinition(BaseModel):
    symbols: list[str] = ["AAPL"]
    strategy_definitions: list[StrategyDefinition] | None = None
    strategy_aliases: list[str] | None = None
    days_to_test_over: int = 30
