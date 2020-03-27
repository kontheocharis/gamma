import time
start_time = time.time()


# DESCRIPTION --> Getting buy share price and sell share price from selected year


import pandas as pd
import numpy as np



class get_share_price_data(object):

    def __init__(self, df_shareprices, format_of_data):

        self.df_shareprices = df_shareprices
        self.format_of_data = format_of_data    # Only adding this (unneccessary) parameter for purpose of loose-coupling and to prevent assumptions when calling this class

        # Asigning the type of dataframe
        if self.format_of_data == 'dataframe':
            self.format_of_data = "<class 'pandas.core.frame.DataFrame'>"   # This is the the output of type(dataframe)

        '''
        List of Methods
            get_index_of_share_price(date, ticker) --> To get the index of buy and sell share prices. This will be used in the parameters of .get_info_of_100_gain().
            get_share_price(date, ticker) --> To get the buy and sell share prices.
            get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, info_of_100_gain) --> To get either the 'share price', 'index' or 'date' of the 100% gain share price.
        '''


    def get_index_of_share_price(self, date, ticker):
        
        if str(type(self.df_shareprices)) == self.format_of_data:  # Only adding this (unneccessary) step for purpose of loose-coupling and to prevent assumptions when calling this class
        # Have to convert the output of type(dataframe) to a string
        
            for i in range(len(self.df_shareprices)):

                if str(self.df_shareprices['Date'].iloc[i]) == date \
                and str(self.df_shareprices['Ticker'].iloc[i]) == ticker:

                    return i    # Return the index of the dataframe where the share_price was found



    def get_share_price(self, date, ticker):
        
        if str(type(self.df_shareprices)) == self.format_of_data:  # Only adding this (unneccessary) step for purpose of loose-coupling and to prevent assumptions when calling this class
        # Have to convert the output of type(dataframe) to a string
        
            for i in range(len(self.df_shareprices)):

                if str(self.df_shareprices['Date'].iloc[i]) == date \
                and str(self.df_shareprices['Ticker'].iloc[i]) == ticker:

                    return int(self.df_shareprices['Close'].iloc[i])



    def get_info_of_100_gain(self, buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, info_of_100_gain):
    # Added an extra parameter asking what info of 100% share price gain you are looking for (eg share price, index or date)
        
        if info_of_100_gain == 'share price':

            share_price_of_100_gain = 0
            indexes_in_between = sell_share_price_index - buy_share_price_index

            for i in range(indexes_in_between):
                
                if int(self.df_shareprices['Close'].iloc[i + buy_share_price_index]) > (2*buy_share_price):     # (i + buy_share_price_index) since I am starting the loop from the index of buy_share_price
                    
                    share_price_of_100_gain = int(self.df_shareprices['Close'].iloc[i + buy_share_price_index])
                    return share_price_of_100_gain


        if info_of_100_gain == 'index':

            share_price_of_100_gain = 0
            indexes_in_between = sell_share_price_index - buy_share_price_index

            for i in range(indexes_in_between):
                
                if int(self.df_shareprices['Close'].iloc[i + buy_share_price_index]) > (2*buy_share_price):     # (i + buy_share_price_index) since I am starting the loop from the index of buy_share_price
                    
                    return i + buy_share_price_index   # (i + buy_share_price_index) since I am starting the loop from the index of buy_share_price


        if info_of_100_gain == 'date':

            share_price_of_100_gain = 0
            indexes_in_between = sell_share_price_index - buy_share_price_index
            index_of_100_gain = 0

            for i in range(indexes_in_between):
                
                if int(self.df_shareprices['Close'].iloc[i + buy_share_price_index]) > (2*buy_share_price):     # (i + buy_share_price_index) since I am starting the loop from the index of buy_share_price
                    
                    return str(self.df_shareprices['Date'].iloc[i + buy_share_price_index])

            








# Code to test class
'''
from get_dataframe_02 import *  

a = load_to_dataframe()

df_shareprices = a.load_pkl_to_dataframe('daily_shareprices.pkl')
df_companytickers = a.load_pkl_to_dataframe('companytickers.pkl')






b = get_share_price_data(df_shareprices, 'dataframe')

buy_share_price_index = b.get_index_of_share_price('2015-01-22', 'GOOG')
buy_share_price = b.get_share_price('2015-01-22', 'GOOG')

sell_share_price_index = b.get_index_of_share_price('2018-01-23', 'GOOG')
sell_share_price = b.get_share_price('2018-01-23', 'GOOG')

share_price_of_100_gain = b.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'share price')
index_of_100_gain = b.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'index')
date_of_100_gain = b.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'date')


print(buy_share_price)
print(sell_share_price)

print(share_price_of_100_gain)
print(index_of_100_gain)
print(date_of_100_gain)


print("--- %s seconds ---" % (time.time() - start_time))
'''