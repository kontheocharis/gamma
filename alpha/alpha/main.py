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

# *Step 1*: Find and import data using stockrow.com
# *Step 2*: Select data that we will use to calculate metrics to screen
# equities
# *Step 3*: Run the stocks and data through an algorithm that will give us an
# output - either 1 or 0

# *Algorithm*
#    1. CNAV1 share price has to be less than NAV share price
#    2. P/E ratio of less than 10
#    3. Operating cashflow over the past 3 years has to be positive
#    4. Debt-to-equity ratio of less than 100% or 1
#    5. Potential ROI of 100% or more (= NAV / current share price -1)
#    6. % of insider ownership is over 60%
#    7. Market capitalisation is a minimum of $1 Billion

# *Variables / data that will be needed*
#    - Current share price -> yahoo_stock_file
#    - Share price from 3 years ago -> yahoo_stock_file
#    - Range of max share prices over a period of 3 years -> yahoo_stock_file
#    - Total assets -> stockrow_balancesheet_file
#    - Investment properties -> stockrow_balancesheet_file
#    - Cash and cash equivalents -> stockrow_balancesheet_file
#    - Land / property -> stockrow_balancesheet_file
#    - Total liabilities -> stockrow_balancesheet_file
#    - Total outstanding shares -> stockrow_balancesheet_file
#    - Operating cashflow over the past 3 years -> stockrow_cashflow_file
#    - Total debt -> stockrow_balancesheet_file
#    - Total equity -> stockrow_balancesheet_file
#    - % of insider ownership

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


    def stock_data(self) -> pd.DataFrame:
        pass
