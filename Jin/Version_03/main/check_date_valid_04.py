import time
start_time = time.time()


# DESCRIPTION --> Checking if date is valid and if there is data in daily_shareprices for that specific date

import pandas as pd
import numpy as np



def is_date_valid(df_shareprices, date, ticker):
        

    valid = 0   # Only creating this variable for the condition of if statement at the end

    for i in range(len(df_shareprices)):

        if str(df_shareprices['Date'].iloc[i]) == date \
        and str(df_shareprices['Ticker'].iloc[i]) == ticker:

            return 'There is data for this date!'   # Using return to stop the loop from iterating too many timnes

        if valid == 0:
            return 'There is no data for this date. Pick another date.'
                



# Code to test class
'''
from get_dataframe_02 import *  

df_shareprices = load_df_from_pkl('daily_shareprices.pkl')



var = is_date_valid(df_shareprices, '2017-01-10', 'AAPL')

print(var)

print("--- %s seconds ---" % (time.time() - start_time))
'''