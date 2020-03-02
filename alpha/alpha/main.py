import tensorflow as tf
import numpy as np

from abc import ABC
from typing import final, List
from dataclasses import dataclass


class DataFetcher(ABC):
    """
    An interface to fetch the exact data that is needed for calculating certain
    investability metrics.
    """

    @final
    FINANCIAL_COLUMNS = (
        'total_assets',
        'total_liabilities',
        'investment_properties',
        'cash_and_equivalent',
        'land_property',
        'total_outstanding_shares',
        'operating_cashflow',
        'total_debt',
        'total_equity',
        'frac_insider_ownership',
    )

    @final
    STOCK_COLUMNS = ('high', 'low', 'close')

    @abstractmethod
    def financial_data(self) -> pd.DataFrame:
        """
        Gets quarterly financial data of company.

        :returns: a date-indexed `pd.DataFrame` with columns
        `self.FINANCIAL_COLUMNS` and quarterly data points.
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


@dataclass
class StockRowYahooFiles:
    stockrow_income_file: str
    stockrow_balancesheet_file: str
    stockrow_cashflow_file: str
    yahoo_stock_file: str

class StockRowYahooFetcher(DataFetcher):
    _files: StockRowYahooFiles

    def __init__(files: StockRowYahooFiles):
        self._files = files

    def financial_data(self) -> pd.DataFrame:
        df = pd.read_excel(self._financial_file, index_col=[0]).transpose()
        df = df.filter()
        return df

    def stock_data(self) -> pd.DataFrame:
        pass
