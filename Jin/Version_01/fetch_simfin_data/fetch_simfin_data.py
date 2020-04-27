
import pandas as pd
import os.path 

# Import the main functionality from the SimFin Python API.
import simfin as sf

# Import names used for easy access to SimFin's data-columns.
from simfin.names import *


class fetch_simfin_data(object):
    
    def __init__(self):
        ''' To fetch data from Simfin and download dataframe, as excel and .pkl files locally '''

    
    def load_income(self):  
        
        if os.path.exists('income.pkl'):
            print('Income statement files already exists locally.')


        else:
            sf.set_data_dir('~/simfin_data/')
            sf.set_api_key(api_key='free')
            sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

            df1 = sf.load(dataset='income', variant='annual', market='us')  # Loading the data from the API and creating a dataframe
            df1.head()

            df1.to_excel('income.xlsx')     # Downloading the dataframe to an excel file locally
            df1.to_pickle('income.pkl')     # Downloading the dataframe to a .pkl file locally, which is supposed to load faster than an excel file
    


    def load_balance(self):
        
        if os.path.exists('balance.pkl'):
            print('Balance sheet data already exists locally.')


        else:
            sf.set_data_dir('~/simfin_data/')
            sf.set_api_key(api_key='free')
            sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

            df2 = sf.load(dataset='balance', variant='annual', market='us')
            df2.head()

            df2.to_excel('balance.xlsx')  
            df2.to_pickle('balance.pkl')  



    def load_cashflow(self):

        if os.path.exists('cashflow.pkl'):
            print('Cashflow statement data already exists locally.')


        else:
            sf.set_data_dir('~/simfin_data/')
            sf.set_api_key(api_key='free')

            sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')
            df3 = sf.load(dataset='cashflow', variant='annual', market='us')
            df3.head()

            df3.to_excel('cashflow.xlsx')  
            df3.to_pickle('cashflow.pkl')  



    def load_shareprices(self):

        if os.path.exists('daily_shareprices.pkl'):
            print('Shareprices data already exists locally.')


        else:
            sf.set_data_dir('~/simfin_data/')
            sf.set_api_key(api_key='free')
            sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

            df4 = sf.load(dataset='shareprices', variant='daily', market='us')
            df4.head()

            df4.to_excel('daily_shareprices.xlsx')
            df4.to_pickle('daily_shareprices.pkl')  



    def load_companytickers(self):

        if os.path.exists('companytickers.pkl'):
            print('Company tickers data already exists locally.')


        else:
            sf.set_data_dir('~/simfin_data/')
            sf.set_api_key(api_key='free')
            sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

            df5 = sf.load(dataset='companies', variant=None, market='us', index='Ticker', refresh_days=30)
            df5.head()

            df5.to_excel('companytickers.xlsx')  
            df5.to_pickle('companytickers.pkl')  
        
