import pandas as pd
import numpy as np
import json 
import requests

year_2019 = 0  # I know that this is an inefficient way to assign values to variables. I will change this later
year_2018 = 1  # This is just for my reference now while writing code
year_2017 = 2
year_2016 = 3
year_2015 = 4
year_2014 = 5


# INCOME STATEMENT

json_income_statement = requests.get("https://financialmodelingprep.com/api/v3/financials/income-statement/AAPL").json()
df_income_statement = pd.DataFrame(json_income_statement['financials'])

#no_of_columns = len(df_income_statement.columns)
#no_of_rows = len(df_income_statement)

eps = df_income_statement["EPS Diluted"]
eps_2016 = float(eps.iloc[year_2016])

total_outstanding_shares = df_income_statement["Weighted Average Shs Out (Dil)"]
total_outstanding_shares_2016 = float(total_outstanding_shares.iloc[year_2016])



# BALANCE SHEET

json_balance_sheet = requests.get("https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/AAPL").json()
df_balance_sheet = pd.DataFrame(json_balance_sheet['financials'])


cash = df_balance_sheet["Cash and cash equivalents"]
cash_2016 = float(cash.iloc[year_2016])

ppe_net = df_balance_sheet["Property, Plant & Equipment Net"]
ppe_net_2016 = float(ppe_net.iloc[year_2016])

total_assets = df_balance_sheet["Total assets"]
total_assets_2016 = float(total_assets.iloc[year_2016])

total_debt = df_balance_sheet["Total debt"]
total_debt_2016 = float(total_debt.iloc[year_2016])

total_liabilities = df_balance_sheet["Total liabilities"]
total_liabilities_2016 = float(total_liabilities.iloc[year_2016])

total_equity = df_balance_sheet["Total shareholders equity"]
total_equity_2016 = float(total_equity.iloc[year_2016])



# CASHFLOW STATEMENT

json_cashflow_statement = requests.get("https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/AAPL").json()
df_cashflow_statement = pd.DataFrame(json_cashflow_statement['financials'])


operating_cashflow = df_cashflow_statement["Operating Cash Flow"]
operating_cashflow_2016 = float(operating_cashflow.iloc[year_2016])
operating_cashflow_2015 = float(operating_cashflow.iloc[year_2015])
operating_cashflow_2014 = float(operating_cashflow.iloc[year_2014])

free_cashflow = df_cashflow_statement["Free Cash Flow"]
free_cashflow_2016 = float(free_cashflow.iloc[year_2016])

