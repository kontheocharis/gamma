import pandas as pd

from abc import ABC, abstractmethod
from typing import Final
from dataclasses import dataclass

class DataFetcher(ABC):
    """
    An interface to fetch the exact data that is needed for calculating certain
    investability metrics.
    """

    FINANCIAL_COLUMNS: Final = (
        'total_outstanding_shares',
        'eps',
        'cash_short_term_investments',
        'ppe',
        'total_assets',
        'total_liabilities',
        'total_shareholders_equity',
        'total_debt',
        'operating_cashflow_y0',
        'operating_cashflow_y1',
        'operating_cashflow_y2',
    )

    STOCK_COLUMNS: Final = ('high', 'low')

    @abstractmethod
    def financial_data(self) -> pd.DataFrame:
        """
        Gets yearly financial data of company.

        :returns: a date-indexed `pd.DataFrame` with columns
        `self.FINANCIAL_COLUMNS` and yearly data points.
        """
        pass

    @abstractmethod
    def stock_data(self) -> pd.DataFrame:
        """
        Gets daily stock data of company.

        :returns: a date-indexed `pd.DataFrame` with columns `self.STOCK_COLUMNS`
        and daily data points.
        """
        pass
