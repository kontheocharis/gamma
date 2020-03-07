
# DESCRIPTION --> To take json file of tickers from API and note down tickers which paths are present
# and export them into a .csv file locally

import pandas as pd
import json
import time
import os
start_time = time.time()



def load_tickers():

    path_list_of_tickers = "/Users/jin/Desktop/download/f_statements/list_of_tickers.json"  # Where the file is kept locally
    load_tickers.df_list_of_tickers = open(path_list_of_tickers, 'r')     # Open the file
    load_tickers.df_list_of_tickers = load_tickers.df_list_of_tickers.read()  # This converts the file into a string (aka an object)

    load_tickers.df_list_of_tickers = json.loads(load_tickers.df_list_of_tickers)     # This converts the object into a dictionary
    load_tickers.df_list_of_tickers = pd.DataFrame.from_dict(load_tickers.df_list_of_tickers['symbolsList'])   # Lastly, this converts the file into a dataframe



def path_is_ok(path):

    if os.stat(path).st_size == 0:
        return False
    else: 
        return True


def parse_path(ticker):


    path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/{ticker}.json"
    path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/{ticker}.json"
    path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/{ticker}.json"
    path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{ticker}.json"


    if path_is_ok(path_income_statement) == False:
        print(ticker + " has an empty file path in the income statement.")


    elif path_is_ok(path_balance_sheet) == False:
        print(ticker + " has an empty file path in the balance sheet.")


    elif path_is_ok(path_cashflow_statement) == False:
        print(ticker + " has an empty file path in the cashflow statement.")


    elif path_is_ok(path_share_price) == False:
        print(ticker + " has an empty file path in the daily share price json file.")
    

    else:
        df.append(ticker)




df = []     # Creating an empty array (to be later converted to a dataframe after appending stock tickers / symbols into it)

for i in range(13854):  # Because there are 13854 stock tickers in the list from the API

    load_tickers()
    temporary_ticker = load_tickers.df_list_of_tickers['symbol'].iloc[i]
    
    parse_path(temporary_ticker)

    

df = pd.DataFrame(df)
df.columns = ['Stock_Ticker']     # Renaming the column name (which would otherwise be called "0")
print(df)

df.to_csv('stock_ticker_list_after_parse_path.csv')    # To save dataframe to a .csv file locally to refer to 


print("--- %s seconds ---" % (time.time() - start_time))