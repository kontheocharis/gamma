
import pandas as pd, json
import numpy as np




def get_metric_income(df_statement, dict_df_indices, fiscal_year, metric):


    df_statement = pd.read_pickle( df_statement )   # Loading the df of financial statement
    dict_df_indices = json.load( (open(dict_df_indices)) )  # Loading the stock ticker dictionary


    array_metrics = np.zeros(15000)    # Creating an empty np.array with 15,000 elements
    fiscal_year = 'company_indices_' + str(fiscal_year)

    counter = 0     # This kind of acts as [i] and represents the position of elements in the np.array


    for key in dict_df_indices[fiscal_year]:    # Loop through all the indices (in one fiscal year of indices)

        temporary_value = dict_df_indices[fiscal_year][key]     # Temporary index of a stock in the df_statement
        temporary_metric = df_statement[metric].iloc[ temporary_value ]

        array_metrics[counter] = float(temporary_metric)    # Appending the value of a metric into the np.array

        counter = counter + 1   # Add 1 to shift the placement of value in the np.array
        


    return array_metrics
     # np.array is in the order of dict_df_indices

    