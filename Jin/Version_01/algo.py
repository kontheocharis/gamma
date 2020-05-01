
from datetime import date

# Get 3 lists of companies of data that is available at buy date and sell date --> (buy shareprices data, sell shareprices data, financial statement data)
from calculate_metrics.available_data_at_date import AvailableDataAtDate, compare_arrays_and_return_matches

# Get array of metrics
from calculate_metrics.get_metrics import get_array_company_index_of_financial_statement, get_array_metric

# Get array shareprices
from calculate_metrics.get_shareprices import GetShareprices

# Get formulas of ratios
from calculate_metrics.formula_of_ratios import debt_to_equity_ratio, positive_operating_cashflow, price_to_earnings_ratio, market_cap, cnav, nav, roi

# Get variables (DICT_INVESTMENT_CRITERIA) with investment criteria to input as parameters into the functions below
from backtest_strategy.investment_criteria import DICT_INVESTMENT_CRITERIA

# Get list of company names that pass criteria
from backtest_strategy.get_company_names_that_pass_criteria import get_company_names_that_pass_criteria

# Get array of shareprices that had 100% gain
from backtest_strategy.check_shareprices import CheckShareprices


def algo(matrix_start_date, buy_date, sell_date):
    '''Run backtesting on fundamental investing strategies.'''

    '''PSEUDOCODE
    1. Get list of company names that has data available for financial statements
    2. Get list of company names that has data available for buy shareprices
    3. Get list of company names that has data available for sell shareprices
    4. Get a list of company names that has data for BOTH financial statements and shareprices
    '''

    A = AvailableDataAtDate('income.pkl', 'dict_df_statement_index.json',
                            'matrix.pkl', matrix_start_date, 'dict_company_index_matrix.json')

    # Get list of company names that has data available for buy shareprices
    array_available_shareprice_data_at_buy_date = A.available_shareprice_data_at_selected_date(
        buy_date)

    # Get list of company names that has data available for sell shareprices
    array_available_shareprice_data_at_sell_date = A.available_shareprice_data_at_selected_date(
        sell_date)

    # Get list of company names that has data available for financial statements
    array_available_financial_statement_data_at_buy_date = A.available_financial_statement_data_at_selected_date(
        buy_date)

    # Compare the 3 lists of company names --> Array of company names that has data for all 3
    array_company_names_with_sufficient_data = compare_arrays_and_return_matches(array_available_shareprice_data_at_buy_date,
                                                                                 array_available_shareprice_data_at_sell_date, array_available_financial_statement_data_at_buy_date)

    # Get no of companies there is with sufficient data
    no_of_companies_with_sufficient_data = len(
        array_company_names_with_sufficient_data)

    print(
        f'There is sufficient date for {str(no_of_companies_with_sufficient_data)} companies.')

    '''PSEUDOCODE
    5. Take that list of company names and get data for metrics of financial statements
    '''

    # Get fiscal year of buy date
    buy_fiscal_year = buy_date.year

    # Get array of company index of financial statements from company name (ie get value from key)
    company_index_of_financial_statement: list = get_array_company_index_of_financial_statement(
        'income.pkl', 'dict_df_statement_index.json', buy_fiscal_year, array_company_names_with_sufficient_data)

    # Fetch needed metrics from income statement
    net_income: list = get_array_metric(
        'income.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Net Income')
    total_outstanding_shares: list = get_array_metric(
        'income.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Shares (Diluted)')

    # Fetch needed metrics from balance sheet
    cash: list = get_array_metric('balance.pkl', 'dict_df_statement_index.json',
                                  company_index_of_financial_statement, 'Cash, Cash Equivalents & Short Term Investments')

    array_ppe: list = get_array_metric('balance.pkl', 'dict_df_statement_index.json',
                                       company_index_of_financial_statement, 'Property, Plant & Equipment, Net')

    array_total_assets = get_array_metric(
        'balance.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Total Assets')

    array_shortterm_debt = get_array_metric(
        'balance.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Short Term Debt')

    longterm_debt: list = get_array_metric(
        'balance.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Long Term Debt')

    total_liabilities: list = get_array_metric(
        'balance.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Total Liabilities')

    array_total_equity = get_array_metric(
        'balance.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Total Equity')

    # Fetch needed metrics from cashflow statement
    array_operating_cashflow = get_array_metric(
        'cashflow.pkl', 'dict_df_statement_index.json', company_index_of_financial_statement, 'Net Cash from Operating Activities')

    '''PSEUDOCODE
    6. Take that list of company names and get data for buy and sell shareprices
    '''

    B = GetShareprices('dict_company_index_matrix.json',
                       matrix_start_date, 'matrix.pkl')

    # Get array of company index of matrix from company name (ie get value from key)
    array_company_index_of_matrix = B.get_array_company_index_of_matrix(
        array_company_names_with_sufficient_data)

    # Get array of shareprices at buy date and sell date
    array_buy_shareprices = B.get_array_shareprices(
        buy_date, array_company_index_of_matrix)
    array_sell_shareprices = B.get_array_shareprices(
        sell_date, array_company_index_of_matrix)

    '''PSEUDOCODE
        7. Get arrays metrics and calculate ratios that are needed
        '''

    # Get np.array of ratios
    array_debt_to_equity_ratio = debt_to_equity_ratio(
        array_shortterm_debt, longterm_debt, array_total_equity)

    array_positive_operating_cashflow = positive_operating_cashflow(
        array_operating_cashflow)

    array_price_to_earnings_ratio = price_to_earnings_ratio(
        net_income, total_outstanding_shares, array_buy_shareprices)

    array_market_cap = market_cap(
        array_buy_shareprices, total_outstanding_shares)

    array_cnav = cnav(cash, array_ppe,
                      total_liabilities, total_outstanding_shares)

    array_nav = nav(array_total_assets, total_liabilities,
                    total_outstanding_shares)

    array_roi = roi(array_cnav, array_nav)

    '''PSEUDOCODE
        8. Take arrays of ratios and get a list of companies that meet requirements
        9. Take arrays of ratios and get a list of company index that meet requirements
        '''

    # Get list of company names that pass investment criteria
    array_company_names_that_pass_criteria = get_company_names_that_pass_criteria(DICT_INVESTMENT_CRITERIA, array_company_names_with_sufficient_data,
                                                                                  array_debt_to_equity_ratio, array_positive_operating_cashflow, array_price_to_earnings_ratio, array_market_cap, array_cnav, array_nav, array_roi)

    print(
        f'There are {str(len(array_company_names_that_pass_criteria))} companies that passed the investment criteria.')

    # Check if there are no data of shareprices at either buy date or sell date
    if len(array_company_names_that_pass_criteria) == 0:
        print('There is no shareprice data for this date. Choose another date.')
        return

    '''PSEUDOCODE
    10. Get list of company index (of companies that meet requirements)
    11. Get list of buy shareprices (of companies that meet requirements)

    12. Get list of company names (from companies that passed criteria)
    Of which there was 100% gain in shareprice between period
    Or an overall gain in shareprice at the end of the period
    '''

    '''Using the same class (get_shareprices.py) as above'''
    # Get list of company index (of companies that meet requirements)
    array_company_index_of_matrix = B.get_array_company_index_of_matrix(
        array_company_names_that_pass_criteria)

    # Get list of buy shareprices (of companies that meet requirements)
    array_buy_shareprices = B.get_array_shareprices(
        buy_date, array_company_index_of_matrix)

    C = CheckShareprices('matrix.pkl', matrix_start_date, buy_date, sell_date)

    # Get list of company names that shareprice increased (either 100% shareprice gain or shareprice increased at end of period)
    array_company_names_with_shareprices_gain = C.get_company_names_that_shareprice_increased(
        array_company_names_that_pass_criteria, array_company_index_of_matrix, array_buy_shareprices)

    print(
        f'The shareprice of {str(len(array_company_names_with_shareprices_gain))} companies increased.')

    # Get list of company index and date index that shareprice increased
    array_company_index_with_shareprices_gain = C.get_company_index_that_shareprices_increased()
    array_date_index_with_shareprices_gain = C.get_date_index_with_shareprices_gain()

    # Get list of company names that shareprice decreased
    array_company_names_without_shareprice_gain = C.get_company_names_without_shareprice_gain()

    print(
        f'The shareprice of {str(len(array_company_names_without_shareprice_gain))} companies decreased.')

    # Calculate the rate of accuracy of investment strategy
    accuracy_rate = (len(array_company_names_with_shareprices_gain) /
                     len(array_company_names_that_pass_criteria)) * 100

    print(f'The rate of accuracy is {str(int(accuracy_rate))}%.')


algo(date(2007, 1, 3), date(2011, 5, 11), date(2015, 3, 10))
