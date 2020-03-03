import pandas as pd
import numpy as np
import json 
import requests


# IMPORTANT VARIABLES TO NOTE

# analysing_share_price.buy_share_price
# analysing_share_price.sell_share_price
# analysing_share_price.max_sell_price_possible --> the maximum sell price over the period of 3 years --> don't need this, but it might be useful to know
# analysing_share_price.sell_date_of_100_gain --> the date when the 100% gain was made during the period of 3 years (if any)
# analysing_share_price.sell_share_price_of_100_gain --> the sell price when the 100% gain was made during the period of 3 years (if any)



def analysing_share_price(URL, buy_date, sell_date, goal_of_return_during_period):

    json_share_price = requests.get(URL).json()
    df_share_price = pd.DataFrame(json_share_price['historical'])

    # .loc['row_name'] to select rows
    # df['col_name'] to select columns


    for i in range(len(df_share_price)):
        if df_share_price["date"].iloc[i] == buy_date:
            buy_date_index = i


    for i in range(len(df_share_price)):
        if df_share_price["date"].iloc[i] == sell_date:
            sell_date_index = i


    # Had to use a function decorator to use the variable outside the function
    analysing_share_price.buy_share_price = df_share_price["close"].iloc[buy_date_index]  # Buy price in 2016
    analysing_share_price.sell_share_price = df_share_price["close"].iloc[sell_date_index]    # Sell price 3 years later in 2019

    analysing_share_price.max_sell_price_possible = 0     
    # This is to find the max price over the past 3 years to see if there is a 100% gain from the buy price within the period of 3 years (2016-2019) 

    no_of_indexes_in_between = sell_date_index - buy_date_index

    # This iteration is to find the maximum sell price possible, over the period of 3 years
    for i in range(no_of_indexes_in_between):
        if df_share_price["close"].iloc[i+buy_date_index] > analysing_share_price.max_sell_price_possible:  
        # Had to do (i + buy_date_index) to start analysing share price from the buy data
            analysing_share_price.max_sell_price_possible = float(df_share_price["close"].iloc[i+buy_date_index])

    for i in range(no_of_indexes_in_between):
        if df_share_price["close"].iloc[i+buy_date_index] > (goal_of_return_during_period * analysing_share_price.buy_share_price):
        # goal_of_return_during_period = 2 now, but it can be easily changed below when calling the umbrella function
            analysing_share_price.sell_date_of_100_gain = df_share_price["date"].iloc[i+buy_date_index]
            analysing_share_price.sell_share_price_of_100_gain = df_share_price["close"].iloc[i+buy_date_index]

        