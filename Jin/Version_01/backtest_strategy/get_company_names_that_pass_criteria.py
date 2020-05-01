
import numpy as np

# To ignore all RuntimeWarning errors (that are caused by np.nan to fill up spaces in the matrix)
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


def get_company_names_that_pass_criteria(dict_investment_criteria, array_company_names_with_sufficient_data,
                                         array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi):
    '''To get list of company names that pass investment criteria.'''

    '''
    PSEUDOCODE
    1. Take all the metrics (of companies with available data) and check if metric passes investment criteria
    2. Get a list of company names of which metric passes investment criteria
    '''

    # Check if debt-to-equity ratio is less than 1
    array_debt_to_equity_ratio = np.less(
        array_debt_to_equity_ratio, dict_investment_criteria['debt_to_equity_ratio'])

    '''Don't need to write a condition for array_positive_operating_cashflow because all the values are already in booleans (TRUE, FALSE)'''

    # Check if price-to-earnings ratio is less than 15
    array_price_to_earnings_ratio = np.less(
        array_price_to_earnings_ratio, dict_investment_criteria['price_to_earnings_ratio'])

    # Check if market capitalization is greater than $1 billion
    array_market_cap = np.greater(
        array_market_cap, dict_investment_criteria['market_cap'])

    # Check if CNAV is less than NAV (which it should already be due to how both ratios are calculated)
    array_cnav = np.less(array_cnav, array_nav)

    # Check if return on investment is more than 2 (aka 100% gain)
    array_roi = np.greater(array_roi, dict_investment_criteria['roi'])

    # To get the indices of the stocks that meet all my criterias
    indices_stocks_pass_criteria = np.where((array_debt_to_equity_ratio) &  # Where all these ratios conditions == True
                                            (array_price_to_earnings_ratio) &
                                            (array_market_cap) &
                                            (array_cnav) &
                                            (array_roi))

    # Convert tuple to np.array
    indices_stocks_pass_criteria = indices_stocks_pass_criteria[0]

    # From list of indices, get a list of company names that pass investment criteria
    company_names_that_pass_criteria = np.take(
        array_company_names_with_sufficient_data, indices_stocks_pass_criteria)
    return company_names_that_pass_criteria
