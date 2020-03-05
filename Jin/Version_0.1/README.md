
## What is Version 0.1?

Version 0.1 is a simple program to backtesting a value investing strategy on US equities INDIVIDUALLY, with the use of Financialmodelingprep.com's API. 

In Version 0.2, the program will be able to backtest a value investing strategy on all US equities, provided that you have the database of US equities' 3 financial statements, daily stock prices over a period of several years and US stock tickers. 


## Investing Philosophy Behind Program

This is Version 0.1 of the investing algorithm.

My investing philosophy is: the more fundamentally sound a company is, the more likely that market correction will occur and that the market will ultimatelyl adjust to its intrinsic value.


## Dates Used in Program

Currently, the buy and sell dates are set to 2016-04-01 and 2019-04-01 respectively. The dates to analyse financial statements are set to 2016. This means that the operating cashflow used will be from 2014 to 2016.

The dates to read data from the 3 financial statements to calculate ratios can be changed / set between Lines 6 and 11 of investing_01.py.

The dates to compare share prices can be changed / set in Line 20 of investing_03.py.


## Company Used in Program

To change the US stock, enter the new stock ticker in Line 17 of investing_03.py. 

To change the values of fundamental ratios / metrics, enter the new values in Line 49 of investing_03.py. Refer to Lines 25 and 26 to view the arguments of the function.


## Company Used in Program

```
python investing_03.py
```
