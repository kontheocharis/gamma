
import numpy as np


def debt_to_equity_ratio(shortterm_debt, longterm_debt, total_equity):

    if len(shortterm_debt) != len(longterm_debt) or len(longterm_debt) != len(total_equity):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'
    
    total_debt = np.add(shortterm_debt, longterm_debt)

    return np.divide( total_debt, total_equity, out=np.zeros_like(total_debt), where=total_equity!=0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument



    # return np.divide( np.add(shortterm_debt, longterm_debt), total_equity)



def positive_operating_cashflow(operating_cashflow):

    # I will write program to check if operating cashflow is positive for 3 years later

    return np.greater(operating_cashflow, 0)



def price_to_earnings_ratio(net_income, total_outstanding_shares, buy_share_price):


    if len(net_income) != len(total_outstanding_shares) or len(total_outstanding_shares) != len(buy_share_price):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'


    earnings = np.multiply(net_income, 0.9)

    eps_estimated = np.divide(earnings, total_outstanding_shares, out=np.zeros_like(earnings), where=total_outstanding_shares!=0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument

    return np.divide( buy_share_price, eps_estimated, out=np.zeros_like(buy_share_price), where=eps_estimated!=0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument



def market_cap(buy_share_price, total_outstanding_shares):


    if len(buy_share_price) != len(total_outstanding_shares):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'

    
    return np.multiply(buy_share_price, total_outstanding_shares)



def cnav(cash, ppe, total_liabilities, total_outstanding_shares):    # Conservative Net Asset Value (CNAV) per share
    

    if len(cash) != len(ppe) or len(ppe) != len(total_liabilities) or len(total_liabilities) != len(total_outstanding_shares):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'

    
    ppe = np.multiply(ppe, 0.5)     # Assuming that (property investments + land) is 50% of PP&E since I don't have exact figures
    net_assets = np.subtract( np.add(cash, ppe), total_liabilities)

    return np.divide(net_assets, total_outstanding_shares, out=np.zeros_like(net_assets), where=total_outstanding_shares!=0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument



def nav(total_assets, total_liabilities, total_outstanding_shares):  # Net Asset Value (NAV) per share

    if len(total_assets) != len(total_liabilities) or len(total_liabilities) != len(total_outstanding_shares):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'

    net_assets = np.subtract(total_assets, total_liabilities)

    return np.divide( net_assets, total_outstanding_shares, out=np.zeros_like(net_assets), where=total_outstanding_shares!=0 )
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument



def roi(cnav_share_price, nav_share_price):

    if len(nav_share_price) != len(cnav_share_price):    # To check if arrays are of the same length. If not, return an error.
        return 'Cant do calculation as arrays are of different lengths'

    potential_gain = np.subtract(nav_share_price, cnav_share_price)

    return np.divide(potential_gain, cnav_share_price, out=np.zeros_like(potential_gain), where=cnav_share_price!=0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument
