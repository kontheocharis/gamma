
import pandas as pd
import numpy as np
import json 
import requests

# IMPORTANT VARIABLES TO NOTE

# string_interpolation.URL_income_statement
# string_interpolation.URL_balance_sheet
# string_interpolation.URL_cashflow_statement
# string_interpolation.URL_share_price


def string_interpolation():

    json_us_tickers = requests.get("https://financialmodelingprep.com/api/v3/company/stock/list").json()
    df_us_tickers = pd.DataFrame(json_us_tickers['symbolsList'])

    # .loc['row_name'] to select rows
    # df['col_name'] to select columns

    for x in range(len(df_us_tickers)):
    #for x in range(len(df_us_tickers)):
        string_interpolation.ticker = df_us_tickers["symbol"].iloc[x]
        

        string_interpolation.URL_income_statement = f"https://financialmodelingprep.com/api/v3/financials/income-statement/{string_interpolation.ticker}"
        json_income_statement = requests.get(string_interpolation.URL_income_statement).json()
        

        # Checking the size of income statement to see if it's empty
        if len(json_income_statement) < 30:
            continue
        else:
            string_interpolation.URL_balance_sheet = f"https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/{string_interpolation.ticker}"
            string_interpolation.URL_cashflow_statement = f"https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/{string_interpolation.ticker}"
            string_interpolation.URL_share_price = f"https://financialmodelingprep.com/api/v3/historical-price-full/{string_interpolation.ticker}?serietype=line"
            #print(string_interpolation.URL_balance_sheet)


string_interpolation()