import pandas as pd
import numpy as np


df_income_statement = pd.read_csv("financials_income_statement.csv")    # Getting data from a .csv file
# df_income_statement = pd.read_csv("financials.csv", index_col ="Date")

df_balance_sheet = pd.read_csv("financials_balance_sheet.csv")
df_cashflow_statement = pd.read_csv("financials_cashflow_statement.csv")

#data = data.transpose()     # Swapping rows & columns in a dataframe



'''
https://stockrow.com/api/companies/AAPL/financials.xlsx?dimension=Q&section=Income%20Statement&sort=asc
https://stockrow.com/api/companies/AAPL/financials.xlsx?dimension=Q&section=Balance%20Sheet&sort=asc
https://stockrow.com/api/companies/AAPL/financials.xlsx?dimension=Q&section=Cash%20Flow&sort=asc



'''




def getting_data (index_position, label_date, financial_statement): 
        
        if financial_statement == "income statement":
                return df_income_statement.at[index_position, label_date]      # Using data.at[index, string] to find the exact cell of data that I need
                # Need to use return to assign the newly calculation to a value

        elif financial_statement == "balance sheet":
                return df_balance_sheet.at[index_position, label_date]
        
        elif financial_statement == "cashflow statement":
                return df_cashflow_statement.at[index_position, label_date]


# Income Statement

index_position_of_total_outstanding_shares = 28
index_position_of_eps = 27

label_date = "30/9/16"


total_outstanding_shares = getting_data (index_position_of_total_outstanding_shares, label_date, "income statement")
eps = getting_data (index_position_of_eps, label_date, "income statement")



# Balance Sheet

index_position_of_cash_and_short_term_investments = 0
index_position_of_net_ppe = 5
index_position_of_total_assets = 10
index_position_of_total_liabilities = 21
index_position_of_shareholders_equity = 25
index_position_of_total_debt = 30

   
cash_and_short_term_investments = getting_data (index_position_of_cash_and_short_term_investments, label_date, "balance sheet")
net_ppe = getting_data (index_position_of_net_ppe, label_date, "balance sheet")
total_assets = getting_data (index_position_of_total_assets, label_date, "balance sheet")
total_liabilities = getting_data (index_position_of_total_liabilities, label_date, "balance sheet")
shareholders_equity = getting_data (index_position_of_shareholders_equity, label_date, "balance sheet")
total_debt = getting_data (index_position_of_total_debt, label_date, "balance sheet")



# Cashflow Statement

index_position_of_operating_cashflow = 7

label_date_minus_one = "30/9/15"
label_date_minus_two = "30/9/14"


operating_cashflow_zero = getting_data (index_position_of_operating_cashflow, label_date, "cashflow statement")         # Year 2016
operating_cashflow_minus_one = getting_data (index_position_of_operating_cashflow, label_date_minus_one, "cashflow statement")  # Year 2015
operating_cashflow_minus_two = getting_data (index_position_of_operating_cashflow, label_date_minus_two, "cashflow statement")  # Year 2014



df_share_price = pd.read_csv("financials_share_price.csv")    # Getting data from a .csv file



def getting_data_yahoo_finance (index_position, label_name): 
        
        return df_share_price.at[index_position, label_name]      

 


# Yahoo Finance - share prices

index_position_of_buy_share_price = 25
starting_index_position_of_max_sell_price = index_position_of_buy_share_price + 1

label_name_of_buy_share_price = "Low"
label_name_of_max_sell_share_price = "High"

buy_share_price = getting_data_yahoo_finance (index_position_of_buy_share_price, label_name_of_buy_share_price)

max_index_no_of_share_price = len(df_share_price) - 1   # len(df_share_price) = 61 indexes in Apple

max_sell_share_price = 0



for i in range(max_index_no_of_share_price - index_position_of_buy_share_price):    # 60 - 25 = 35 iterations
    
    max_price = getting_data_yahoo_finance (starting_index_position_of_max_sell_price, label_name_of_max_sell_share_price)
    if max_price > max_sell_share_price:
        max_sell_share_price = max_price
    starting_index_position_of_max_sell_price = starting_index_position_of_max_sell_price + 1





# Metrics

#from backtesting_two import *   # To import all the variables calculate the metrics


total_good_assets = cash_and_short_term_investments + net_ppe   # This ain't actually the calculation for total good assets bc I should not take Net PP&E and exclude short-term investments 

cnav1 = (total_good_assets - total_liabilities) / total_outstanding_shares
nav = (total_assets - total_liabilities) / total_outstanding_shares
pe_ratio = buy_share_price / eps
debt_to_equity_ratio = total_debt / shareholders_equity
potential_roi = nav/buy_share_price - 1
market_cap = total_outstanding_shares * buy_share_price




# Requirements


if cnav1 < nav and pe_ratio < 10 and operating_cashflow_zero > 0 and operating_cashflow_minus_one > 0 and operating_cashflow_minus_two > 0 and debt_to_equity_ratio < 1 and potential_roi > 1 and market_cap > 10**9:

        print("invest!")

else: 
        print("don't invest!")



