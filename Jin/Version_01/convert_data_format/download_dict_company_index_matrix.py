
import json, pickle, os.path
from datetime import date
import pandas as pd


# To download a dictionary containing company names & company index in matrix
def download_dict_company_index_matrix(df_shareprices):

    # Get dataframe of shareprices from .pkl file
    df_shareprices = pd.read_pickle(df_shareprices)


    if os.path.exists('dict_company_index_matrix.json'):

        print('Dictionary containing company names and company indices of matric already exists.')

        # Load .son file of dictionary containing company names & company index in matrix
        dict_companytickers = json.load( open('dict_company_index_matrix.json') )


    else:

        dict_companytickers = { 
        }

        temporary_ticker = ''
        index = 0

        # Iterate through every line item in the shareprices dataframe
        for i in range(len(df_shareprices)):

            # Get every unique company name
            if str( df_shareprices['Ticker'].iloc[i] ) != temporary_ticker:    # Need to write this as each company will have thousands of shareprices lines, but we only want to fetch a list of companies

                temporary_ticker = str( df_shareprices['Ticker'].iloc[i] )

                # Append every unique company name (from shareprices dataframe) into a dictionary
                dict_companytickers[ temporary_ticker ] = index    # Can't use i since that represents looping through all the lines in df_shareprices
                index = index + 1


        with open('dict_company_index_matrix.json', 'w') as fp:
            # Download dictionary into a .json file locally
            json.dump(dict_companytickers, fp)
