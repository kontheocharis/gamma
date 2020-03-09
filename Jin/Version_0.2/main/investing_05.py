

import pandas as pd


array = []


class stocks_that_fulfilled_requirements(object):
    
    def __init__(self, fulfil_requirements, ticker, buy_share_price, final_sell_share_price):

        self.fulfil_requirements = fulfil_requirements
        self.ticker = ticker
        self.buy_share_price = buy_share_price
        self.final_sell_share_price = final_sell_share_price


    def add_ticker_to_array(self):  # If investment strategy criteria is fulfilled, add the stock ticker to an array
        
        if self.fulfil_requirements == 1:

            return True
            # I will return the stock ticker and .append() it in final_algorithm.py
    

    def did_stock_price_increase(self):
        
        if self.final_sell_share_price > self.buy_share_price:

            return True



'''



def did_stock_price_move_up(self):

    if final_sell_share_price > buy_share_price:

        no_of_stocks_that_price_moved_up = no_of_stocks_that_price_moved_up + 1


    elif buy_share_price > final_sell_share_price:

        no_of_stocks_that_price_moved_down = no_of_stocks_that_price_moved_down + 1



def accuracy_rate():





'''