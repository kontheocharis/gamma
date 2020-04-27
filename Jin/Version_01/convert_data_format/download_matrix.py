
import pandas as pd, numpy as np
import json, pickle, os.path
from datetime import date
from convert_data_format.library_functions import *     # Need to import functions written from outside this file


class download_matrix(object):
    
    def __init__(self, df_shareprices, df_income, dict_company_index_matrix, start_date, end_date):
        
        self.df_shareprices = pd.read_pickle(df_shareprices)   # Getting df_shareprices from .pkl file
        self.df_income = pd.read_pickle(df_income)  # Getting income statement dataframe from .pkl file 
        self.dict_company_index_matrix = json.load( (open(dict_company_index_matrix)) )
        self.start_date = start_date
        self.end_date = end_date


    # Create an empty matrix of correct dimensions
    def create_empty_matrix(self):
    
        # Get no of days in-between date bounds, used as the columns dimension (in the matrix)
        self.date_index = (self.end_date - self.start_date).days

        self.date_index = self.date_index + 1     # Add 1 because Wed - Mon = 3 - 1 = 2. But there are 3 days (Mon, Tues, Wed)

        # Get no of company tickers, used as the rows dimension (in the matrix)
        no_of_tickers = len(self.dict_company_index_matrix)

        # Create matrix as a numpy array
        self.matrix = np.full( (self.date_index, no_of_tickers), np.NaN, dtype = np.float32)  # (columns, rows)



    # To append shareprices data into the matrix
    def create_matrix_shareprices(self):

        # Check if matrix has already been created
        if os.path.exists('matrix.pkl'):
            print('Matrix of shareprices .pkl file already exists.')


        else:
            
            for i in range(len(self.df_shareprices)):

                # To convert date (string) into Datetime format
                selected_date = convert_string_to_date( self.df_shareprices['Date'].iloc[i] )

                # To get difference between start date and selected date (aka date_index_temp)
                date_index_temp = ( selected_date - self.start_date ).days  # And convert format from Datetime to integer


                '''READ THIS BEFORE EDITING CODE BELOW
                - Data in matrix can be called via matrix[date_index][company_index]
                - I already have an empty matrix with a size of date index & company index (columns, rows)
                - In the shareprices dataframe, there will be lines of data from dates that are too early or late (before start date or after end date)
                - The code below will ignore and skip through lines in the dataframe
                '''

                # If the selected date (from dataframe of shareprices) is within the range of start and end date (date index of matrix)
                if date_index_temp < self.date_index: 

                    # To get the company_index (in the matrix) of selected company ticker (string)
                    company_index = get_companyindex( self.dict_company_index_matrix, self.df_shareprices['Ticker'].iloc[i] )

                    
                    # Asign the shareprice to an index in the matrix
                    self.matrix[date_index_temp][company_index] = self.df_shareprices['Close'].iloc[i]    # matrix[date_index_temp][company_index]


            output = open('matrix.pkl', 'wb')   # Downloads the (now filled) matrix file locally
            pickle.dump(self.matrix, output)
            output.close()

