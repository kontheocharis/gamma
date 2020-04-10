import json
import pandas as pd 
import numpy as np

from get_shareprices_04.library_functions import *


class get_shareprices(object):
    
    def __init__(self, dict_df_indices, dict_companytickers, matrix_start_date, matrix, buy_date, sell_date):

        self.dict_df_indices = json.load( (open(dict_df_indices)))
        self.dict_companytickers = json.load( (open(dict_companytickers)) )

        self.matrix = pd.read_pickle(matrix)
        self.matrix_start_date = matrix_start_date

        self.buy_date = buy_date  # Selected date to get share price from
        self.sell_date = sell_date



    def get_buy_shareprices(self):

        array_buy_shareprices = np.zeros(15000)    # Creating an empty np.array with 15,000 elements
        counter = 0

        date_index = (self.buy_date - self.matrix_start_date).days   # Difference in days from selected date and fixed start date in matrix

        fiscal_year = self.buy_date.year
        fiscal_year = 'company_indices_' + str(fiscal_year)  # Asining the name of year dictionary within the dictionary of df_indices


        for key in self.dict_df_indices[fiscal_year]: 

            company_index = get_company_index(key, self.dict_companytickers)    # Getting the company_index by calling a function that I wrote outside this file

            temporary_buy_shareprice = self.matrix[date_index][company_index]   # Getting the buy share price at a specific date (date_index), of a specific company (company_index)

            array_buy_shareprices[counter] = temporary_buy_shareprice   # Appending the buy share price to a np.array

            counter = counter + 1

        return array_buy_shareprices




    def get_sell_shareprices(self):

        array_buy_shareprices = np.zeros(15000)    # Creating an empty np.array with 15,000 elements
        counter = 0

        date_index = (self.sell_date - self.matrix_start_date).days   # Difference in days from selected date and fixed start date in matrix

        fiscal_year = self.sell_date.year
        fiscal_year = 'company_indices_' + str(fiscal_year)  # Asining the name of year dictionary within the dictionary of df_indices


        for key in self.dict_df_indices[fiscal_year]: 


            company_index = get_company_index(key, self.dict_companytickers)    # Getting the company_index by calling a function that I wrote outside this file

            temporary_buy_shareprice = self.matrix[date_index][company_index]   # Getting the buy share price at a specific date (date_index), of a specific company (company_index)

            array_buy_shareprices[counter] = temporary_buy_shareprice   # Appending the buy share price to a np.array

            counter = counter + 1

        return array_buy_shareprices




    def get_array_company_index(self):

        array_company_index = np.zeros(15000)    # Creating an empty np.array with 15,000 elements
        counter = 0


        fiscal_year = self.sell_date.year
        fiscal_year = 'company_indices_' + str(fiscal_year)  # Asining the name of year dictionary within the dictionary of df_indices


        for key in self.dict_df_indices[fiscal_year]: 


            company_index = get_company_index(key, self.dict_companytickers)    # Getting the company_index by calling a function that I wrote outside this file

            array_company_index[counter] = company_index  

            counter = counter + 1

        return array_company_index




    def get_100_shareprice(self, array_buy_shareprices, array_company_index):

        days_inbetween = (self.sell_date - self.buy_date).days  # Getting the date range (ie number of days between buy and sell dates)
        buy_date_index = (self.buy_date - self.matrix_start_date).days  # Getting the date_index to start from

        array_100_shareprices = np.zeros(15000)    # Creating an empty np.array with 15,000 elements

        counter = 0     # Counter acts as [i] for np.array of 100_shareprices
        


        for i in range(len(array_company_index)):   # Iterating through every company
            
            temporary_company_index = array_company_index[i]    # Getting company index
            temporary_company_index = int(temporary_company_index)  # Converting numpy.float64 to integer
            temporary_buy_share_price = array_buy_shareprices[i]    # Getting buy share price of each company

            is_100_shareprice = False


            for j in range(days_inbetween):    # Iterating through date range (ie dates in between buy and sell dates)
                
                if self.matrix[buy_date_index + j][temporary_company_index] > (2 * temporary_buy_share_price):  # If the buy share price of an element between the date range > 2 times the initial buy share price
                    
                    is_100_shareprice = True

                    array_100_shareprices[counter] = self.matrix[buy_date_index + j][temporary_company_index]   # Appending share price of 100% gain to np.array
                    continue
                
                

            if is_100_shareprice == False:  # If there is no share price within date range that is 100% more than initial buy share price

                array_100_shareprices[counter] = 0


            counter = counter + 1   # Counter acts as [i] for np.array of 100_shareprices

        
        return array_100_shareprices
                    
