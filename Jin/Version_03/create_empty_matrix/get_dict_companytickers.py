'''
1. This file is to take the company tickers and asign an index to them
2. And put it into a dictionary
3. Download the dictionary into a .json file locally

'''


import pandas as pd
import json


df_shareprices = pd.read_pickle('daily_shareprices.pkl')   # Converting .pkl file into a dataframe 


dict_companytickers = {     # Creating an empty dictionary to add keys and values in the iteration

}




temporary_ticker = ''   # Empty string to input newly found stock ticker later in the loop
index = 0

for i in range(len(df_shareprices)):

    if str( df_shareprices['Ticker'].iloc[i] ) != temporary_ticker:

        temporary_ticker = str( df_shareprices['Ticker'].iloc[i] )

        dict_companytickers[ temporary_ticker ] = index    # Can't use i since that represents looping through all the tickers
        index = index + 1




with open('dict_companytickers.json', 'w') as fp:
    json.dump(dict_companytickers, fp)  # To download the dictionary (containing the companytickers and indices) into a .json file locally