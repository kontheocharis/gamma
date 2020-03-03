import pandas as pd
import numpy as np
import json 
import requests

from final_one import *     # To import all the variables from final_one.py
from final_two import *     





# METRICS

total_good_assets = cash_2016 + (ppe_net_2016 / 2)   # This ain't actually the calculation for total good assets bc I should not take Net PP&E and exclude short-term investments 

cnav1 = (total_good_assets - total_liabilities_2016) / total_outstanding_shares_2016
nav = (total_assets_2016 - total_liabilities_2016) / total_outstanding_shares_2016
pe_ratio = buy_share_price / eps_2016
debt_to_equity_ratio = total_debt_2016 / total_equity_2016
potential_roi = nav/buy_share_price - 1
market_cap = total_outstanding_shares_2016 * buy_share_price




# REQUIREMENTS


if cnav1 < nav and pe_ratio < 10 and operating_cashflow_2016 > 0 and operating_cashflow_2015 > 0 and operating_cashflow_2014 > 0 and debt_to_equity_ratio < 1 and potential_roi > 1 and market_cap > 10**9:
    print("Invest! Based on historic data, your buy price would be " + str(buy_share_price) + " and the highest possible price that you could have sold it at would be " + str(highest_possible_sell_price))

else: 
    print("Don't invest! However, based on historic data, your buy price would be " + str(buy_share_price) + " and the highest possible price that you could have sold it at would be " + str(highest_possible_sell_price))


