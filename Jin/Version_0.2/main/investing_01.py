
# DESCRIPTION --> Getting metrics from the 3 financial statements

def finding_value_from_year(df, year, metric):  # Purpose of this function is to go through the dataframe (of the financial statements) and get the value of a metric of a specific year

   date = ""   # Need to write this as I had to come up with an idea to check if there was actually a value (taken from the date) in the dataframe


   for i in range(len(df)):

      if year in df['date'].iloc[i]:    # Searching for a date with a specific year since I don't have the exact specific date

         date = df['date'].iloc[i]  #index = i


         # Running this if statement as many files, such as that of MFGP.json, are fucked up
         # EG. FCF = "" --> Not even FCF = "0"

         if df[metric].iloc[i] == "":  # Assuming that "" means 0 and not that the API program did not manage to collect data
            return 0
            
         else: 
            return df[metric].iloc[i]
   

   if date == "":  # This is referring back to the empty string variable, date, created at the start of the function 
      return 0    # Used to return 0, in the event that no data for a specific date is present (eg in the even that the company had not gone public back then)




def year_of_operating_cashflow_1year_before(year):    # Purpose of this function is to return (starting_year - 1) to get operating cashflow from 1 year before

    new_year = int(year) - 1
    new_year = str(new_year)
    return new_year

def year_of_operating_cashflow_2year_before(year):    # Purpose of this function is to return (starting_year - 2) to get operating cashflow from 2 years before

    new_year = int(year) - 2
    new_year = str(new_year)
    return new_year




class analysing_json_files(object):
   

   def __init__(self, data_income_statement, data_balance_sheet, data_cashflow_statement, year, stock_ticker):
      self.data_income_statement = data_income_statement
      self.data_balance_sheet = data_balance_sheet
      self.data_cashflow_statement = data_cashflow_statement
      self.year = year
      self.stock_ticker = stock_ticker
  


   # INCOME STATEMENT

   def eps_income_statement(self):
      self.eps = finding_value_from_year(self.data_income_statement, self.year, 'EPS Diluted')
      self.eps = float(self.eps)    # Convert EPS into a string
      return self.eps


   def total_outstanding_shares_income_statement(self):
      self.total_outstanding_shares = finding_value_from_year(self.data_income_statement, self.year, 'Weighted Average Shs Out (Dil)')
      self.total_outstanding_shares = float(self.total_outstanding_shares)    # Convert EPS into a string
      return self.total_outstanding_shares



   # BALANCE SHEET

   def cash_balance_sheet(self):
      self.cash = finding_value_from_year(self.data_balance_sheet, self.year, 'Cash and cash equivalents')
      self.cash = float(self.cash)
      return self.cash

   def ppe_net_balance_sheet(self):
      self.ppe_net = finding_value_from_year(self.data_balance_sheet, self.year, 'Property, Plant & Equipment Net')
      self.ppe_net = float(self.ppe_net)
      return self.ppe_net

   def total_assets_balance_sheet(self):
      self.total_assets = finding_value_from_year(self.data_balance_sheet, self.year, 'Total assets')
      self.total_assets = float(self.total_assets)
      return self.total_assets

   def total_debt_balance_sheet(self):
      self.total_debt = finding_value_from_year(self.data_balance_sheet, self.year, 'Total debt')
      self.total_debt = float(self.total_debt)
      return self.total_debt

   def total_liabilities_balance_sheet(self):
      self.total_liabilities = finding_value_from_year(self.data_balance_sheet, self.year, 'Total liabilities')
      self.total_liabilities = float(self.total_liabilities)
      return self.total_liabilities

   def total_equity_balance_sheet(self):
      self.total_equity = finding_value_from_year(self.data_balance_sheet, self.year, 'Total shareholders equity')
      self.total_equity = float(self.total_equity)
      return self.total_equity



   # CASHFLOW STATEMENT

   def operating_cashflow_0_cashflow_statement(self):
      self.operating_cashflow_0 = finding_value_from_year(self.data_cashflow_statement, self.year, 'Operating Cash Flow')
      self.operating_cashflow_0 = float(self.operating_cashflow_0)
      return self.operating_cashflow_0

   def operating_cashflow_1year_before_cashflow_statement(self):
      self.operating_cashflow_1year_before = finding_value_from_year(self.data_cashflow_statement, year_of_operating_cashflow_1year_before(self.year), 'Operating Cash Flow')
      # Have to put a function into the parameter as I need to get operating cashflow data from 1 year back
      self.operating_cashflow_1year_before = float(self.operating_cashflow_1year_before)
      return self.operating_cashflow_1year_before

   def operating_cashflow_2year_before_cashflow_statement(self):
      self.operating_cashflow_2year_before = finding_value_from_year(self.data_cashflow_statement, year_of_operating_cashflow_2year_before(self.year), 'Operating Cash Flow')
      # Have to put a function into the parameter as I need to get operating cashflow data from 2 years back
      self.operating_cashflow_2year_before = float(self.operating_cashflow_2year_before)
      return self.operating_cashflow_2year_before


   def free_cashflow_cashflow_statement(self):
      self.free_cashflow = finding_value_from_year(self.data_cashflow_statement, self.year, 'Free Cash Flow')
      self.free_cashflow = float(self.free_cashflow)
      return self.free_cashflow
      
      
      #print("Getting data from the financial statements of " + self.stock_ticker + " was successful!")

   
   





'''

# Only use this to test the analysing_json_files class

path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/AAPL.json"

df_income_statement = open(path_income_statement, 'r')     # Open the file
        
df_income_statement = df_income_statement.read()  # This converts the file into a string (aka an object)
df_income_statement = json.loads(df_income_statement)     # This converts the object into a dictionary
        
df_income_statement = pd.DataFrame.from_dict(df_income_statement['financials'])   # Lastly, this converts the file into a dataframe


path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/AAPL.json"

df_balance_sheet = open(path_balance_sheet, 'r')  
df_balance_sheet = df_balance_sheet.read()
df_balance_sheet = json.loads(df_balance_sheet)

df_balance_sheet = pd.DataFrame.from_dict(df_balance_sheet['financials'])



path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/AAPL.json"

df_cashflow_statement = open(path_cashflow_statement, 'r')
df_cashflow_statement = df_cashflow_statement.read()
df_cashflow_statement = json.loads(df_cashflow_statement)

df_cashflow_statement = pd.DataFrame.from_dict(df_cashflow_statement['financials'])



class_analysing_json_files = analysing_json_files(df_income_statement, df_balance_sheet, df_cashflow_statement, "2018", "AAPL")
fcf = class_analysing_json_files.free_cashflow_cashflow_statement()
print(fcf)

'''