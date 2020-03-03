import pandas as pd
import numpy as np
import json 
import requests

from final_one import *     # To import all the variables from final_one.py
from final_two import *     
from final_four import *  

# RUNNING UMBRELLA FUNCTIONS TO USE VARIABLES
# Used function decorators to use the variable outside the function

#analysing_statements("https://financialmodelingprep.com/api/v3/financials/income-statement/AAPL", "https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/AAPL", "https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/AAPL")
#analysing_share_price("https://financialmodelingprep.com/api/v3/historical-price-full/AAPL?serietype=line", "2016-04-01", "2019-04-01", 2)

string_interpolation()
analysing_statements(string_interpolation.URL_income_statement, string_interpolation.URL_balance_sheet, string_interpolation.URL_cashflow_statement)
analysing_share_price(string_interpolation.URL_share_price, "2016-04-01", "2019-04-01", 2)


# METRICS

total_good_assets = analysing_statements.cash_2016 + (analysing_statements.ppe_net_2016 / 2)   # This ain't actually the calculation for total good assets bc I should not take Net PP&E and exclude short-term investments 

cnav1 = (total_good_assets - analysing_statements.total_liabilities_2016) / analysing_statements.total_outstanding_shares_2016
nav = (analysing_statements.total_assets_2016 - analysing_statements.total_liabilities_2016) / analysing_statements.total_outstanding_shares_2016
pe_ratio = analysing_share_price.buy_share_price / analysing_statements.eps_2016
debt_to_equity_ratio = analysing_statements.total_debt_2016 / analysing_statements.total_equity_2016
potential_roi = nav/analysing_share_price.buy_share_price - 1
market_cap = analysing_statements.total_outstanding_shares_2016 * analysing_share_price.buy_share_price




# REQUIREMENTS


if cnav1 < nav and pe_ratio < 10 and operating_cashflow_2016 > 0 and operating_cashflow_2015 > 0 and operating_cashflow_2014 > 0 and debt_to_equity_ratio < 1 and potential_roi > 1 and market_cap > 10**9 and analysing_statements.free_cashflow_2016 > 0:
    print("The CNAV value investing algorithm states that we should invest in " + str(string_interpolation.ticker) + "! Based on historic data, your buy price would be " + str(analysing_share_price.buy_share_price) + " and the price of a 100% gain, you would sell it at during the period of 3 years would have been " + str(analysing_share_price.sell_share_price_of_100_gain))

else: 
    print("The CNAV value investing algorithm states that we should not invest in " + str(string_interpolation.ticker) + "! However, based on historic data, if you did, your buy price would be " + str(analysing_share_price.buy_share_price) + " and the price at 100% gain, you would sell it at during the period of 3 years would have been " + str(analysing_share_price.sell_share_price_of_100_gain))

