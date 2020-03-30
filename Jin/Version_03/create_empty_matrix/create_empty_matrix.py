
import pandas as pd
import numpy as np

'''
1. The goal is to create an empty matrix (aka 3D array) to store the share price data
2. Empty matrix referring to all the value in the matrix being set to Nan
3. Since the data is in a matrix, it will save time having to iterate through a dataframe everytime we run the program
4. The matrix will be 2-dimensions
5. Rows = no of companies, and Columns = no of dates in between bounds
6. I will be able to access data by writing matrix[i][j]

'''



from calculate_days_inbetween import *

import json

with open('dict_companytickers.json') as f:     # Importing .json file of dictionary of company tickers and indices
  dict_companytickers = json.load(f)

no_of_companytickers = len(dict_companytickers)     # To get the number of indices of company tickers (which will be needed to set the no of rows in the matrix)




days_inbetween = calculate_days_inbetween()     # Calling function from another file to get the no of days in-between the date bounds

array_days_inbetween = []     # Empty array to add the indices of no of days in-between the 2 date bounds (first date and last date)


for i in range(days_inbetween): 

    array_days_inbetween.append(i)    # This iteration is to give me an array of all the indices of companytickers





# np.empty( (rows, columns) )
empty_matrix = np.empty((no_of_companytickers, days_inbetween))    # Creating an empty matrix with random values

empty_matrix[:] = np.NaN  # Asigning Nan as values in the empty array 





matrix = pd.DataFrame(data = empty_matrix, columns = array_days_inbetween)  # The parameters has to be arrays


print(matrix)

