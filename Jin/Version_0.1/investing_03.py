import pandas as pd
import numpy as np
import json 
import requests

import time
start_time = time.time()    # To test how fast this program runs


from investing_01 import *
from investing_02 import *     
from investing_04 import *  

# RUNNING UMBRELLA FUNCTIONS TO USE VARIABLES
# Used function decorators to use the variable outside the function

string_interpolation("aapl")

analysing_statements(string_interpolation.URL_income_statement, string_interpolation.URL_balance_sheet, string_interpolation.URL_cashflow_statement)
analysing_share_price(string_interpolation.URL_share_price, "2016-04-01", "2019-04-01", 2)


# METRICS

def investing_algorithm(pe_ratio_margin, operating_cashflow_margin, debt_to_equity_ratio_margin, potential_roi_margin, \
    market_cap_margin): 
    

    total_good_assets = analysing_statements.cash_2016 + (analysing_statements.ppe_net_2016 / 2)   # This ain't actually the calculation for total good assets bc I should not take Net PP&E and exclude short-term investments 

    cnav1 = (total_good_assets - analysing_statements.total_liabilities_2016) / analysing_statements.total_outstanding_shares_2016
    nav = (analysing_statements.total_assets_2016 - analysing_statements.total_liabilities_2016) / analysing_statements.total_outstanding_shares_2016
    pe_ratio = analysing_share_price.buy_share_price / analysing_statements.eps_2016
    debt_to_equity_ratio = analysing_statements.total_debt_2016 / analysing_statements.total_equity_2016
    potential_roi = nav/analysing_share_price.buy_share_price - 1
    market_cap = analysing_statements.total_outstanding_shares_2016 * analysing_share_price.buy_share_price


    # REQUIREMENTS


    if cnav1 < nav and pe_ratio < pe_ratio_margin and analysing_statements.operating_cashflow_2016 > operating_cashflow_margin and analysing_statements.operating_cashflow_2015 > operating_cashflow_margin and analysing_statements.operating_cashflow_2014 > operating_cashflow_margin and debt_to_equity_ratio < debt_to_equity_ratio_margin and potential_roi > potential_roi_margin and market_cap > market_cap_margin:
        print("Our investing algorithm states that we should invest in this stock! If you did invest in this stock, your buy price would have beem " + str(analysing_share_price.buy_share_price) + " and you sell price at 100% gain would be ... " + str(analysing_share_price.sell_share_price_of_100_gain))

    else: 
        print("Our investing algorithm states that we should NOT invest in this stock! However, if you did invest in this stock, your buy price would have been " + str(analysing_share_price.buy_share_price) + " and you sell price at 100% gain would be ... "  + str(analysing_share_price.sell_share_price_of_100_gain))


investing_algorithm(5, 0, 1, 1, 10**9)
print("--- %s seconds ---" % (time.time() - start_time))    # To print the runtime of program
