# DESCRIPTION --> Comparing ratios with investment strategy and checking if share price of stocks (that met the criteria) went up or down


import pandas as pd
import numpy as np




class test_investment_strategy(object):


    def __init__(self, stock_ticker, dict_investment_criteria, array_stocks_pass_criteria, array_stocks_share_price_increase):

        self.stock_ticker = stock_ticker
        self.dict_investment_criteria = dict_investment_criteria
        self.array_stocks_pass_criteria = array_stocks_pass_criteria    # Array to add in stocks that pass criteria
        self.array_stocks_share_price_increase = array_stocks_share_price_increase



    def parameter_checker(self):

        # To check if the parameters consist of 1 dictionary and 2 arrays
        # Since we are writing methods within this class with the assumption that they are

        if str(type(self.dict_investment_criteria)) != "<class 'dict'>":
            print('The input parameter, ' + str(self.dict_investment_criteria) + ', is not a dictionary! Change the format of your variable.')
            return

        if str(type(self.array_stocks_pass_criteria)) != "<class 'list'>":
            print('The input parameter, ' + str(self.array_stocks_pass_criteria) + ', is not an array! Change the format of your variable.')
            return

        if str(type(self.array_stocks_share_price_increase)) != "<class 'list'>":
            print('The input parameter, ' + str(self.array_stocks_share_price_increase) + ', is not an array! Change the format of your variable.')
            return


    
    def compare_investment_strategy(self, debt_to_equity_ratio, positive_operating_cashflow, price_to_earnings_ratio, \
        market_cap, roi, cnav, nav):


        self.pass_critera = False    # To use this variable in the next method (within this class)

        # Checking if ratio of this specific stock passes my investment criteria
        if (debt_to_equity_ratio <= self.dict_investment_criteria['debt_to_equity_ratio']) and (positive_operating_cashflow == self.dict_investment_criteria['positive_operating_cashflow']) and \
        (price_to_earnings_ratio <= self.dict_investment_criteria['price_to_earnings_ratio']) and (market_cap >= self.dict_investment_criteria['market_cap']) and \
        (cnav < nav) and (roi >= self.dict_investment_criteria['roi']):
            
            self.pass_critera = True    # 1 means that it has passed my investment criteria
            self.array_stocks_pass_criteria.append(self.stock_ticker)    # Adding stock that passed my investment criteria into an array

        return self.array_stocks_pass_criteria

    

    def compare_share_price(self, buy_share_price, sell_share_price, share_price_of_100_gain):

        if self.pass_critera == True:     # To ensure that this method will only parse stocks that matched my investment criteria

            if sell_share_price > buy_share_price:

                self.array_stocks_share_price_increase.append(self.stock_ticker)


            elif share_price_of_100_gain > buy_share_price:

                self.array_stocks_share_price_increase.append(self.stock_ticker)

        return self.array_stocks_share_price_increase
    


# Code to test class
'''
investment_strategy_criteria = {

  'debt_to_equity_ratio': 1,
  'positive_operating_cashflow': True,
  'price_to_earnings_ratio': 15,
  'market_cap': 10**9,  # Billion = 10^9
  'roi': 2  # Will add the % sign later as I can only compare and compute integers
}

array_stocks_pass_criteria = []
array_stocks_share_price_increase = []



a = test_investment_strategy('AAPL', investment_strategy_criteria, array_stocks_pass_criteria, array_stocks_share_price_increase)     # Input is investment strategy criteria

a.parameter_checker() 
var = a.compare_investment_strategy(0.5, True, 10, 10**10, 3, 10, 20)   # This should pass the investment criteria
# .compare_investment_strategy(debt to equity ratio, positive operating cashflow, pe ratio, market cap, ROI, CNAV, NAV)

var2 = a.compare_share_price(100, 200, 220)
# .compare_share_price(buy share price, sell share price, share price of 100% gain)



print(var)
print(var2)
'''