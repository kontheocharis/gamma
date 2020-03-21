
# DESCRIPTION --> Wrapping all the functions / files and deciding how many times to loop through 

import pandas as pd
import time
import json
start_time = time.time()


from investing_01 import *  # Getting metrics from the 3 financial statements
from investing_02 import *  # Getting buy_share_price, sell_share_price & sell_share_price in the event of a 100% gain
from investing_03 import *  # Calculating ratios and checking whether a company fits investing strategy requirements
from investing_04 import *  # String interpolation program and getting paths and converting them into dataframes to parse through programs from investing_01.py and investing_02.py
from investing_05 import *  # Adding stocks that pass investment strategy requirement into an array, and from that array, adding stocks which fit my strategy into a second array



df_stock_ticker = pd.read_csv("stock_ticker_list_after_parse_up_to_date.csv")

size_of_stock_ticker_list = len(df_stock_ticker)


array_of_stocks_that_fulfilled_requirements = []  # The array is for investing_05.py, to input companies that pass my investment strategy criteria
array_of_stocks_that_share_price_increased = []  # The array is for investing_05.py, to input companies (that passed my investment strategy criteria), that has had their share price increased



def final_algorithm(no_of_iterations, df_stock_ticker, year_to_buy, date_to_buy, date_to_sell):

   
    for i in range(no_of_iterations):   # To loop through all the files in the .csv file

        temporary_ticker = df_stock_ticker["Stock_Ticker"].iloc[i]    # Created new variable temporary_ticker is putting each ticker in each path on my desktop to convert json files to databases
        

        # INVESTING_04.PY --> String interpolation program and getting paths and converting them into dataframes to parse through programs from investing_01.py and investing_02.py
        class_stock_ticker = stock_ticker(temporary_ticker)

        # Creating new variables and asigning variables from functions with the class from investing_04.py
        # Have to created new variables and asign values to them in order to retain the self.variable_name in investing_04.py
        df_income_statement = class_stock_ticker.string_interpolation_income_statement()    # Calling the class from investing_04.py and asgining the value to the df_income_statement variable
        df_balance_sheet = class_stock_ticker.string_interpolation_balance_sheet()  # Calling the class from investing_04.py and asgining the value to the df_balance_sheet variable
        df_cashflow_statement = class_stock_ticker.string_interpolation_cashflow_statement()    # Calling the class from investing_04.py and asgining the value to the df_cashflow_statement variable
        df_share_price = class_stock_ticker.string_interpolation_share_price()  # Calling the class from investing_04.py and asgining the value to the df_share_price variable




        # INVESTING_01.PY --> Getting metrics from the 3 financial statements
        class_analysing_json_files = analysing_json_files(df_income_statement, df_balance_sheet, df_cashflow_statement, year_to_buy, temporary_ticker)     # Calling the class from investing_01.py

        # Creating new variables and asigning variables from functions with the class from investing_01.py
        # Metrics from INCOME STATEMENT
        eps = class_analysing_json_files.eps_income_statement()
        total_outstanding_shares = class_analysing_json_files.total_outstanding_shares_income_statement()

        # Metrics from BALANCE SHEET
        cash = class_analysing_json_files.cash_balance_sheet()
        ppe_net = class_analysing_json_files.ppe_net_balance_sheet()
        total_assets = class_analysing_json_files.total_assets_balance_sheet()
        total_debt = class_analysing_json_files.total_debt_balance_sheet()
        total_liabilities = class_analysing_json_files.total_liabilities_balance_sheet()
        total_equity = class_analysing_json_files.total_equity_balance_sheet()
        
        # Metrics from CASHFLOW STATEMENT
        operating_cashflow_0 = class_analysing_json_files.operating_cashflow_0_cashflow_statement()
        operating_cashflow_1year_before = class_analysing_json_files.operating_cashflow_1year_before_cashflow_statement()
        operating_cashflow_2year_before = class_analysing_json_files.operating_cashflow_2year_before_cashflow_statement()
        free_cashflow = class_analysing_json_files.free_cashflow_cashflow_statement()



        # CHECKER --> That metrics actually contain a value (and ain't 0) --> Otherwise this would screw up calculating the ratios
        # This code is to skip any company that has 0 for any important metrics (eg total outstanding shares) as this tells me that the API ain't working right
        
        # Metrics from INCOME STATEMENT
        if eps == 0:    # If the value of EPS = 0
            continue    # Stop the loop and skip this company --> Data is probably unreliable since EPS has to be greater than 0

        if total_outstanding_shares == 0: 
            continue

        # Metrics from BALANCE SHEET
        if cash == 0: 
            continue    # Stop the loop and skip this company

        if ppe_net == 0: 
            continue

        if total_assets == 0: 
            continue

        if total_debt == 0: 
            continue

        if total_liabilities == 0: 
            continue

        if total_liabilities == 0: 
            continue
            
            



        # INVESTING_02.PY --> Getting buy_share_price, sell_share_price & sell_share_price in the event of a 100% gain
        class_analysing_share_price = analysing_share_price(df_share_price, 2, date_to_buy, date_to_sell)  # Calling the class from investing_02.py

        # Value of buy_share_price
        buy_share_price = class_analysing_share_price.buy_share_price()
        sell_share_price_end_of_period = class_analysing_share_price.sell_share_price_end_of_period()



        # CHECKER --> That buy_share_price and sell_share_price_end_of_period actually contain a value (and ain't 0) --> Otherwise we won't want to analyse these companies
        # This code is to skip any company that has 0 for the buy or sell share_price as this tells me that the company is either too young or has gone private recently
        
        if buy_share_price == 0:    # If the company is too new and does not have data from a date too far back
            continue    # Stop the loop and skip this company

        if sell_share_price_end_of_period == 0:     # If the company has gone private and does not have data from a recent date
            continue    # Stop the loop and skip this company


        share_price_of_100_gain = class_analysing_share_price.share_price_of_100_gain()     # Share price of 100% gain from buy_share_price (if applicable)

        # Value and date of final_sell_share_price
        final_sell_share_price = class_analysing_share_price.final_sell_share_price()   # Final sell_share_price -->betwen 100% gain and sell_share_price at the end of period, whichever is greater
        date_of_final_sell_share_price = class_analysing_share_price.date_of_final_sell_share_price()



        
        # INVESTING_03.PY --> Calculating ratios and checking whether a company fits investing strategy requirements
        class_calculating_ratios = calculating_ratios(eps, total_outstanding_shares, cash, ppe_net, total_assets, \
        total_debt, total_liabilities, total_equity, operating_cashflow_0, operating_cashflow_1year_before, \
        operating_cashflow_2year_before, free_cashflow, buy_share_price)

        # Calculating all the different ratios using metrics obtained from class in INVESTING_01.PY
        pe_ratio = class_calculating_ratios.pe_ratio()
        years_of_positive_operating_cashflow = class_calculating_ratios.years_of_positive_operating_cashflow()
        debt_to_equity_ratio = class_calculating_ratios.debt_to_equity_ratio()
        market_cap = class_calculating_ratios.market_cap()
        cnav1 = class_calculating_ratios.cnav1()
        nav = class_calculating_ratios.nav()
        potential_roi = class_calculating_ratios.potential_roi()


        # INVESTING_03.PY
        # Checking if a company fits investment strategy
        class_investing_strategy_requirements = investing_strategy_requirements(pe_ratio, years_of_positive_operating_cashflow, debt_to_equity_ratio, market_cap, \        
        # cnav1, nav, potential_roi, 5, 3, 1, 10**9, 1)   # For reference, numbers mean --> (pe_ratio_requirement, years_of_positive_operating_cashflow_requirement, debt_to_equity_ratio_requirement, market_cap_requirement, potential_roi_requirement)

        fulfil_requirements = class_investing_strategy_requirements.fulfil_requirements()   # Check whether a company fulfils my given investing strategy requirements




        # INVESTING_05.PY --> Adding stocks that pass investment strategy requirement into an array, and from that array, adding stocks which fit my strategy into a second array
        class_stocks_that_fulfilled_requirements = stocks_that_fulfilled_requirements(fulfil_requirements, temporary_ticker, buy_share_price, final_sell_share_price)  # To check if the company has fulfilled my investment strategy requirement (aka fulfil_requirements = 1)

        if class_stocks_that_fulfilled_requirements.add_ticker_to_array() == True:
            array_of_stocks_that_fulfilled_requirements.append(temporary_ticker)    # To add the company that fulfilled my investment strategy into an array
            
            print(temporary_ticker + " meets my investment strategy criteria.")

            # Only run the program in investing_05.py that checks if a share price increased if the stock fulfils our investing strategy requirement
            if class_stocks_that_fulfilled_requirements.did_stock_price_increase() == True:
                array_of_stocks_that_share_price_increased.append(temporary_ticker)     # To add the company that fulfilled my investment strategy AND increased in share price, into an array
                
                # Delete this when eethan leaves
                print(temporary_ticker)

    

    rate_of_accuracy = len(array_of_stocks_that_share_price_increased) / len(array_of_stocks_that_fulfilled_requirements) * 100

    print("The rate of accuracy of my investment strategy is " + str(rate_of_accuracy) + "%")
    print("There are " + str(len(array_of_stocks_that_fulfilled_requirements)) + " stocks that fulfil my investment requirement")



    
# final_algorithm(2000, df_stock_ticker, "2017", "2017-01-31", "2019-02-01")
final_algorithm(size_of_stock_ticker_list, df_stock_ticker, "2017", "2017-01-31", "2019-02-01")



print("--- %s seconds ---" % (time.time() - start_time))