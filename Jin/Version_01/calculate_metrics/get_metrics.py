
import pandas as pd
import json
import numpy as np


def get_array_company_index_of_financial_statement(df_statement, dict_df_indices, fiscal_year, array_company_names_with_sufficient_data):
    '''Get list of company index of companies (that financial statements data is available for).'''

    # Open and load (any one of three) financial statement and dictionary (containing company names and financial statement indices)
    df_statement = pd.read_pickle(df_statement)
    dict_df_indices = json.load((open(dict_df_indices)))

    array_company_index_of_financial_statement = []

    # Getting the name of dictionary for a specific fiscal year (to access data within a dictionary holding many dictionaries)
    fiscal_year = 'company_indices_' + str(fiscal_year)
    dict_for_fiscal_year = dict_df_indices[fiscal_year]

    for i in range(len(array_company_names_with_sufficient_data)):

        # Get company index from company name (ie get value from key)
        temp_company_index = dict_for_fiscal_year[array_company_names_with_sufficient_data[i]]

        # Return an array of company index
        array_company_index_of_financial_statement.append(temp_company_index)

    return np.asarray(array_company_index_of_financial_statement)


def get_array_metric(df_statement, dict_df_indices, array_company_index_of_financial_statement, metric):
    '''Get list of metrics from financial statements.'''

    # Open and load (any one of three) financial statement and dictionary (containing company names and financial statement indices)
    df_statement = pd.read_pickle(df_statement)
    dict_df_indices = json.load((open(dict_df_indices)))

    array_metrics = []

    for i in range(len(array_company_index_of_financial_statement)):

        # Get metric for each company in the financial statement
        temp_company_index = array_company_index_of_financial_statement[i]
        temp_metric = df_statement[metric].iloc[temp_company_index]

        # Add the metric for each company to an array
        array_metrics.append(float(temp_metric))

    return np.asarray(array_metrics)
