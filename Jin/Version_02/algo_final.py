
from datetime import date
import pandas as pd 



from get_simfin_data_01.get_simfin_data import *
# To download data from the data source

from convert_data_format_02.convert_data_shareprices import *
# Code to convert share price data and download the matrix (with data) and dictionary locally

from convert_data_format_02.convert_data_statement import *
# Code to convert statements data and download 2 dictionaries

from get_metrics_03.get_metrics import *
# Getting np.arrays of metrics

from get_shareprices_04.get_shareprices import *
# Getting share prices

from calculate_ratios_05.formula_of_ratios import *
# Calculating ratios

from calculate_accuracy_rate_06.investment_criteria import *    # Getting variable - dict_investment_criteria - to put into parameters of function below
from calculate_accuracy_rate_06.check_investment_criteria import *





def algo(buy_date, sell_date, buy_fiscal_year):

  a = get_simfin_data()

  a.load_income()
  a.load_balance() 
  a.load_cashflow()
  a.load_shareprices()
  a.load_companytickers()



  b = convert_data_shareprices( 'daily_shareprices.pkl', 'income.pkl', date(2007, 1, 3), date(2019, 3, 21) )
  b.create_dict_companytickers()

  b.create_empty_matrix()
  b.create_matrix_shareprices()   # This method will download the matrix.pkl file locally




  c = convert_data_statement('income.pkl', 2007, 2018)     # Set the year parameter to any year between 2007 and 2018
  c.get_dict_df_indices()




  # Income Statement 
  array_net_income = get_metric_income('income.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Net Income')
  array_total_outstanding_shares = get_metric_income('income.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Shares (Diluted)')

  # Balance Sheet
  array_cash = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Cash, Cash Equivalents & Short Term Investments')
  array_ppe = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Property, Plant & Equipment, Net')
  array_total_assets = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Total Assets')
  array_shortterm_debt = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Short Term Debt')
  array_longterm_debt = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Long Term Debt')
  array_total_liabilities = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Total Liabilities')
  array_total_equity = get_metric_income('balance.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Total Equity')

  # Cashflow Statement
  array_operating_cashflow = get_metric_income('cashflow.pkl', 'dict_df_indices.json', buy_fiscal_year, 'Net Cash from Operating Activities')





  d = get_shareprices('dict_df_indices.json', 'dict_companytickers.json', date(2007, 1, 3), 'matrix.pkl', buy_date, sell_date)   # date(2014, 2, 3), date(2016, 2, 3))

  array_buy_shareprices = d.get_buy_shareprices()
  array_sell_shareprices = d.get_sell_shareprices()

  array_company_index = d.get_array_company_index()   # Getting array of company_index to input into function below
  array_100_shareprices = d.get_100_shareprice(array_buy_shareprices, array_company_index)





  array_debt_to_equity_ratio = debt_to_equity_ratio(array_shortterm_debt, array_longterm_debt, array_total_equity)

  array_positive_operating_cashflow = positive_operating_cashflow(array_operating_cashflow)

  array_price_to_earnings_ratio = price_to_earnings_ratio(array_net_income, array_total_outstanding_shares, array_buy_shareprices)

  array_market_cap = market_cap(array_buy_shareprices, array_total_outstanding_shares)


  array_cnav = cnav(array_cash, array_ppe, array_total_liabilities, array_total_outstanding_shares)
  array_nav = nav(array_total_assets, array_total_liabilities, array_total_outstanding_shares)
  array_roi = roi(array_cnav, array_nav)




  # Get no of stocks that passed criteria
  # and no of stocks (that passed criteria) that increased in share price
  no_of_stocks_pass_criteria, no_of_stocks_pass_criteria_increase_shareprices = check_investment_critera(dict_investment_criteria, array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi, \
    array_buy_shareprices, array_sell_shareprices, array_100_shareprices)



  # To return rate_of_accuracy = 0 if there is no shareprice data for either the buy_date or sell_date

  if no_of_stocks_pass_criteria != 0:   # If it is not going to be divisible by 0
  
    rate_of_accuracy = no_of_stocks_pass_criteria_increase_shareprices / no_of_stocks_pass_criteria * 100

  else: 
    rate_of_accuracy = 0


  
  print( 'The rate of accuracy is ' + str( rate_of_accuracy ) + '%. ' +  \
    str(no_of_stocks_pass_criteria) + ' no of stocks passed the investment criteria and ' + str(no_of_stocks_pass_criteria_increase_shareprices) + ' (that passed the criteria) increased in share price.')
  






algo(date(2011, 5, 6), date(2013, 5, 7), 2011)

