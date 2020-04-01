
# This take 384 seconds to load

import pickle, json, pandas as pd
from datetime import date



def get_companyindex(dict_companytickers, stock_ticker):    # Note that the stock ticker has to be in the format of a string

    key_list = list(dict_companytickers.keys())     # Creating a key_list and val_list to get key from value
    val_list = list(dict_companytickers.values())   # In this case, it is to get company_index from the name of company
    
    company_index = val_list[key_list.index(stock_ticker)]  # To get company_index from the stock ticker (string)
    
    return company_index



def convert_string_to_date(date_string):

    date_string = date_string.split('-')    # Splitting string (date) into an array
    
    date_string = date( int(date_string[0]), int(date_string[1]), int(date_string[2]) )     # Have to convert each string (within the array) to an integer to input it into Datetime format 

    return date_string



def create_matrix_shareprices(matrix, df_shareprices, dict_companytickers, first_date):


    for i in range(len(df_shareprices)):

        selected_date = convert_string_to_date( df_shareprices['Date'].iloc[i] )    # Converting date (string) into Datetime format

        date_index = selected_date - first_date   # Difference between start date and selected date
        date_index = date_index.days    # To convert format from Datetime into an integer
        
        company_index = get_companyindex( dict_companytickers, df_shareprices['Ticker'].iloc[i] )    # To get the company_index (in the matrix) of selected company ticker (string)


        # matrix[date_index][company_index]
        matrix[date_index][company_index] = df_shareprices['Close'].iloc[i]     # To asign the share price to a value in the matrix
        # The matrix has 4,460 date_index & 2,062 company_index --> 4,460 columns and 2,062 rows


    output = open('matrix.pkl', 'wb')
    pickle.dump(matrix, output)
    output.close()





matrix = pd.read_pickle('empty_matrix.pkl')     # Load matrix

df_shareprices = pd.read_pickle('daily_shareprices.pkl')   # Load df_shareprices from a .json file 

with open('dict_companytickers.json') as json_file:     # Load dict_companytickers into a dictionary from a .json file
    dict_companytickers = json.load(json_file)  # Need this to get the company_index to asign share prices to a specific value (of company_index & date_index)

first_date = date(2007, 1, 3)   # 3rd January 2007



create_matrix_shareprices(matrix, df_shareprices, dict_companytickers, first_date)

