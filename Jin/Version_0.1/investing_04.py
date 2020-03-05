import pandas as pd
import numpy as np


def string_interpolation(ticker):

    string_interpolation.URL_income_statement = f"https://financialmodelingprep.com/api/v3/financials/income-statement/{ticker}"
    string_interpolation.URL_balance_sheet = f"https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/{ticker}"
    string_interpolation.URL_cashflow_statement = f"https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/{ticker}"
    string_interpolation.URL_share_price = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line"
