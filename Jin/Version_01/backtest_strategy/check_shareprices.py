
import numpy as np
import pandas as pd
import datetime


# To get lists of company names, company index & date index of companies that shareprice increased (and also met investment criteria)
class CheckShareprices:

    def __init__(self, matrix, matrix_start_date, buy_date, sell_date):
        '''PSEUDOCODE
        1. Get a list of company names that have 100% increase in shareprice or shareprice increase at end of period
        2. Get a list of company index (that shareprice increased)
        3. Get a list of date index (that shareprice increased)
        4. Get a list of company names and company index that shareprice did not increase at all (for both 100% shareprice gain and shareprice increase at end of period)
        '''

        # Open files containing data relating to matrix
        self.matrix = pd.read_pickle(matrix)
        self.matrix_start_date = matrix_start_date
        self.buy_date = buy_date
        self.sell_date = sell_date

    def get_company_names_that_shareprice_increased(self, array_company_names_that_pass_criteria, array_company_index_of_matrix, array_buy_shareprices):
        '''To get list of company names that shareprice increased - either sell shareprice is greater than buy shareprice of a 100% gain during period.'''

        '''PSEUDOCODE
        1. Check if there is a 100% shareprice gain in between buy date and sell date
        2. If there is, get a list of company names, company index and date index
        '''

        self.array_company_names_that_pass_criteria = array_company_names_that_pass_criteria
        self.array_company_index_of_matrix = array_company_index_of_matrix
        self.array_buy_shareprices = array_buy_shareprices

        # Get the date range (ie no of days between buy and sell dates)
        days_inbetween = (self.sell_date - self.buy_date).days + 1

        # Get temporary date index of matrix, of buy date (to start from), which I will increase in the iteration
        temp_buy_date_index = (self.buy_date - self.matrix_start_date).days

        # Create empty arrays that this class will later return
        self.array_company_names_with_shareprices_gain = []
        self.array_company_index_with_shareprices_gain = []
        self.array_date_index_with_shareprices_gain = []

        self.array_company_names_without_shareprice_gain = []

        for i in range(len(self.array_company_index_of_matrix)):

            # Iterate through every company (that met criteria)
            temp_company_index = int(self.array_company_index_of_matrix[i])
            temp_buy_share_price = array_buy_shareprices[i]
            does_shareprice_increase = False

            # Check if there is a 100% gain in shareprice for every company
            for j in range(days_inbetween):

                # Don't need to write == True, since the if statement implies that already
                if np.isnan(self.matrix[temp_buy_date_index + j][temp_company_index]):
                    continue

                # If there is no data for a date, it'll be NaN
                if self.matrix[temp_buy_date_index + j][temp_company_index] > (2 * temp_buy_share_price):

                    # If there is a 100% gain in shareprice, return arrays of company names, company index & date index
                    self.array_company_names_with_shareprices_gain.append(
                        array_company_names_that_pass_criteria[i])
                    self.array_company_index_with_shareprices_gain.append(
                        array_company_index_of_matrix[i])
                    self.array_date_index_with_shareprices_gain.append(
                        temp_buy_date_index + j)

                    does_shareprice_increase = True
                    break

            '''PSEUDOCODE
            3. If there isn't a 100% shareprice gain, check if the shareprice at sell date is more than the shareprice at buy date
            4. If there is, get a list of company names, company index and date index
            '''

            if not does_shareprice_increase:

                # Check if the shareprice at sell date is more than shareprice at buy date
                date_index_at_sell_date = temp_buy_date_index + days_inbetween
                sell_shareprice = self.matrix[date_index_at_sell_date][temp_company_index]

                if sell_shareprice > temp_buy_share_price:

                    # Using i as index because the index within array (of stocks that pass criteria) is different from the company index. You will get an error if you write [temp_company_index] instead of [i]
                    self.array_company_names_with_shareprices_gain.append(
                        array_company_names_that_pass_criteria[i])
                    self.array_company_index_with_shareprices_gain.append(
                        array_company_index_of_matrix[i])
                    self.array_date_index_with_shareprices_gain.append(
                        date_index_at_sell_date)

                    does_shareprice_increase = True

            '''PSEUDOCODE
            5. If a company doesn't have a 100% shareprice gain or increase in shareprice at end of period, get a list of company names and company index
            '''

            if not does_shareprice_increase:

                self.array_company_names_without_shareprice_gain.append(
                    array_company_names_that_pass_criteria[i])

        return self.array_company_names_with_shareprices_gain

    def get_company_index_that_shareprices_increased(self):
        '''To get list of company index of companies that shareprice increased.'''
        return self.array_company_index_with_shareprices_gain

    def get_date_index_with_shareprices_gain(self):
        '''To get list of date index of companies that shareprice increased.'''
        return self.array_date_index_with_shareprices_gain

    def get_company_names_without_shareprice_gain(self):
        '''To get list of company name that shareprice did not increase (in other words, decreased).'''
        return self.array_company_names_without_shareprice_gain
