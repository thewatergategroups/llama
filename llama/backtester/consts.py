from pydantic import BaseModel
from ..strats import StrategyDefinition


class BacktestDefinition(BaseModel):
    symbols: list[str] = ["AAPL"]
    strategies: list[StrategyDefinition] | None = None
    days_to_test_over: int = 30
