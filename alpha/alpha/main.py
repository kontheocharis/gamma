import tensorflow as tf
import numpy as np

from abc import ABC
from typing import final

class DataFetcher(ABC):

    @final
    FINANCIAL_COLUMNS = ('total_assets', 'market_cap', 'revenue', 'gross_profit', 'net_profit', 'earnings')

    @final
    STOCK_COLUMNS = ('high', 'low', 'close')

    @abstractmethod
    def financials() -> tf.data.

