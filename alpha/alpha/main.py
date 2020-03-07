import argparse
import os
import logging
import math
from enum import Enum
from dataclasses import dataclass
from pprint import pprint
from datetime import date, timedelta
from typing import Callable, Optional, Tuple

import numpy as np
import pandas as pd

from alpha.data_fetching import FmpDataFetcher
from alpha.metrics import V1Metrics, BacktrackingAnalyser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_v1_metrics_for(company: str,
                       investing_date: date,
                       cash_flow_period: int = 3,
                       data_dir: Optional[str] = None) -> Optional[Tuple[V1Metrics, pd.DataFrame]]:
    """
    Determines whether to invest in `company` in year `investing_year`.

    :param company: the symbol of the company in question.
    :param investing_year: the year of investing.
    :param cash_flow_period: for how many years in the past, including
        `investing_year`, does cash flow need to be positive?
    """

    # Use the financialmodelingprep.com fetcher for this
    fetcher = FmpDataFetcher(company,
                             (investing_date.year - cash_flow_period + 1, investing_date.year),
                             data_dir)

    stock_data = fetcher.stock_data()
    all_stock_data = fetcher.stock_data(restrict_dates=False)

    if stock_data.empty:
        logger.warning(f"No stock data for {company}, skipping.")
        return None

    try:
        _ = all_stock_data.loc[investing_date]
    except KeyError:
        logger.warning(f"No stock data for investing_date for {company}, skipping.")
        return None

    financial_data = fetcher.financial_data()

    # Get a reference to the current year
    curr_year_row = financial_data[financial_data.index.year == investing_date.year]
    try:
        curr_year = curr_year_row.iloc[0]
    except IndexError:
        logger.warning(f"Error for {company}, skipping.")
        return None

    metrics = V1Metrics()

    if any(math.isnan(x) for x in (
            curr_year['cash_short_term_investments'],
            curr_year['ppe'],
            curr_year['total_liabilities'],
            curr_year['total_assets'],
            curr_year['total_debt'],
            curr_year['total_shareholders_equity'],
            curr_year['total_outstanding_shares'],
            curr_year['eps'],
    )):
        logger.warning(f"Some metrics are NaN for {company}, skipping.")
        return None
        

    # This is not correct
    total_good_assets = curr_year['cash_short_term_investments'] + (curr_year['ppe'] / 2)

    # CNAV1
    if curr_year['total_outstanding_shares'] == 0:
        logger.warning(f"Zero total outstanding shares for {company}, skipping.")
        return None
    metrics.cnav1 = (total_good_assets - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # NAV
    metrics.nav = (curr_year['total_assets'] - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # Get the share price a day before the report was released
    date_of_report = curr_year_row.index[0]

    for i in range(1, 30): # buffer
        try:
            share_price_at_date = stock_data.loc[date_of_report - timedelta(days=i)]['high']
            break
        except KeyError:
            continue
    else:
        logger.warning(f"Insufficient stock data for {company}, skipping.")
        return None

    # P/E ratio
    if curr_year['eps'] == 0:
        logger.warning(f"Zero EPS for {company}, skipping.")
        return None
    metrics.pe_ratio = share_price_at_date / curr_year['eps']

    # Debt-to-equity ratio
    if curr_year['total_shareholders_equity'] == 0.0:
        logger.warning(f"Zero total shareholders equity for {company}, skipping.")
        return None
    metrics.debt_to_equity_ratio = curr_year['total_debt'] / curr_year['total_shareholders_equity']

    # Potential ROI
    metrics.potential_roi = (metrics.nav / share_price_at_date) - 1

    # Market cap.
    metrics.market_cap = curr_year['total_outstanding_shares'] * share_price_at_date

    # Ensure that cash flow has been positive for the past `cash_flow_period` years
    metrics.cash_flows = [cash_flow for cash_flow in financial_data['operating_cashflow']]

    return metrics, all_stock_data


def main():
    # Use command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('date', type=lambda s: date.fromisoformat(s))
    parser.add_argument('return_percent', type=float)
    args = parser.parse_args()

    # data_dir spec:
    #   companies -> \n separated list of company names to use
    #   balance-sheet-statement/
    #       X.json for X in companies
    #   cash-flow-statement/
    #       X.json for X in companies
    #   income-statement/
    #       X.json for X in companies

    companies: List[str]
    with open(os.path.join(args.data_dir, 'companies'), 'r') as f:
        companies = f.read().splitlines()

    analyser = BacktrackingAnalyser(investing_date=args.date, return_percent=args.return_percent)

    logger.info("Running.")
    for company in companies:
        result = get_v1_metrics_for(company, investing_date=args.date, data_dir=args.data_dir)
        if result:
            logger.info(f"{company} has workable data.")
            metrics, stock_df = result
            analyser.add_metrics_for(company, metrics)
            analyser.add_stock_df_for(company, stock_df)

            if metrics.are_investable():
                logger.info(f"{company} is investable!")

    print(f"Percentage of companies deemed investable: {analyser.investable_percent():.3f}")
    print(f"Final average_accuracy: {analyser.average_accuracy():.3f}")

    # print(companies)

