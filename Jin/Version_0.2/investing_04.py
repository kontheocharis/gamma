
# FILE --> STRING INTERPOLATION OF STOCK TICKERS AND CREATING DATAFRAMES FOR FINANCIAL STATEMENTS AND SHARE PRICE

import pandas as pd
import os
import json
import time
start_time = time.time()



path_list_of_tickers = "/Users/jin/Desktop/download/f_statements/list_of_tickers.json"  # Where the file is kept locally
df_list_of_tickers = open(path_list_of_tickers, 'r')     # Open the file
df_list_of_tickers = df_list_of_tickers.read()  # This converts the file into a string (aka an object)

df_list_of_tickers = json.loads(df_list_of_tickers)     # This converts the object into a dictionary
df_list_of_tickers = pd.DataFrame.from_dict(df_list_of_tickers['symbolsList'])   # Lastly, this converts the file into a dataframe

no_of_tickers = len(df_list_of_tickers)




def string_interpolation(ticker):

    # INCOME STATEMENT json file --> Dataframe 
    path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/{ticker}.json"

    if os.stat(path_income_statement).st_size == 0:
        print("The income statement of " + ticker + " is empty")
        return
    

    string_interpolation.df_income_statement = open(path_income_statement, 'r')     # Open the file
    # Spent an 1.5h solving this error
        # In the future, use this to list files in any given directory --> os.listdir("/Users/jin/Desktop") 
        # The second argument, 'r', is unneccessary, as it is set to default and just opens the file for reading
    
    string_interpolation.df_income_statement = string_interpolation.df_income_statement.read()  # This converts the file into a string (aka an object)
    string_interpolation.df_income_statement = json.loads(string_interpolation.df_income_statement)     # This converts the object into a dictionary


    if len(string_interpolation.df_income_statement) < 2:
        print("The balance sheet of " + ticker + " is empty")
        return

    string_interpolation.df_income_statement = pd.DataFrame.from_dict(string_interpolation.df_income_statement['financials'])   # Lastly, this converts the file into a dataframe
    # I have to write 'financials' as the json file has 2 components: the company's stock ticker and financials





    # BALANCE SHEET json file --> Dataframe 
    path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/{ticker}.json"

    if os.stat(path_balance_sheet).st_size == 0:
        print("The balance sheet of " + ticker + " is empty")
        return


    string_interpolation.df_balance_sheet = open(path_balance_sheet, 'r')  
    string_interpolation.df_balance_sheet = string_interpolation.df_balance_sheet.read()
    string_interpolation.df_balance_sheet = json.loads(string_interpolation.df_balance_sheet)

    if len(string_interpolation.df_balance_sheet) < 2:
        print("The balance sheet of " + ticker + " is empty")
        return

    string_interpolation.df_balance_sheet = pd.DataFrame.from_dict(string_interpolation.df_balance_sheet['financials'])





    # CASHFLOW STATEMENT json file --> Dataframe 
    path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/{ticker}.json"

    if os.stat(path_cashflow_statement).st_size == 0:
        print("The cashflow statement of " + ticker + " is empty")
        return

    string_interpolation.df_cashflow_statement = open(path_cashflow_statement, 'r')
    string_interpolation.df_cashflow_statement = string_interpolation.df_cashflow_statement.read()
    string_interpolation.df_cashflow_statement = json.loads(string_interpolation.df_cashflow_statement)


    if len(string_interpolation.df_cashflow_statement) < 2:
        print("The cashflow statement of " + ticker + " is empty")
        return

    string_interpolation.df_cashflow_statement = pd.DataFrame.from_dict(string_interpolation.df_cashflow_statement['financials'])




    # DAILY SHARE PRICE json file --> Dataframe 
    path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{ticker}.json"
    df_share_price = open(path_share_price, 'r')
    df_share_price = df_share_price.read()


    if len(df_share_price) < 10:
        print("The share price file of " + ticker + " is empty")
        return
                            

    df_share_price = json.loads(df_share_price)
    df_share_price = pd.DataFrame.from_dict(df_share_price['historical'])

    print("This loop is successful. The company is " + ticker)
    #print(df_share_price.head())



def looping_string_interpolation(no_of_loops):

    for i in range(no_of_loops):

        temporary_ticker = df_list_of_tickers["symbol"].iloc[i]     # Temporary string of ticker attached
        string_interpolation(temporary_ticker)  
        # Temporary ticker is putting each ticker in each path on my desktop to convert json files to databases


#looping_string_interpolation(no_of_tickers)
looping_string_interpolation(4)

print("--- %s seconds ---" % (time.time() - start_time))

