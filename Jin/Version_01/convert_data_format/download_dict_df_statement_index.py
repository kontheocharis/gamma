
import json
import pickle
import os.path
import pandas as pd


def download_dict_df_statement_index(df_income, start_year, end_year):
    '''To download dictionary containing company index & df statement index.'''

    # Get income statement dataframe from .pkl file
    df_income = pd.read_pickle(df_income)

    # Check if dictionary has already been downloaded
    if os.path.exists('dict_df_statement_index.json'):
        print('Dictionary of company indices of financial statements already exists.')

    else:
        dict_df_indices = {
        }

        for i in range(end_year - start_year):

            # Iterate through all the fiscal years between the start and end year
            fiscal_year = start_year + i

            # Create an empty dictionary to input data for a specific fiscal year
            empty_dict = {
            }

            for j in range(len(df_income)):

                if int(df_income['Fiscal Year'].iloc[j]) == fiscal_year:
                    # Get and asign the company name (key) and df statement index (value) into empty dictionary (for one year)
                    stock_ticker = str(df_income['Ticker'].iloc[j])
                    empty_dict[stock_ticker] = j

            # Take the entire dictionary (for each year) and add it to the main dictionary (that contain many dictionaries)
            dict_df_indices['company_indices_' + str(fiscal_year)] = empty_dict

        with open('dict_df_statement_index.json', 'w') as fp:
            json.dump(dict_df_indices, fp)
