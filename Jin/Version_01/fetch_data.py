
from datetime import date
import pandas as pd 

# File to download data from the data source
from fetch_simfin_data.fetch_simfin_data import * 

# File to download dictionary containing company index & df statement index
from convert_data_format.download_dict_df_statement_index import *

# File to download dictionary containing company names & company index of matrix
from convert_data_format.download_dict_company_index_matrix import *    

# File to download shareprice matrix and dictionary containing company index & company name (key, value) locally
from convert_data_format.download_matrix import *



# Download data from data source (if not already downloaded locally)
a = fetch_simfin_data()

a.load_income()
a.load_balance() 
a.load_cashflow()
a.load_shareprices()
a.load_companytickers()


# Download dictionary containing company index & df statement index
download_dict_df_statement_index('income.pkl', 2007, 2018)     # Set the year parameter to any year between 2007 and 2018

# Download dictionary with company index & company name (key, value) locally
download_dict_company_index_matrix('daily_shareprices.pkl')


# Download the matrix.pkl file locally
b = download_matrix( 'daily_shareprices.pkl', 'income.pkl', 'dict_company_index_matrix.json', date(2007, 1, 3), date(2019, 3, 21) )

b.create_empty_matrix()
b.create_matrix_shareprices()

