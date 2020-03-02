from alpha.fmp import FmpDataFetcher

def main():
    fetcher = FmpDataFetcher('AAPL', (2017, 2020))
    print(fetcher.stock_data())
    print(fetcher.financial_data())


