# DESCRIPTION --> Looping all the stock tickers to run as parameters in my program

import pandas as pd
import numpy as np



def loop_through_stocks(df_companytickers):

    for i in range(len(df_companytickers)):

        one_stock_ticker = df_companytickers['Ticker'].iloc[i]
        #print(one_stock_ticker)



# Code to test class

df_companytickers = pd.read_excel(r'companytickers.xlsx')   # Can't use class from get_dataframe_02.py because it fucks up the dataframe (for some reason) and I can't access the 'Ticker' column


loop_through_stocks(df_companytickers)

