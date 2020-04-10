
import pandas as pd 
import json
from datetime import date
import numpy as np


from calculate_accuracy_rate_06.investment_criteria import *
from calculate_accuracy_rate_06.check_investment_criteria import *


dict_investment_criteria = {

  'debt_to_equity_ratio': 1,
  'positive_operating_cashflow': True,
  'price_to_earnings_ratio': 15,
  'market_cap': 10**9,  # Billion = 10^9
  'roi': 2  # Will add the % sign later as I can only compare and compute integers
}

a = np.array([-1, -2, -3]) 
b = np.array([[-1, -2, 3], [4, -5, 6]]) 
c = np.array([[-1, -2, 3], [4, -5, 6]]) 
d = np.array([[-1, -2, 3], [4, -5, 6]]) 
e = np.array([[-1, -2, 3], [4, -5, 6]]) 
f = np.array([[-1, -2, 3], [4, -5, 6]]) 
g = np.array([-1, -2, 3]) 


indices_stocks_pass_criteria = investment_critera(dict_investment_criteria, a, b, c, d, e, f, g)

print(test)


