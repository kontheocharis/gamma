
# DESCRIPTION --> String interpolation through list of tickers

import pandas as pd
import os
import json
import time


'''
# Only uncomment this when testing the code with the file

start_time = time.time()


df_stock_ticker = pd.read_csv("stock_ticker_list_after_parse_up_to_date.csv")

size_of_stock_ticker_list = len(df_stock_ticker)
'''


class stock_ticker(object):
    
    def __init__(self, ticker):
        self.ticker = ticker


    def string_interpolation_income_statement(self):
      

    # INCOME STATEMENT json file --> Dataframe 
        path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/{self.ticker}.json"

        self.df_income_statement = open(path_income_statement, 'r')     # Open the file
        # Spent an 1.5h solving this error
            # In the future, use this to list files in any given directory --> os.listdir("/Users/jin/Desktop") 
            # The second argument, 'r', is unneccessary, as it is set to default and just opens the file for reading
        
        self.df_income_statement = self.df_income_statement.read()  # This converts the file into a string (aka an object)
        self.df_income_statement = json.loads(self.df_income_statement)     # This converts the object into a dictionary
        
        self.df_income_statement = pd.DataFrame.from_dict(self.df_income_statement['financials'])   # Lastly, this converts the file into a dataframe

        return self.df_income_statement
        

    def string_interpolation_balance_sheet(self):

        # BALANCE SHEET json file --> Dataframe 
        path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/{self.ticker}.json"

        self.df_balance_sheet = open(path_balance_sheet, 'r')  
        self.df_balance_sheet = self.df_balance_sheet.read()
        self.df_balance_sheet = json.loads(self.df_balance_sheet)

        self.df_balance_sheet = pd.DataFrame.from_dict(self.df_balance_sheet['financials'])

        return self.df_balance_sheet


    def string_interpolation_cashflow_statement(self):

        # CASHFLOW STATEMENT json file --> Dataframe 
        path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/{self.ticker}.json"

        self.df_cashflow_statement = open(path_cashflow_statement, 'r')
        self.df_cashflow_statement = self.df_cashflow_statement.read()
        self.df_cashflow_statement = json.loads(self.df_cashflow_statement)

        self.df_cashflow_statement = pd.DataFrame.from_dict(self.df_cashflow_statement['financials'])

        return self.df_cashflow_statement


    def string_interpolation_share_price(self):

        # DAILY SHARE PRICE json file --> Dataframe 
        path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{self.ticker}.json"
        
        self.df_share_price = open(path_share_price, 'r')
        self.df_share_price = self.df_share_price.read()
        self.df_share_price = json.loads(self.df_share_price)
        
        self.df_share_price = pd.DataFrame.from_dict(self.df_share_price['historical'])

        return self.df_share_price

        #print("This loop is successful. The company is " + self.ticker)
        #print(self.df_income_statement)






'''

# Only uncomment this when testing the code with the file


# To loop through all the files in the .csv file
#for i in range(size_of_stock_ticker_list):
for i in range(2):

    temporary_ticker = df_stock_ticker["Stock_Ticker"].iloc[i]    # Temporary ticker is putting each ticker in each path on my desktop to convert json files to databases
    stock_ticker(temporary_ticker).string_interpolation()




print("--- %s seconds ---" % (time.time() - start_time))

'''