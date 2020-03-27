import time
start_time = time.time()


import pandas as pd
import numpy as np


from get_metric_from_pkl_02 import *
from calculate_ratios_03 import *
from check_date_valid_04 import *
from get_share_price_data_05 import *
from test_investment_strategy_06 import *
from calculate_rate_of_accuracy_07 import *
#from loop_through_stocks_08 import *



# Getting dataframes from .pkl files --> get_metric_from_pkl_02.py
df_income = load_df_from_pkl('income.pkl')
df_balance = load_df_from_pkl('balance.pkl')
df_cashflow = load_df_from_pkl('cashflow.pkl')
df_shareprices = load_df_from_pkl('daily_shareprices.pkl')
df_companytickers = pd.read_excel(r'companytickers.xlsx')



# Testing investment strategy --> test_investment_strategy_07
investment_strategy_criteria = {

  'debt_to_equity_ratio': 1,
  'positive_operating_cashflow': True,
  'price_to_earnings_ratio': 15,
  'market_cap': 10**9,  # Billion = 10^9
  'roi': 2  # Will add the % sign later as I can only compare and compute integers
}

array_stocks_pass_criteria = []
array_stocks_share_price_increase = []




class algo(object):

  def __init__(self, df_income, df_balance, df_cashflow, df_shareprices, df_companytickers, \
  array_stocks_pass_criteria, array_stocks_share_price_increase, \
  investment_strategy_criteria):
      
    self.df_income = df_income
    self.df_balance = df_balance
    self.df_cashflow = df_cashflow
    self.df_shareprices = df_shareprices
    self.df_companytickers = df_companytickers

    self.array_stocks_pass_criteria = array_stocks_pass_criteria
    self.array_stocks_share_price_increase = array_stocks_share_price_increase
    self.investment_strategy_criteria = investment_strategy_criteria
    




  def run_algo(self, fiscal_year, buy_date, sell_date):
  

    # To put in different company tickers as the parameter
    for i in range(len(self.df_income)):
      
      if int(self.df_income['Fiscal Year'].iloc[i]) == fiscal_year:



        # Getting metrics from dataframe --> get_metric_from_pkl_02.py
        net_income = get_metric_from_df(self.df_income, 'Net Income', i)
        total_outstanding_shares = get_metric_from_df(self.df_income, 'Shares (Diluted)', i)
        
        cash = get_metric_from_df(self.df_balance, 'Cash, Cash Equivalents & Short Term Investments', i)
        ppe = get_metric_from_df(self.df_balance, 'Property, Plant & Equipment, Net', i)
        total_assets = get_metric_from_df(self.df_balance, 'Total Assets', i)
        shortterm_debt = get_metric_from_df(self.df_balance, 'Short Term Debt', i)
        longterm_debt = get_metric_from_df(self.df_balance, 'Long Term Debt', i)
        total_liabilities = get_metric_from_df(self.df_balance, 'Total Liabilities', i)
        total_equity = get_metric_from_df(self.df_balance, 'Total Equity', i)

        operating_cashflow = get_metric_from_df(self.df_cashflow, 'Net Cash from Operating Activities', i)

        print(net_income)




  '''

  # Getting share price data --> get_share_price_data_05.py
  class_05 = get_share_price_data(df_shareprices, 'dataframe')

  buy_share_price_index = class_05.get_index_of_share_price(self.buy_date, company_ticker)
  sell_share_price_index = class_05.get_index_of_share_price(self.sell_date, company_ticker)

  buy_share_price = class_05.get_share_price(self.buy_date, company_ticker)
  sell_share_price = class_05.get_share_price(self.sell_date, company_ticker)


  share_price_of_100_gain = class_05.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'share price')
  index_of_100_gain = class_05.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'index')
  date_of_100_gain = class_05.get_info_of_100_gain(buy_share_price_index, sell_share_price_index, buy_share_price, sell_share_price, 'date')



  # Calculating ratios --> calculate_ratios_03.py
  class_03 = calculate_ratios()

  debt_to_equity_ratio = class_03.debt_to_equity_ratio(shortterm_debt, longterm_debt, total_equity)
  positive_operating_cashflow = class_03.positive_operating_cashflow(operating_cashflow)
  price_to_earnings_ratio = class_03.price_to_earnings_ratio(net_income, total_outstanding_shares, buy_share_price)
  market_cap = class_03.market_cap(buy_share_price, total_outstanding_shares)
  cnav = class_03.cnav(cash, ppe, total_liabilities, total_outstanding_shares)
  nav = class_03.nav(total_assets, total_liabilities, total_outstanding_shares)
  roi = class_03.roi(sell_share_price, buy_share_price)   # Using buy and sell share price as parameters
  # Therefore I to put this code after I get share price info



  # Testing investment strategy --> test_investment_strategy_06.py

  class_06 = test_investment_strategy(company_ticker, investment_strategy_criteria, array_stocks_pass_criteria, array_stocks_share_price_increase)

  class_06.parameter_checker()

  array_stocks_pass_criteria = class_06.compare_investment_strategy(debt_to_equity_ratio, positive_operating_cashflow, price_to_earnings_ratio, \
            market_cap, roi, cnav, nav)
  array_stocks_share_price_increase = class_06.compare_share_price(buy_share_price, sell_share_price, share_price_of_100_gain)
  '''





a = algo(df_income, df_balance, df_cashflow, df_shareprices, df_companytickers, \
  array_stocks_pass_criteria, array_stocks_share_price_increase, \
  investment_strategy_criteria)



a.run_algo(2015, '2015-01-12', '2017-01-10')



print("--- %s seconds ---" % (time.time() - start_time))
