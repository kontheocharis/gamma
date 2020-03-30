
# To calculate the number of days in between the first and last dates that I took from 'GOOG' in df_shareprices

from datetime import date
import pandas as pd


def calculate_days_inbetween():

    first_date = date(2007, 1, 3)   # 3rd January 2007
    last_date = date(2019, 3, 21)

    days_inbetween = last_date - first_date
    days_inbetween = days_inbetween.days    # To convert type from datedelta to integer

    return days_inbetween

