from alpaca.data.models import BarSet
from .stocks.models import CustomBarSet
from enum import StrEnum

BARSET_TYPE = BarSet | CustomBarSet


class Status(StrEnum):
    IN_PROGRESS = "inprogress"
    COMPLETED = "completed"
    FAILED = "failed"
