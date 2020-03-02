


import pandas as pd
import wget
#save_location = "C:/Users/jin/Desktop/"
#wget.download("https://stockrow.com/api/companies/AAPL/financials.xlsx?dimension=Q&section=Income%20Statement&sort=asc")

symbol = "AAPL"
section = "Income%20Statement"

url = "https://stockrow.com/api/companies/{}/financials.xlsx?dimension=A&section={}&sort=asc"




data_xls = pd.read_excel(url.format(symbol, section), index_col = [0]).transpose()
#data_xls.to_csv('csvfile.csv', encoding='utf-8', index=False)



print(data_xls)