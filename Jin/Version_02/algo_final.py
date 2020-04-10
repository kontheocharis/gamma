
from datetime import date
import pandas as pd 



from get_simfin_data_01.get_simfin_data import *
# To download data from the data source

a = get_simfin_data()

a.load_income()
a.load_balance() 
a.load_cashflow()
a.load_shareprices()
a.load_companytickers()




from convert_data_format_02.convert_data_shareprices import *
# Code to convert share price data and download the matrix (with data) and dictionary locally

b = convert_data_shareprices( 'daily_shareprices.pkl', 'income.pkl', date(2007, 1, 3), date(2019, 3, 21) )
b.create_dict_companytickers()

b.create_empty_matrix()
b.create_matrix_shareprices()   # This method will download the matrix.pkl file locally




from convert_data_format_02.convert_data_statement import *
# Code to convert statements data and download 2 dictionaries

c = convert_data_statement('income.pkl', 2007, 2018)     # Set the year parameter to any year between 2007 and 2018
c.get_dict_df_indices()




from get_metrics_03.get_metrics import *
# Getting np.arrays of metrics


# Income Statement 
array_net_income = get_metric_income('income.pkl', 'dict_df_indices.json', 2014, 'Net Income')
array_total_outstanding_shares = get_metric_income('income.pkl', 'dict_df_indices.json', 2014, 'Shares (Diluted)')

# Balance Sheet
array_cash = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Cash, Cash Equivalents & Short Term Investments')
array_ppe = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Property, Plant & Equipment, Net')
array_total_assets = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Total Assets')
array_shortterm_debt = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Short Term Debt')
array_longterm_debt = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Long Term Debt')
array_total_liabilities = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Total Liabilities')
array_total_equity = get_metric_income('balance.pkl', 'dict_df_indices.json', 2014, 'Total Equity')

# Cashflow Statement
array_operating_cashflow = get_metric_income('cashflow.pkl', 'dict_df_indices.json', 2014, 'Net Cash from Operating Activities')






from get_shareprices_04.get_shareprices import *
# Getting share prices

d = get_shareprices('dict_df_indices.json', 'dict_companytickers.json', date(2007, 1, 3), 'matrix.pkl', date(2014, 2, 3), date(2016, 2, 3))

array_buy_shareprices = d.get_buy_shareprices()
array_sell_shareprices = d.get_sell_shareprices()

array_company_index = d.get_array_company_index()   # Getting array of company_index to input into function below
array_100_shareprices = d.get_100_shareprice(array_buy_shareprices, array_company_index)






from calculate_ratios_05.formula_of_ratios import *
# Calculating ratios

array_debt_to_equity_ratio = debt_to_equity_ratio(array_shortterm_debt, array_longterm_debt, array_total_equity)

array_positive_operating_cashflow = positive_operating_cashflow(array_operating_cashflow)

array_price_to_earnings_ratio = price_to_earnings_ratio(array_net_income, array_total_outstanding_shares, array_buy_shareprices)

array_market_cap = market_cap(array_buy_shareprices, array_total_outstanding_shares)


array_cnav = cnav(array_cash, array_ppe, array_total_liabilities, array_total_outstanding_shares)
array_nav = nav(array_total_assets, array_total_liabilities, array_total_outstanding_shares)
array_roi = roi(array_cnav, array_nav)






from calculate_accuracy_rate_06.investment_criteria import *    # Getting variable - dict_investment_criteria - to put into parameters of function below
from calculate_accuracy_rate_06.check_investment_criteria import *


# Get no of stocks that passed criteria
no_of_stocks_pass_criteria = check_investment_critera(dict_investment_criteria, array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi)


# Get no of stocks (that passed criteria) that increased in share price
no_of_stocks_pass_criteria_increase_shareprices = check_share_price_increase(dict_investment_criteria, array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi, \
  array_buy_shareprices, array_sell_shareprices)



print( 'The rate of accuracy is ' + str(no_of_stocks_pass_criteria_increase_shareprices / no_of_stocks_pass_criteria * 100) + '%' )






'''
FINISHED EVERYTHING APART FROM THE FOLLOWING:

1. CONVERTING THIS FILE INTO A FUNCTION WITH FISCAL YEAR, BUY DATE AND SELL DATE AS PARAMETERS AS I WANT TO KEEP THE IMPORT HEADINGS FOR NOW
2. NEED TO TAKE 100% SHARE PRICE GAIN INTO ACCOUNT
3. I HAVE ALREADY GOTTEN THE ARRAY FOR 100% SHARE PRICE GAIN BUT NEED TO IMPLEMENT IT IN Line 69 of check_investment_criteria.py 
4. I DONT KNOW HOW TO WRITE OR SINCE AND IS NOW WRITTEN AS (&)
'''
