
import pandas as pd
import json
import time
import os

start_time = time.time()    # To record time taken for program to run



no_of_tickers = len(pd.read_csv("stock_ticker_list_after_parse_dict.csv"))   # To record the number of tickers in newly generated .csv file from parse_dict.py


def load_tickers_from_csv():

    # Will need to manually input name of .csv file generated from parse_dict.py
    load_tickers_from_csv.df_list_of_tickers = pd.read_csv("stock_ticker_list_after_parse_dict.csv")



def stock_is_up_to_date(df_of_ticker):

    for i in range(len(df_of_ticker)):

        if df_of_ticker['date'].iloc[i] == "2020-01-03":   # Let's just take 3rd January 2020 as the minimum date required
            #print("It is up to date")
            return True




def parse_up_to_date(ticker):
    

    path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{ticker}.json"


    df_share_price = open(path_share_price, 'r')     # Open the file
    df_share_price = df_share_price.read()  # This converts the file into a string (aka an object)
    df_share_price = json.loads(df_share_price)     # This converts the object into a dictionary

    df_share_price = pd.DataFrame.from_dict(df_share_price['historical'])  # Lastly, this converts the file into a dataframe

    
    #stock_is_up_to_date(df_share_price)
    

    if not stock_is_up_to_date(df_share_price) == True:
        print(ticker + " does not have share price data of the 3rd January 2020.")


    else:
        print(ticker + " is perfect.")
        df.append(ticker)   # Adding the name of ticker which are valid (aka contains data) into a dataframe
    




df = []     # Creating an empty array (to be later converted to a dataframe after appending stock tickers / symbols into it)


for i in range(no_of_tickers):  # Need to run this program through every ticker from newly generated .csv file from parse_dict.py

    load_tickers_from_csv()     # To load list of tickers from the newly generated .csv file from parse_dict.py  
    temporary_ticker = load_tickers_from_csv.df_list_of_tickers['Stock_Ticker'].iloc[i]     # To select each ticker individually from the newly generated .csv file from parse_dict.py

    parse_up_to_date(temporary_ticker)
    

df = pd.DataFrame(df)
df.columns = ['Stock_Ticker']     # Renaming the column name (which would otherwise be called "0")
print(df)

df.to_csv('stock_ticker_list_after_parse_up_to_date.csv')    # To save dataframe to a .csv file locally to refer to 



print("--- %s seconds ---" % (time.time() - start_time))