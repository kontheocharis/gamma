
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

import pickle


from calculate_days_inbetween import *

import json

with open('dict_companytickers.json') as f:     # Importing .json file of dictionary of company tickers and indices
  dict_companytickers = json.load(f)


days_inbetween = calculate_days_inbetween()     # Calling function from another file to get the no of days in-between the date bounds


no_of_tickers = len(dict_companytickers)  # Getting the number of company tickers to create matrix
days_inbetween = calculate_days_inbetween()     # Getting the number of days in-between date bounds to create matrix


# (columns, rows)
matrix = np.full( (days_inbetween, no_of_tickers), np.NaN, dtype = np.float32)  # Creating the matrix as a numpy multi-dimensional array


# print(matrix)


# Download to .pkl file locally
output = open('empty_matrix.pkl', 'wb')
pickle.dump(matrix, output)
output.close()