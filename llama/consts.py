"""
Overarching enums and models
"""

from enum import StrEnum

from alpaca.data.models import BarSet

from .stocks.models import CustomBarSet

BARSET_TYPE = BarSet | CustomBarSet


class Status(StrEnum):
    """
    Status of a backtest and running of the application
    """

    IN_PROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"
