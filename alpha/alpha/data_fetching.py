import requests
import os
import hashlib
import ujson
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, Tuple, Optional
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
    _data_dir: Optional[str]

    _financial_data: Optional[pd.DataFrame] = None
    _stock_data: Optional[pd.DataFrame] = None

    _BASE_URL = 'https://financialmodelingprep.com/api/v3'
    _CACHE_LOCATION = os.path.join(os.path.dirname(__file__), '../cache/')

    _FINANCIAL_COMP = "financials/{}/{}"
    _SHARE_COMP = "historical-price-full/{}?from={}&to={}"

    def __init__(self, company_symbol: str, date_range: Tuple[date, date], data_dir: Optional[str] = None):
        self._date_range = date_range
        self._symb = company_symbol
        self._data_dir = data_dir


    def save_pickle(self):
        save_url = os.path.join(self._CACHE_LOCATION, "fmp-pickle")
        os.makedirs(save_url, exist_ok=True)

        financial_path = f"{save_url}/financial-{self._symb}.pkl"
        if not os.path.exists(financial_path):
            self._financial_data.to_pickle(financial_path)

        stock_path = f"{save_url}/stock-{self._symb}.pkl"
        if not os.path.exists(stock_path):
            self._stock_data.to_pickle(stock_path)


    def load_pickle(self):
        save_url = os.path.join(self._CACHE_LOCATION, "fmp-pickle")
        os.makedirs(save_url, exist_ok=True)
        paths = (f"{save_url}/financial-{self._symb}.pkl", f"{save_url}/stock-{self._symb}.pkl")

        for p in paths:
            if not os.path.exists(p):
                return

        self._financial_data = pd.read_pickle(paths[0])
        self._stock_data = pd.read_pickle(paths[1])


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
        if not data: raise FmpError(f"no {self._statement_to_string(statement)} data for {self._symb}")

        df = pd.json_normalize(data, record_path='historical').filter(items=('date', 'high', 'low'))
        df.set_index('date', inplace=True)

        self._stock_data = df
        df = self._format_df(df, restrict_dates)
        return df


    def restrict_dates(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
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
        Loads a url resource.

        If `self._data_dir` exists, loads from there. Otherwise, looks at
        the cache first (see `self._CACHE_LOCATION`) and returns the resource
        if present.  If it isn't, fetches the resource at `url`, returns it and
        updates the cache.
        """

        if self._data_dir:
            with open(os.path.join(self._data_dir,
                                   self._statement_to_string(statement),
                                   f"{self._symb}.json"), 'r') as f:
                return f.read()

        else:
            assert False
        # url = f"{self._BASE_URL}/{self._FINANCIAL_COMP.format(self._statement_to_string(statement), self._symb)}" \
        #     if statement != Statement.SHARE_PRICES else \
        #     f"{self._BASE_URL}/{self._SHARE_COMP.format(self._symb, self._year_start, self._year_end + 1)}"

        # url_hash = hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]
        # file_location = os.path.join(self._CACHE_LOCATION, url_hash)

        # if os.path.exists(file_location):
        #     with open(file_location, 'r') as f:
        #         contents = f.read()
        #     return contents

        # contents = requests.get(url).text
        # os.makedirs(os.path.dirname(file_location), exist_ok=True)

        # with open(file_location, 'w') as f:
        #     f.write(contents)
        # return contents
