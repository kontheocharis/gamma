# DESCRIPTION --> Calculating ratios from metrics and storing them on global variables

import pandas as pd
import numpy as np



class calculate_ratios(object):

    def __init__(self):

        # Don't need fiscal_year and ticker as a parameter since .get_metric() will get a metric from a specific year and company ticker
        '''
        List of Methods

        '''

    def debt_to_equity_ratio(self, shortterm_debt, longterm_debt, total_equity):

        return (shortterm_debt + longterm_debt) / total_equity


    def positive_operating_cashflow(self, operating_cashflow):

        # I will write program to check if operating cashflow is positive for 3 years later

        if operating_cashflow > 0:
            return  True
        
        else: 
            return False


    def price_to_earnings_ratio(self, net_income, total_outstanding_shares, buy_share_price):
        
        eps_estimated = (net_income*0.9) / total_outstanding_shares     # Assuming that 10% of net income was given out as preferred dividends, since I don't have the exact figure

        return buy_share_price / eps_estimated


    def market_cap(self, buy_share_price, total_outstanding_shares):

        return buy_share_price * total_outstanding_shares


    def cnav(self, cash, ppe, total_liabilities, total_outstanding_shares):    # Conservative Net Asset Value (CNAV) per share

        return (cash + 0.5*ppe - total_liabilities) / total_outstanding_shares  # Assuming that (property investments + land) is 50% of PP&E since I don't have exact figures


    def nav(self, total_assets, total_liabilities, total_outstanding_shares):  # Net Asset Value (NAV) per share

        return (total_assets - total_liabilities) / total_outstanding_shares


    def roi(self, sell_share_price, buy_share_price):

        return (sell_share_price - buy_share_price) / buy_share_price




# Code to test class
'''
a = calculate_ratios()
var = a.nav(200, 100)

print(var)
'''