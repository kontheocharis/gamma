"""
Data fetcher for financialmodelingprep

Fetches data from financialmodelingprep.com and stores it in current
directory. Fetches yearly balance sheets, income statements, cash flow
statements as well as daily share price data.

Requires: wget, parallel
"""

import os
import subprocess
import requests
from dataclasses import dataclass
from typing import Dict

statements = ('balance-sheet-statement', 'income-statement', 'cash-flow-statement')
jobs = 8

def get_links() -> Dict[str, str]:
    symbols_url = "https://financialmodelingprep.com/api/v3/company/stock/list"
    links: Dict[str, str] = {}

    data = requests.get(symbols_url).json()['symbolsList']

    for statement in statements:
        root_url = f"https://financialmodelingprep.com/api/v3/financials/{statement}/"
        links[statement] = '\n'.join(root_url + i['symbol'] for i in data)

    share_url = "https://financialmodelingprep.com/api/v3/historical-price-full/"
    links['share-prices'] = '\n'.join(share_url + i['symbol'] for i in data)

    return links


def download_data(links: Dict[str, str]):
    for statement in links:
        os.makedirs(statement, exist_ok=True)
        print(f"Downloading {statement} files.")
        subprocess.run(("parallel", "-j", f"{jobs}", "wget",  "-nc", "-O", statement + "/{/}.json", "{}"), input=str.encode(links[statement]))

    print("Done.")


if __name__ == "__main__":
    download_data(get_links())
