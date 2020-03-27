# DESCRIPTION --> Getting metric from .pkl files of income, balance and cashflow


import pandas as pd
import numpy as np



def load_df_from_pkl(file_name):   # file_name is 'income.pkl', 'balance.pkl', 'cashflow.pkl', 'daily_shareprices.pkl' and 'companytickers.pkl'

   return pd.read_pickle(file_name)   # Converting .pkl file into a dataframe 


'''
def get_metric_from_df(df_statement, metric, fiscal_year, ticker):
        
        
    for i in range(len(df_statement)):
        
        metric_to_return = 0

        if int(df_statement['Fiscal Year'].iloc[i]) == fiscal_year \
        and str(df_statement['Ticker'].iloc[i]) == ticker:    # If metric is from selected year and selected company ticker


            if str(df_statement[metric].iloc[i]) == 'nan':   # For blank / empty cells within the dataframe
                metric_to_return = 0

            else:
                metric_to_return = int(df_statement[metric].iloc[i])    # Converting it to an integer to ensure that data type is correct
                # However, this also means that I can't return items such as 'Ticker' as stock tickers are strings, not integers

        
    if metric_to_return == 0:
        return metric_to_return
    
    else:
        return metric_to_return
'''



def get_metric_from_df(df_statement, metric, ticker_index):
    # Ticker index and not ticker as each index has a unique ticker and fiscal year
        
        
    if str(df_statement[metric].iloc[ticker_index]) == 'nan':   # For blank / empty cells within the dataframe
            metric_to_return = 0

    else:
        metric_to_return = int(df_statement[metric].iloc[ticker_index])    # Converting it to an integer to ensure that data type is correct
        # However, this also means that I can't return items such as 'Ticker' as stock tickers are strings, not integers

        
    if metric_to_return == 0:
        return metric_to_return
    
    else:
        return metric_to_return














# Code to test function - load_df_from_pkl(file_name)
'''
from get_dataframe_02 import *  

df_income = load_df_from_pkl('income.pkl')
df_balance = load_df_from_pkl('balance.pkl')
df_cashflow = load_df_from_pkl('cashflow.pkl')



cash = get_metric_from_df(df_balance, 'Cash, Cash Equivalents & Short Term Investments', 2017, 'AAPL')
print(cash)
''' 



# Code to test function - get_metric_from_df(df_statement, metric, fiscal_year, ticker)
'''
df_income = load_df_from_pkl('income.pkl')
df_balance = load_df_from_pkl('balance.pkl')
df_cashflow = load_df_from_pkl('cashflow.pkl')

print(...)
'''