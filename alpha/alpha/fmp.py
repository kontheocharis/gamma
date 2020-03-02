import pandas as pd
import requests
import os
import hashlib
import json
from typing import Tuple

from alpha.base import DataFetcher


class FmpDataFetcher(DataFetcher):
    """
    An implementation of `DataFetcher` using financialmodelingprep.com API

    :param company_symbol: the stock market symbol of the company in question.

    :param year_range: a tuple in the form `(start_year, end_year)` for which
    to fetch data
    """

    _year_start: int
    _year_end: int
    _symb: str

    _BASE_URL = 'https://financialmodelingprep.com/api/v3'
    _CACHE_LOCATION = os.path.join(os.path.dirname(__file__), '../cache/')

    def __init__(self, company_symbol: str, year_range: Tuple[int, int]):
        self._year_start, self._year_end = year_range
        self._symb = company_symbol
        pass


    def financial_data(self) -> pd.DataFrame:
        statements = ('balance-sheet-statement', 'income-statement', 'cash-flow-statement')

        urls = {statement: f"{self._BASE_URL}/financials/{statement}/{self._symb}" \
                for statement in statements}

        raw_dfs = {}
        for statement in statements:
            data = json.loads(self._load_resource(urls[statement]))
            raw_dfs[statement] = pd.DataFrame(data['financials'])
            df = raw_dfs[statement]
            df.set_index('date', inplace=True)
            df.index.name = None
            df.index = pd.to_datetime(df.index)
            df = df.loc[str(self._year_end + 1):str(self._year_start)]

        ics = raw_dfs['income-statement']
        bls = raw_dfs['balance-sheet-statement']
        cfs = raw_dfs['cash-flow-statement']

        mappings = {
            # 'total_outstanding_shares':    ,
            'eps':                         ics['EPS'],
            'cash_short_term_investments': bls['Cash and short-term investments'],
            'property_plant_equipment':    bls['Property, Plant & Equipment Net'],
            'total_assets':                bls['Total assets'],
            'total_liabilities':           bls['Total liabilities'],
            'total_shareholders_equity':   bls['Total shareholders equity'],
            'total_debt':                  bls['Total debt'],
            'operating_cashflow':          cfs['Operating Cash Flow'],
        }

        df = pd.DataFrame(mappings, copy=False)
        return df


    def stock_data(self) -> pd.DataFrame:
        url = f"{self._BASE_URL}/historical-price-full/{self._symb}?from={self._year_start}&to={self._year_end + 1}"
        data = json.loads(self._load_resource(url))

        df = pd.DataFrame(data['historical']).filter(items=('date', 'high', 'low'))
        df.set_index('date', inplace=True)
        df.index.name = None
        df.index = pd.to_datetime(df.index)
        return df


    def _load_resource(self, url: str) -> str:
        """
        Loads a url resource.

        Looks at the cache first (see `self._CACHE_LOCATION`) and returns the
        resource if present.  Otherwise, fetches the resource at `url`, returns
        it and updates the cache.
        """

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
