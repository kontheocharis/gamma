import pandas as pd
import requests
import os
import hashlib
import json
from typing import Tuple, Optional
from enum import Enum

from alpha.base import DataFetcher


class Statement(Enum):
    BALANCE_SHEET = 0
    INCOME_STATEMENT = 1
    CASH_FLOW_STATEMENT = 2
    SHARE_PRICES = 3

    def to_string(self) -> str:
        if self == Statement.BALANCE_SHEET:
            return 'balance-sheet-statement'
        elif self == Statement.INCOME_STATEMENT:
            return 'income-statement'
        elif self == Statement.CASH_FLOW_STATEMENT:
            return 'cash-flow-statement'
        elif self == Statement.SHARE_PRICES:
            return 'share-prices'
        assert False


class FmpError(Exception):
    pass


class FmpDataFetcher(DataFetcher):
    """
    An implementation of `DataFetcher` using financialmodelingprep.com API

    :param company_symbol: the stock market symbol of the company in question.
    :param year_range: a tuple in the form `(start_year, end_year)` for which
        to fetch data
    :param data_folder: the folder in which the data from financialmodelingprep
        is located.
    """

    _year_start: int
    _year_end: int
    _symb: str
    _data_folder: Optional[str]

    _BASE_URL = 'https://financialmodelingprep.com/api/v3'
    _CACHE_LOCATION = os.path.join(os.path.dirname(__file__), '../cache/')

    _FINANCIAL_COMP = "financials/{}/{}"
    _SHARE_COMP = "historical-price-full/{}?from={}&to={}"

    def __init__(self, company_symbol: str, year_range: Tuple[int, int], data_folder: Optional[str] = None):
        self._year_start, self._year_end = year_range
        self._symb = company_symbol
        self._data_folder = data_folder


    def financial_data(self) -> pd.DataFrame:
        statements = (Statement.BALANCE_SHEET, Statement.INCOME_STATEMENT, Statement.CASH_FLOW_STATEMENT)

        raw_dfs = {}
        for statement in statements:
            data = json.loads(self._load_resource(statement))
            if not data: raise FmpError(f"no {statement.to_string()} data for {self._symb}")
            raw_dfs[statement] = pd.DataFrame(data['financials'])
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

        df = self._format_df(df)
        return df


    def stock_data(self) -> pd.DataFrame:
        data = json.loads(self._load_resource(Statement.SHARE_PRICES))
        if not data: raise FmpError(f"no {statement.to_string()} data for {self._symb}")

        df = pd.DataFrame(data['historical']).filter(items=('date', 'high', 'low'))
        df.set_index('date', inplace=True)

        df = self._format_df(df)
        return df


    def _format_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gets `df` in the right format, including parsing indices and values,
        and limiting to applicable dates.
        """

        df.index.name = None
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric, errors='raise')
        df.sort_index(inplace=True)
        df = df.loc[str(self._year_start):str(self._year_end)]
        return df


    def _load_resource(self, statement: Statement) -> str:
        """
        Loads a url resource.

        If `self._data_folder` exists, loads from there. Otherwise, looks at
        the cache first (see `self._CACHE_LOCATION`) and returns the resource
        if present.  If it isn't, fetches the resource at `url`, returns it and
        updates the cache.
        """

        if self._data_folder:
            return json.loads(os.path.join(self._data_folder, statement.to_string(), f"{self._symb}.json"))

        url = f"{self._BASE_URL}/{self._FINANCIAL_COMP.format(statement.to_string(), self._symb)}" \
            if statement != Statement.SHARE_PRICES else \
            f"{self._BASE_URL}/{self._SHARE_COMP.format(self._symb, self._year_start, self._year_end + 1)}"

        url_hash = hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]
        file_location = os.path.join(self._CACHE_LOCATION, url_hash)

        if os.path.exists(file_location):
            with open(file_location, 'r') as f:
                contents = f.read()
            return contents

        contents = requests.get(url).text
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        with open(file_location, 'w') as f:
            f.write(contents)
        return contents
