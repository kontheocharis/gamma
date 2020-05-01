
import json
import datetime
import math
import numpy as np
import pandas as pd

from calculate_metrics.library_functions import get_key_from_value_in_dict


# To get list of company names of which shareprices and financial statement data is available, at buy date and sell date
class AvailableDataAtDate:

    def __init__(self, df_income, dict_df_indices, matrix, matrix_start_date, dict_companytickers):

        # Open dictionary containing company index & df statement index
        self.df_income = pd.read_pickle(df_income)
        self.dict_df_indices = json.load((open(dict_df_indices)))

        # Open files containing data relating to matrix
        self.matrix = pd.read_pickle(matrix)
        self.matrix_start_date = matrix_start_date
        self.dict_companytickers = json.load((open(dict_companytickers)))

    def available_shareprice_data_at_selected_date(self, selected_date: datetime):
        '''To get a list of company names that has shareprice data available at selected (buy or sell) date.'''

        '''PSEUDOCODE
        1. Get data in matrix at a specific date
        2. Get list of company index (of matrix data) available at a specific date
        3. From the list of company index, get a list of company names
        '''

        self.selected_date = selected_date

        array_company_index = []
        array_company_names = []

        # Get data from matrix at a specific date
        date_index = (self.selected_date - self.matrix_start_date).days
        data = self.matrix[date_index]

        # Get list of company index of matrix data available at a specific date
        for i in range(len(data)):

            # If the data point contains data (aka isn't NaN)
            if not math.isnan(data[i]):

                array_company_index.append(i)

        # From the list of company index, get a list of company names
        for j in range(len(array_company_index)):

            # For every company index, get the company name linked to that company index
            temp_value = array_company_index[j]
            temp_key = get_key_from_value_in_dict(
                temp_value, self.dict_companytickers)

            # Add the company name to an array
            array_company_names.append(temp_key)

        return np.asarray(array_company_names)  # Convert array to np.array

    def available_financial_statement_data_at_selected_date(self, selected_date):
        '''To get a list of company names that has financial statements data available at selected buy date.'''

        '''PSEUDOCODE
        1. Get name of dictionary (for one fiscal year), to access data in financial statement at a specific fiscal year
        2. Get list of company names (of financial statement data) available at a specific fiscal year
        '''

        # Get the name of dictionary of a specific fiscal year to access data
        self.selected_fiscal_year = selected_date.year
        # (Since the dictionary has many dictionaries with financial statement data from many years)
        self.selected_fiscal_year = 'company_indices_' + \
            str(self.selected_fiscal_year)

        # Get list of company names at a specific fiscal year
        array_company_names = self.dict_df_indices[self.selected_fiscal_year].keys(
        )
        array_company_names = list(array_company_names)

        return np.asarray(array_company_names)


def compare_arrays_and_return_matches(array_shareprice_data_at_buy_date, array_shareprice_data_at_sell_date, array_financial_statement_data_at_buy_date):
    '''To compare the 3 arrays and return an array of company name matches.'''

    # Convert all the arrays to sets and finding matches between them
    array = set(array_shareprice_data_at_buy_date) & set(
        array_shareprice_data_at_sell_date) & set(array_financial_statement_data_at_buy_date)

    # Convert set to a np.array
    return np.asarray(list(array))
