
# Takes 484 seconds to load

import pandas as pd, numpy as np
import json, pickle, os.path
from datetime import date
from convert_data_format_02.library_functions import *     # Need to import functions written from outside this file



class convert_data_shareprices(object):
    
    def __init__(self, df_shareprices, df_income, start_date, end_date):
        
        self.df_shareprices = pd.read_pickle(df_shareprices)   # Getting df_shareprices from .pkl file
        self.df_income = pd.read_pickle(df_income)  # Getting income statement dataframe from .pkl file 
        self.start_date = start_date
        self.end_date = end_date



    def create_dict_companytickers(self):

        global dict_companytickers  # Setting this as a global variable to use throughout the methods in this class

        if os.path.exists('dict_companytickers.json'):

            print('Dictionary of company tickers already exists.')

            dict_companytickers = json.load( open('dict_companytickers.json') )     # Load .json file of dictionary of company tickers


        else:

            dict_companytickers = {     # Creating an empty dictionary to add keys and values in the iteration
            }


            temporary_ticker = ''   # Empty string to input newly found stock ticker later in the loop
            index = 0

            for i in range(len(self.df_shareprices)):

                if str( self.df_shareprices['Ticker'].iloc[i] ) != temporary_ticker:    # If the selected string is different from a previously selected string

                    temporary_ticker = str( self.df_shareprices['Ticker'].iloc[i] )

                    dict_companytickers[ temporary_ticker ] = index    # Can't use i since that represents looping through all the tickers
                    index = index + 1


            with open('dict_companytickers.json', 'w') as fp:
                json.dump(dict_companytickers, fp)  # To download dict_companytickers into a .json file locally




    def create_empty_matrix(self):
    
        date_index = (self.end_date - self.start_date).days  # Getting the number of days in-between date bounds to create matrix

        date_index = date_index + 10  # Adding 10 because I'd rather have more date_index columns than less (when I'm asining values in the matrix later)

        no_of_tickers = len(dict_companytickers)  # Getting the number of company tickers to create matrix


        global matrix
        matrix = np.full( (date_index, no_of_tickers), np.NaN, dtype = np.float32)  # Creating the matrix as a numpy multi-dimensional array
        # (columns, rows)



    def create_matrix_shareprices(self):


        if os.path.exists('matrix.pkl'):

            print('Matrix of share prices .pkl file already exists.')


        else:

            for i in range(len(self.df_shareprices)):

                selected_date = convert_string_to_date( self.df_shareprices['Date'].iloc[i] )    # Converting date (string) into Datetime format

                date_index = selected_date - self.start_date   # Difference between start date and selected date
                date_index = date_index.days    # To convert format from Datetime into an integer
                
                company_index = get_companyindex( dict_companytickers, self.df_shareprices['Ticker'].iloc[i] )    # To get the company_index (in the matrix) of selected company ticker (string)


                # matrix[date_index][company_index]
                matrix[date_index][company_index] = self.df_shareprices['Close'].iloc[i]     # To asign the share price to a value in the matrix
                # The matrix has 4,460 date_index & 2,062 company_index --> 4,460 columns and 2,062 rows


            output = open('matrix.pkl', 'wb')   # Downloads the (now filled) matrix file locally
            pickle.dump(matrix, output)
            output.close()

