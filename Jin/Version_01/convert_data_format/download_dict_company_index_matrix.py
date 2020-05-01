
import json
import pickle
import os.path
import pandas as pd


def download_dict_company_index_matrix(df_shareprices):
    '''To download a dictionary containing company names & company index in matrix.'''

    # Get dataframe of shareprices from .pkl file
    df_shareprices = pd.read_pickle(df_shareprices)

    if os.path.exists('dict_company_index_matrix.json'):
        print('Dictionary containing company names and company indices of matric already exists.')

        # Load .son file of dictionary containing company names & company index in matrix
        dict_companytickers = json.load(open('dict_company_index_matrix.json'))

    else:
        dict_companytickers = {
        }
        temporary_ticker = ''
        index = 0

        # Iterate through every line item in the shareprices dataframe
        for i in range(len(df_shareprices)):

            # Get every unique company name
            # Need to write this as each company will have thousands of shareprices lines, but we only want to fetch a list of companies
            if str(df_shareprices['Ticker'].iloc[i]) != temporary_ticker:
                temporary_ticker = str(df_shareprices['Ticker'].iloc[i])

                # Append every unique company name (from shareprices dataframe) into a dictionary
                # Can't use i since that represents looping through all the lines in df_shareprices
                dict_companytickers[temporary_ticker] = index
                index = index + 1

        with open('dict_company_index_matrix.json', 'w') as fp:
            # Download dictionary into a .json file locally
            json.dump(dict_companytickers, fp)
