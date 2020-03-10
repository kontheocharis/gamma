import requests
import os
import hashlib
import ujson
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, Tuple, Optional, Dict
from enum import Enum
from datetime import date, timedelta

import pandas as pd


class Statement(Enum):
    BALANCE_SHEET = 0
    INCOME_STATEMENT = 1
    CASH_FLOW_STATEMENT = 2
    SHARE_PRICES = 3


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
        'operating_cashflow',
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


# Actual implementation

class FmpError(Exception):
    pass

class FmpNonExistentBoundsError(FmpError):
    pass

class FmpDataFetcher(DataFetcher):
    """
    An implementation of `DataFetcher` using financialmodelingprep.com API

    :param company_symbol: the stock market symbol of the company in question.
    :param year_range: a tuple in the form `(start_year, end_year)` for which
        to fetch data
    :param data_dir: the folder in which the data from financialmodelingprep
        is located.
    """

    date_range: Tuple[date, date]
    _symb: str
    _data_dir: str

    _financial_data: Optional[pd.DataFrame] = None
    _stock_data: Optional[pd.DataFrame] = None

    _CACHE_LOCATION = os.path.join(os.path.dirname(__file__), '../cache/')
    _PICKLE_SAVE_URL: str
    _PICKLE_PATHS: Dict[str, str]


    def __init__(self, company_symbol: str, date_range: Tuple[date, date], data_dir: str):
        self._date_range = date_range
        self._symb = company_symbol
        self._data_dir = data_dir

        self._PICKLE_SAVE_URL = os.path.join(self._CACHE_LOCATION, 'fmp-pickle')
        self._PICKLE_PATHS = {p: os.path.join(self._PICKLE_SAVE_URL, f"{p}-{self._symb}.pkl") \
                              for p in ('financial', 'stock')}

    def save_pickle(self):
        os.makedirs(self._PICKLE_SAVE_URL, exist_ok=True)

        if not os.path.exists(self._PICKLE_PATHS['financial']):
            self._financial_data.to_pickle(self._PICKLE_PATHS['financial'])

        if not os.path.exists(self._PICKLE_PATHS['stock']):
            self._stock_data.to_pickle(self._PICKLE_PATHS['stock'])


    def load_pickle(self):
        for path in self._PICKLE_PATHS.values():
            if not os.path.exists(path):
                return

        self._financial_data = pd.read_pickle(self._PICKLE_PATHS['financial'])
        self._stock_data = pd.read_pickle(self._PICKLE_PATHS['stock'])


    def financial_data(self) -> pd.DataFrame:
        if self._financial_data is not None:
            return self._format_df(self._financial_data)

        statements = (Statement.BALANCE_SHEET, Statement.INCOME_STATEMENT, Statement.CASH_FLOW_STATEMENT)

        raw_dfs = {}
        for statement in statements:
            data = ujson.loads(self._load_resource(statement))
            if not data: raise FmpError(f"no {self._statement_to_string(statement)} data for {self._symb}")
            raw_dfs[statement] = pd.json_normalize(data, record_path='financials')
            raw_dfs[statement].set_index('date', inplace=True)

        ics = raw_dfs[Statement.INCOME_STATEMENT]
        bls = raw_dfs[Statement.BALANCE_SHEET]
        cfs = raw_dfs[Statement.CASH_FLOW_STATEMENT]

        mappings = {
            'total_outstanding_shares':    ics['Weighted Average Shs Out'],
            'eps':                         ics['EPS'],
            'cash_short_term_investments': bls['Cash and short-term investments'],
            'ppe':                         bls['Property, Plant & Equipment Net'],
            'total_assets':                bls['Total assets'],
            'total_liabilities':           bls['Total liabilities'],
            'total_shareholders_equity':   bls['Total shareholders equity'],
            'total_debt':                  bls['Total debt'],
            'operating_cashflow':          cfs['Operating Cash Flow'],
        }

        df = pd.DataFrame(mappings, copy=False)

        self._financial_data = df
        df = self._format_df(df)
        return df


    def stock_data(self, restrict_dates=True) -> pd.DataFrame:
        if self._stock_data is not None:
            return self._format_df(self._stock_data)

        data = ujson.loads(self._load_resource(Statement.SHARE_PRICES))
        if not data: raise FmpError(f"no stock data for {self._symb}")

        df = pd.json_normalize(data, record_path='historical').filter(items=('date', 'high', 'low'))
        df.set_index('date', inplace=True)

        self._stock_data = df
        df = self._format_df(df, restrict_dates)
        return df


    def restrict_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.loc[self._date_range[0]:self._date_range[1]]
        if df.empty:
            raise FmpNonExistentBoundsError("no data available for date bounds")
        return df


    def _format_df(self, df: pd.DataFrame, restrict_dates=True) -> pd.DataFrame:
        """
        Gets `df` in the right format, including parsing indices and values,
        and limiting to applicable dates.
        """

        df.index.name = None
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric, errors='raise')
        df.sort_index(inplace=True)
        if restrict_dates:
            df = self.restrict_dates(df)
        return df


    def _statement_to_string(self, statement: Statement) -> str:
        if statement == Statement.BALANCE_SHEET:
            return 'balance-sheet-statement'
        elif statement == Statement.INCOME_STATEMENT:
            return 'income-statement'
        elif statement == Statement.CASH_FLOW_STATEMENT:
            return 'cash-flow-statement'
        elif statement == Statement.SHARE_PRICES:
            return 'share-prices'
        assert False


    def _load_resource(self, statement: Statement) -> str:
        """
        Loads a resource from self._data_dir.
        """
        with open(os.path.join(
                self._data_dir,
                self._statement_to_string(statement),
                f"{self._symb}.json"), 'r') as f:
            return f.read()
