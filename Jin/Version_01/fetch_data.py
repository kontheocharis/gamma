
from datetime import date

# File to download data from the data source
from fetch_simfin_data.fetch_simfin_data import load_income, load_balance, load_cashflow, load_shareprices, load_companytickers

# File to download dictionary containing company index & df statement index
from convert_data_format.download_dict_df_statement_index import download_dict_df_statement_index

# File to download dictionary containing company names & company index of matrix
from convert_data_format.download_dict_company_index_matrix import download_dict_company_index_matrix

# File to download shareprice matrix and dictionary containing company index & company name (key, value) locally
from convert_data_format.download_matrix import DownloadMatrix


# Download data from data source (if not already downloaded locally)
load_income()
load_balance()
load_cashflow()
load_shareprices()
load_companytickers()


# Download dictionary containing company index & df statement index
# Set the year parameter to any year between 2007 and 2018
download_dict_df_statement_index('income.pkl', 2007, 2018)

# Download dictionary with company index & company name (key, value) locally
download_dict_company_index_matrix('daily_shareprices.pkl')


# Download the matrix.pkl file locally
B = DownloadMatrix('daily_shareprices.pkl', 'dict_company_index_matrix.json', date(
    2007, 1, 3), date(2019, 3, 21))

B.create_empty_matrix()
B.create_matrix_shareprices()
