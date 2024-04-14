"""
Overarching enums and models
"""

from enum import StrEnum

from .stocks.extendend_bars import ExtendedBarSet
from .stocks.models import CustomBarSet

BARSET_TYPE = ExtendedBarSet | CustomBarSet


class Status(StrEnum):
    """
    Status of a backtest and running of the application
    """

    IN_PROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"
