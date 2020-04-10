
# These are function that will be used in convert_data_shareprices.py

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
