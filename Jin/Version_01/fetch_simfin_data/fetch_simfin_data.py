
import os.path

# Import the main functionality from the SimFin Python API
import simfin as sf

# Import names used for easy access to SimFin's data-columns
from simfin.names import *


def load_income():
    '''To download Simfin income statement data into excel and .pkl files locally.'''

    if os.path.exists('income.pkl'):
        print('Income statement files already exists locally.')

    else:
        sf.set_data_dir('~/simfin_data/')
        sf.set_api_key(api_key='free')
        sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

        # Load data from Simfin API and create a dataframe
        df1 = sf.load(dataset='income', variant='annual', market='us')
        df1.head()

        # Download dataframe to an excel and .pkl file locally
        df1.to_excel('income.xlsx')
        df1.to_pickle('income.pkl')


def load_balance():
    '''To download Simfin balance sheet data into excel and .pkl files locally.'''

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


def load_cashflow():
    '''To download Simfin cashflow statement data into excel and .pkl files locally.'''

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


def load_shareprices():
    '''To download Simfin shareprices data into excel and .pkl files locally.'''

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


def load_companytickers():
    '''To download Simfin company tickers data into excel and .pkl files locally.'''

    if os.path.exists('companytickers.pkl'):
        print('Company tickers data already exists locally.')

    else:
        sf.set_data_dir('~/simfin_data/')
        sf.set_api_key(api_key='free')
        sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

        df5 = sf.load(dataset='companies', variant=None,
                      market='us', index='Ticker', refresh_days=30)
        df5.head()

        df5.to_excel('companytickers.xlsx')
        df5.to_pickle('companytickers.pkl')
