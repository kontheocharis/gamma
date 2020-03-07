
## About download_list_of_stocks

download_list_of_stocks parses through all 13,584 stocks tickers from financialmodelingprep's API to output an excel file with 5,038 files that contain data. 

The other files are either empty or contain empty objects (eg { }) 

download_list_of_stocks contains two programs - parse_path.py & parse_dict.py - to run through all 13,584 stocks tickers from financialmodelingprep's API

https://financialmodelingprep.com/developer/docs/#Symbols-List


## Set Up Requirement to run the Programs

The code in these 2 files were written with the assumption that the paths to the data (of three financial statements and daily share price) would be:


```
path_income_statement = f"/Users/jin/Desktop/download/f_statements/income-statement/{ticker}.json"
path_balance_sheet = f"/Users/jin/Desktop/download/f_statements/balance-sheet-statement/{ticker}.json"
path_cashflow_statement = f"/Users/jin/Desktop/download/f_statements/cash-flow-statement/{ticker}.json"
path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/{ticker}.json"
```


## Ignore This File if stock_ticker_list_after_parse_path.csv is Already Present in Main Folder

If the file stock_ticker_list_after_parse_path.csv - containing 5,038 files - is already present in Jin/Version_0.2/main, ignore this file, unless you would like to make changes to the criteria of the program parsing all the stock tickers. 

