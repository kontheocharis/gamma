
from datetime import date

# Purpose: to get company index of each stock ticker to add into a dictionary
def get_companyindex(dict_companytickers, stock_ticker):    # Note that stock ticker has to be in the format of a string

    # Create a key_list and val_list, to get key from value
    key_list = list(dict_companytickers.keys())     
    val_list = list(dict_companytickers.values())

    # To get company_index from stock ticker (string)
    company_index = val_list[key_list.index(stock_ticker)]  
    
    return company_index



def convert_string_to_date(date_string):

    # Convert date (string) into an array
    date_string = date_string.split('-')
    
    # Convert each number in string format (within the array) into an integer to input into Datetime format 
    date_string = date( int(date_string[0]), int(date_string[1]), int(date_string[2]) )     # There are 3 parts since date(year, month, day)

    return date_string

