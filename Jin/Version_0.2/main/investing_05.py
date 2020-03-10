
# DESCRIPTION --> Adding stocks that pass investment strategy requirement into an array, and from that array, adding stocks which fit my strategy into a second array

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
