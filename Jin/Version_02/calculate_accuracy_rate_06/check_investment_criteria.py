
import numpy as np

import warnings   # To ignore all RuntimeWarning errors (that are caused by np.nan to fill up spaces in the matrix)
warnings.filterwarnings("ignore",category =RuntimeWarning)


def check_investment_critera (dict_investment_criteria, \
  array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi, \
  array_buy_shareprices, array_sell_shareprices, array_100_shareprices):


  array_debt_to_equity_ratio = np.where(array_debt_to_equity_ratio < dict_investment_criteria['debt_to_equity_ratio'], True, False)  # Where debt-to-equity ratio < 1, replace it with True, else replace it with False

  # Don't need this since results are already in booleans, but might want to do this for the sake of consistency
  # array_positive_operating_cashflow = np.where(array_positive_operating_cashflow == dict_investment_criteria['positive_operating_cashflow'], True, False)  # Where positive cashflow = True, replace it with True, else replace it with False
  
  array_price_to_earnings_ratio = np.where(array_price_to_earnings_ratio < dict_investment_criteria['price_to_earnings_ratio'], True, False)  # Where price-to-earnings ratio < 15, replace it with True, else replace it with False
  array_market_cap = np.where(array_market_cap > dict_investment_criteria['market_cap'], True, False)  # Where market cap > 1B, replace it with True, else replace it with False
  
  array_cnav = np.where(array_cnav < array_nav, True, False)  # Where CNAV < NAV, replace it with True, else replace it with False
  array_roi = np.where(array_roi > dict_investment_criteria['roi'], True, False)  # Where ROI > 2, replace it with True, else replace it with False



  # To get the indices of the stocks that meet all my criterias
  indices_stocks_pass_criteria = np.argwhere( (array_debt_to_equity_ratio == True) & \
    (array_price_to_earnings_ratio == True) & \
    (array_market_cap == True) & \
    (array_cnav == True) & \
    (array_roi == True) )


  no_of_stocks_pass_criteria = len(indices_stocks_pass_criteria)





  # The code below is to check if the shareprice increased 

  array_increase_shareprices = np.where(array_sell_shareprices > array_buy_shareprices, True, False)  # Where sell shareprice > buy shareprice, replace it with True, else replace it with False


  # Where sell 100% gain shareprice > 0, replace it with True, else replace it with False
  array_100_gain = np.where(array_100_shareprices > 0, True, False)


  # To get the indices of the stocks that meet all my criterias
  indices_stocks_pass_criteria_increase_shareprices = np.argwhere( (array_debt_to_equity_ratio == True) & \
    (array_price_to_earnings_ratio == True) & \
    (array_market_cap == True) & \
    (array_cnav == True) & \
    (array_roi == True) ) & \
    (array_increase_shareprices == True) | (array_100_gain == True)   # If stock that passed criteria increased in shareprice by end of period, or had a 100% shareprice gain in between period


  no_of_stocks_pass_criteria_increase_shareprices = len(indices_stocks_pass_criteria_increase_shareprices)


  return no_of_stocks_pass_criteria, no_of_stocks_pass_criteria_increase_shareprices



