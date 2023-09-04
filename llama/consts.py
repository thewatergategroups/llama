from alpaca.data.models import BarSet
from .stocks.models import CustomBarSet


BARSET_TYPE = BarSet | CustomBarSet
