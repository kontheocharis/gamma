
import pandas as pd
import json
import time
import os

start_time = time.time()    # To record time taken for program to run



no_of_tickers = len(pd.read_csv("stock_ticker_list_after_parse_path.csv"))   # To record the number of tickers in newly generated .csv file from parse_path.py


def load_tickers_from_csv():

    # Will need to manually input name of .csv file generated from parse_path.py
    load_tickers_from_csv.df_list_of_tickers = pd.read_csv("stock_ticker_list_after_parse_path.csv")



def dict_is_ok(dict):

    if len(dict) < 2:
        return False
    else: 
        return True



def parse_dict(ticker):
    
    path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/{ticker}.json"
    path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/{ticker}.json"
    path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/{ticker}.json"
    path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{ticker}.json"


    dict_income_statement = open(path_income_statement, 'r')     # Open the file
    dict_income_statement = dict_income_statement.read()  # This converts the file into a string (aka an object)
    dict_income_statement = json.loads(dict_income_statement)     # This converts the object into a dictionary

    dict_balance_sheet = open(path_balance_sheet, 'r')     # Open the file
    dict_balance_sheet = dict_balance_sheet.read()  # This converts the file into a string (aka an object)
    dict_balance_sheet = json.loads(dict_balance_sheet)     # This converts the object into a dictionary

    dict_cashflow_statement = open(path_cashflow_statement, 'r')     # Open the file
    dict_cashflow_statement = dict_cashflow_statement.read()  # This converts the file into a string (aka an object)
    dict_cashflow_statement = json.loads(dict_cashflow_statement)     # This converts the object into a dictionary

    dict_share_price = open(path_share_price, 'r')     # Open the file
    dict_share_price = dict_share_price.read()  # This converts the file into a string (aka an object)
    dict_share_price = json.loads(dict_share_price)     # This converts the object into a dictionary

    
    if dict_is_ok(dict_income_statement) == False:
        print(ticker + " has an empty dictionary in the income statement.")


    elif dict_is_ok(dict_balance_sheet) == False:
        print(ticker + " has an empty dictionary in the balance sheet.")

    elif dict_is_ok(dict_cashflow_statement) == False:
        print(ticker + " has an empty dictionary in the cashflow statement.")


    # Should I write a seperate if statement without the function since its technically supposed to be < 10???
    elif dict_is_ok(dict_share_price) == False:    
        print(ticker + " has an empty dictionary in the daily share price file.")


    else:
        print(ticker + " is perfect.")
        df.append(ticker)   # Adding the name of ticker which are valid (aka contains data) into a dataframe




df = []     # Creating an empty array (to be later converted to a dataframe after appending stock tickers / symbols into it)


for i in range(no_of_tickers):  # Need to run this program through every ticker from newly generated .csv file from parse_path.py


    load_tickers_from_csv()     # To load list of tickers from the newly generated .csv file from parse_path.py  
    temporary_ticker = load_tickers_from_csv.df_list_of_tickers['Stock_Ticker'].iloc[i]     # To select each ticker individually from the newly generated .csv file from parse_path.py
    
    parse_dict(temporary_ticker)    # Running each individually selected ticker through a parser program / function / checker



df = pd.DataFrame(df)
df.columns = ['Stock_Ticker']     # Renaming the column name (which would otherwise be called "0")
print(df)

df.to_csv('stock_ticker_list_after_parse_dict.csv')    # To save dataframe to a .csv file locally to refer to 


print("--- %s seconds ---" % (time.time() - start_time))