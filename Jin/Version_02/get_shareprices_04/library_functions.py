
def get_company_index(stock_ticker, dict_companytickers):


    counter = 0

    for key in dict_companytickers:     # Iterate through every key in the (share price) dictionary 

        if key == stock_ticker:     # If the key matches with the selected stock ticker
            
            counter =  1

            return dict_companytickers[key]     # Return the company_index so that it can be used in the matrix and the share price can be found
            # EG of use --> matrix[date_index][company_index]

    
    if counter != 1:

        return 0

