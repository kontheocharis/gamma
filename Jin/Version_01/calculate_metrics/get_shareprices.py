import json
import pandas as pd
import numpy as np


class GetShareprices:

    def __init__(self, dict_companytickers, matrix_start_date, matrix):

        # Open files containing data relating to matrix
        self.dict_companytickers = json.load((open(dict_companytickers)))
        self.matrix = pd.read_pickle(matrix)
        self.matrix_start_date = matrix_start_date

    def get_array_company_index_of_matrix(self, array_company_names_with_sufficient_data):
        '''To return an array containing company index of matrix, for companies that have sufficient data (for both shareprices and financial statement).'''

        '''PSEUDOCODE
        1. Get company index of matrix from list company names with sufficient data
        '''

        array_company_index_of_matrix = []

        for i in range(len(array_company_names_with_sufficient_data)):

            # Get company index for each company that has sufficient data
            temp_company_name = array_company_names_with_sufficient_data[i]
            temp_company_index = self.dict_companytickers[temp_company_name]

            # Return an array with company index of companies with sufficient data
            array_company_index_of_matrix.append(temp_company_index)

        return np.asarray(array_company_index_of_matrix)

    def get_array_shareprices(self, selected_date, array_company_index_of_matrix):
        '''To get an array of shareprices at the buy date and sell date (of companies that have sufficient data).'''

        array_shareprices_at_selected_date = []

        # Get difference in days from selected date and fixed start date in matrix
        date_index = (selected_date - self.matrix_start_date).days

        for i in range(len(array_company_index_of_matrix)):

            # Get company index of each company (of companies that have sufficient data)
            temp_company_index = array_company_index_of_matrix[i]

            # Get shareprice of each company
            temp_shareprice = self.matrix[date_index][temp_company_index]

            # Return an array with shareprices at selected date
            array_shareprices_at_selected_date.append(temp_shareprice)

        return np.asarray(array_shareprices_at_selected_date)
