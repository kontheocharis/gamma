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


# IMPORTANT VARIABLES TO NOTE

   # analysing_statements.eps_2016
   # analysing_statements.total_outstanding_shares_2016

   # analysing_statements.cash_2016
   # analysing_statements.ppe_net_2016
   # analysing_statements.total_assets_2016
   # analysing_statements.total_debt_2016
   # analysing_statements.total_liabilities_2016
   # analysing_statements.total_equity_2016

   # analysing_statements.operating_cashflow_2016
   # analysing_statements.operating_cashflow_2015
   # analysing_statements.operating_cashflow_2014
   # analysing_statements.free_cashflow_2016


def analysing_statements(URL_income_statement, URL_balance_sheet, URL_cashflow_statement):
   
   # INCOME STATEMENT

   json_income_statement = requests.get(URL_income_statement).json()
   df_income_statement = pd.DataFrame(json_income_statement['financials'])

   #no_of_columns = len(df_income_statement.columns)
   #no_of_rows = len(df_income_statement)

   eps = df_income_statement["EPS Diluted"]
   analysing_statements.eps_2016 = float(eps.iloc[year_2016])
   # variables["eps_2016"] = float(eps.iloc[year_2016])

   total_outstanding_shares = df_income_statement["Weighted Average Shs Out (Dil)"]
   analysing_statements.total_outstanding_shares_2016 = float(total_outstanding_shares.iloc[year_2016])



   # BALANCE SHEET

   json_balance_sheet = requests.get(URL_balance_sheet).json()
   df_balance_sheet = pd.DataFrame(json_balance_sheet['financials'])


   cash = df_balance_sheet["Cash and cash equivalents"]
   analysing_statements.cash_2016 = float(cash.iloc[year_2016])

   ppe_net = df_balance_sheet["Property, Plant & Equipment Net"]
   analysing_statements.ppe_net_2016 = float(ppe_net.iloc[year_2016])

   total_assets = df_balance_sheet["Total assets"]
   analysing_statements.total_assets_2016 = float(total_assets.iloc[year_2016])

   total_debt = df_balance_sheet["Total debt"]
   analysing_statements.total_debt_2016 = float(total_debt.iloc[year_2016])

   total_liabilities = df_balance_sheet["Total liabilities"]
   analysing_statements.total_liabilities_2016 = float(total_liabilities.iloc[year_2016])

   total_equity = df_balance_sheet["Total shareholders equity"]
   analysing_statements.total_equity_2016 = float(total_equity.iloc[year_2016])



   # CASHFLOW STATEMENT

   json_cashflow_statement = requests.get(URL_cashflow_statement).json()
   df_cashflow_statement = pd.DataFrame(json_cashflow_statement['financials'])


   operating_cashflow = df_cashflow_statement["Operating Cash Flow"]
   analysing_statements.operating_cashflow_2016 = float(operating_cashflow.iloc[year_2016])
   analysing_statements.operating_cashflow_2015 = float(operating_cashflow.iloc[year_2015])
   analysing_statements.operating_cashflow_2014 = float(operating_cashflow.iloc[year_2014])

   free_cashflow = df_cashflow_statement["Free Cash Flow"]
   analysing_statements.free_cashflow_2016 = float(free_cashflow.iloc[year_2016])


