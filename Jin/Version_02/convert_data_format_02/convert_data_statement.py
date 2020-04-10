

import pandas as pd, numpy as np
import json, pickle, os.path
from datetime import date



class convert_data_statement(object):
    
    def __init__(self, df_income, start_year, end_year):
        
        self.df_income = pd.read_pickle(df_income)  # Getting income statement dataframe from .pkl file 
        self.start_year = start_year
        self.end_year = end_year


    def get_dict_df_indices(self):

        if os.path.exists('dict_df_indices.json'):

            print('Dictionary of company indices of financial statements already exists.')



        else:

            global dict_df_indices
            dict_df_indices = {
            }


            for i in range(self.end_year - self.start_year):

                fiscal_year = self.start_year + i    # To increase the fiscal years that this function will loop through

                empty_dict = {  # Creating an empty dictionary to input data for a specific fiscal year. Afterwards, I will take the entire dictionary (for each year) and add it to the entire dictionary
                }
            

                for j in range(len(self.df_income)):

                    if int( self.df_income['Fiscal Year'].iloc[j] ) == fiscal_year:
                        
                        stock_ticker = str( self.df_income['Ticker'].iloc[j] )   # Getting stock ticker, which will be the key in the dictionary
                        empty_dict[stock_ticker] = j  # Asigning both the key and value into the empty dictionary (for one year)
                

                dict_df_indices['company_indices_' + str(fiscal_year)] = empty_dict     # To add the dictionary into a dictionary (which will contain many dictionaries)


            with open('dict_df_indices.json', 'w') as fp:
                json.dump(dict_df_indices, fp)  # To download dict_df_indices into a .json file locally




    '''
    def get_dict_report_date(self):

        # To output dictionary of companies of a specific fiscal year, for easy access and to save time when loading the program. 
        # This will save us time from having to loop through the entire dataframe each time we run the program.


        dict_report_date = {
        }

        for i in range(self.end_year - self.start_year):

            fiscal_year = self.start_year + i
            string_fiscal_year = 'company_indices_' + str(fiscal_year)

            empty_dict = {  # Creating an empty dictionary to input data for a specific fiscal year. Afterwards, I will take the entire dictionary (for each year) and add it to the entire dictionary
            }


            for key in dict_df_indices[string_fiscal_year]:     # Iterating through dictionary
                
                stock_ticker = key
                index = dict_df_indices[string_fiscal_year][stock_ticker]

                empty_dict[stock_ticker] = str( self.df_income['Report Date'].iloc[index] )  # Asigning both the key and value into the empty dictionary (for one year)

            dict_report_date['company_report_date_' + str(fiscal_year)] = empty_dict


        with open('dict_report_date.json', 'w') as fp:
            json.dump(dict_report_date, fp)  # To download the dictionary into a .json file locally
    '''

