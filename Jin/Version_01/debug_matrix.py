from datetime import date
import json
import pandas as pd
import numpy as np


'''
EXPECTED DATA
matrix[2009-08-26][GOOG] --> 116.4467 close price
matrix[2015-11-09][BLK] --> 349.57 close price
'''


def debug_converting_df_to_matrix(matrix_filename, dict_company_index_matrix_filename, selected_date, company, expected_value):

    # Open all the newly created and formatted data files
    matrix = pd.read_pickle(matrix_filename)
    dict_company_index_matrix = json.load(
        (open(dict_company_index_matrix_filename)))

    # Get date index and company index, from Datetime date and company name (string)
    date_index = (selected_date - date(2007, 1, 3)).days

    # Convert expected value into the same format as data in matrix
    expected_value = np.float32(expected_value)

    # Get value from matrix
    company_index = dict_company_index_matrix[company]
    value_to_check = matrix[date_index][company_index]

    # If value_to_check equals to the condition (aka expected value), nothing happens. Else, return an AssertionError
    if value_to_check == expected_value:
        print('Debugging test checks out. The matrix was created correctly.')

    else:
        print('Something is wrong. The matrix was created incorrectly!')


'''
EXPECTED DATA
Matrix start date: 2007-01-03
Buy date: 2011-05-06
Sell date: 2013-05-07
Date index of buy date: (buy_date - matrix_start_date).days

Company name: ATW
Shareprice gain? Yes
Company index of matrix: 1121
Date index with shareprice gain: 2316
'''


def get_shareprice_in_matrix(company_name, selected_date):
    '''To get shareprice data from company name and date (instead of company index, date index).'''

    matrix = pd.read_pickle('matrix.pkl')

    # Get date index from date input
    matrix_start_date = date(2007, 1, 3)
    date_index = (selected_date - matrix_start_date).days

    # Get company index from company name input
    dict_company_index_matrix = json.load(
        (open('dict_company_index_matrix.json')))
    company_index = dict_company_index_matrix[company_name]

    shareprice = matrix[date_index][company_index]
    print(shareprice)


get_shareprice_in_matrix('ATW', date(2013, 5, 7))
