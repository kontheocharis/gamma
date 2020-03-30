'''
1. This file is to take the company tickers and indexes in df_companytickers
2. And put it into a dictionary
3. Download the dictionary into a .json file locally
4. The purpose is to use this .json file when creating an empty 3D array 

'''


import pandas as pd
import json

df_companytickers = pd.read_excel(r'companytickers.xlsx')   # To read the excel file


dict_companytickers = {     # Creating an empty dictionary to add keys and values in the iteration

}

for i in range(len(df_companytickers)):

    dict_companytickers[ str(df_companytickers['Ticker'].iloc[i]) ] = i     # To create the dictionary and pairing companyticker with index



with open('dict_companytickers.json', 'w') as fp:
    json.dump(dict_companytickers, fp)  # To download the dictionary (containing the companytickers and indices) into a .json file locally