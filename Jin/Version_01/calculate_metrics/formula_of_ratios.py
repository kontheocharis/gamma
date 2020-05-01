
import numpy as np


def debt_to_equity_ratio(shortterm_debt, longterm_debt, total_equity):
    '''To calculate debt-to-equity ratio.'''

    # To check if arrays are of the same length. If not, return an error.
    if len(shortterm_debt) != len(longterm_debt) or len(longterm_debt) != len(total_equity):
        return 'Cant do calculation as arrays are of different lengths'

    total_debt = shortterm_debt + longterm_debt

    return np.divide(total_debt, total_equity, out=np.zeros_like(total_debt), where=total_equity != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument


def positive_operating_cashflow(operating_cashflow):
    '''To get positive operating cashflow.'''

    # I will write program to check if operating cashflow is positive for 3 years later

    return np.greater(operating_cashflow, 0)


def price_to_earnings_ratio(net_income, total_outstanding_shares, buy_share_price):
    '''To calculate price-to-earnings ratio.'''

    if len(net_income) != len(total_outstanding_shares) or len(total_outstanding_shares) != len(buy_share_price):
        return 'Cant do calculation as arrays are of different lengths'

    earnings = net_income * 0.9

    eps_estimated = np.divide(earnings, total_outstanding_shares, out=np.zeros_like(
        earnings), where=total_outstanding_shares != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument

    return np.divide(buy_share_price, eps_estimated, out=np.zeros_like(buy_share_price), where=eps_estimated != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument


def market_cap(buy_share_price, total_outstanding_shares):
    '''To get market capitalization.'''

    if len(buy_share_price) != len(total_outstanding_shares):
        return 'Cant do calculation as arrays are of different lengths'

    return buy_share_price * total_outstanding_shares


def cnav(cash, ppe, total_liabilities, total_outstanding_shares):
    '''To calculate CNAV (Conservative Net Asset Value) per share.'''

    if len(cash) != len(ppe) or len(ppe) != len(total_liabilities) or len(total_liabilities) != len(total_outstanding_shares):
        return 'Cant do calculation as arrays are of different lengths'

    # I am assuming that (property investments + land) is 50% of PP&E since I don't have exact figures
    ppe = ppe * 0.5
    conservative_net_assets = (cash + ppe) - total_liabilities

    return np.divide(conservative_net_assets, total_outstanding_shares, out=np.zeros_like(conservative_net_assets), where=total_outstanding_shares != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument


def nav(total_assets, total_liabilities, total_outstanding_shares):
    '''To calculate NAV (Net Asset Value) per share.'''

    if len(total_assets) != len(total_liabilities) or len(total_liabilities) != len(total_outstanding_shares):
        return 'Cant do calculation as arrays are of different lengths'

    net_assets = total_assets - total_liabilities

    return np.divide(net_assets, total_outstanding_shares, out=np.zeros_like(net_assets), where=total_outstanding_shares != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument


def roi(cnav_share_price, nav_share_price):
    '''To calculate ROI based on CNAV and NAV per share.'''

    # Check if arrays are of the same length
    if len(nav_share_price) != len(cnav_share_price):
        return 'Cant do calculation as arrays are of different lengths'

    potential_gain = nav_share_price - cnav_share_price

    return np.divide(potential_gain, cnav_share_price, out=np.zeros_like(potential_gain), where=cnav_share_price != 0)
    # Divides the calculation anywhere where b != zero. But when b = zero, then it remains unchanged from whatever value you originally gave it in the 'out' argument
