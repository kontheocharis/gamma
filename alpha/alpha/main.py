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

from alpha.data_fetching import FmpDataFetcher, FmpNonExistentBoundsError
from alpha.metrics import V1Metrics, BacktrackingAnalyser

LOGGING_FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


def get_v1_metrics_for(company: str,
                       investing_date: date,
                       cash_flow_period: int,
                       lookahead_period: int,
                       data_dir: str) -> Optional[Tuple[V1Metrics, pd.DataFrame]]:
    """
    Determines whether to invest in `company` in year `investing_year`.

    :param company: the symbol of the company in question.
    :param investing_year: the year of investing.
    :param cash_flow_period: for how many years in the past, including
        `investing_year`, does cash flow need to be positive?
    """

    # Use the financialmodelingprep.com fetcher for this
    fetcher = FmpDataFetcher(
        company,
        (investing_date - timedelta(weeks=52 * cash_flow_period),
         investing_date + timedelta(weeks=52 * lookahead_period)),
        data_dir)

    fetcher.load_pickle()

    try:
        all_stock_data = fetcher.stock_data(restrict_dates=False)
        stock_data = fetcher.restrict_dates(all_stock_data)
        financial_data = fetcher.financial_data()
    except FmpNonExistentBoundsError as e:
        logger.warning(f"No sufficient data for {company}, skipping.")
        return None

    if all_stock_data[all_stock_data.index.date == investing_date].empty:
        logger.warning(f"No stock data for investing_date for {company}, skipping.")
        return None


    # Get a reference to the current year
    curr_year_row = financial_data[financial_data.index.date < investing_date]
    if curr_year_row.empty or curr_year_row.index.year[-1] < (investing_date.year - 1):
        logger.warning(f"No suitable financial statement for {company}, skipping.")
        return None
    curr_year = curr_year_row.iloc[-1]

    metrics = V1Metrics()

    # Check for NaNs
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
    date_of_report = curr_year.name

    for i in range(0, 30): # 30-day buffer
        try:
            share_date = date_of_report - timedelta(days=i)
            share_price_at_date = stock_data.loc[share_date]['high']
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
    cash_flows = financial_data[financial_data.index.date < investing_date]['operating_cashflow']
    if len(cash_flows) < cash_flow_period or any(math.isnan(x) for x in cash_flows[:cash_flow_period]):
        logger.warning(f"Insufficient cash flow history for {company}, skipping.")
        return None
    metrics.cash_flows = [cash_flow for cash_flow in cash_flows[:cash_flow_period]]

    fetcher.save_pickle()
    # logger.info(f"Dates: invest={investing_date}, lookahead_until={investing_date + timedelta(weeks=52 * lookahead_period)}, financial_statement_date={date_of_report.date()}, share_date={share_date}")
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

    analyser = BacktrackingAnalyser(
        investing_date=args.date,
        return_percent=args.return_percent)

    logger.info("Running.")
    for company in companies:
        result = get_v1_metrics_for(
            company,
            investing_date=args.date,
            data_dir=args.data_dir,
            lookahead_period=3,
            cash_flow_period=3)
        if not result:
            continue

        logger.info(f"{company} has workable data.")
        metrics, stock_df = result
        analyser.add_metrics_for(company, metrics)
        analyser.add_stock_df_for(company, stock_df)

        if metrics.are_investable():
            logger.info(f"{company} is investable!")

    analyser.run_analysis()

    print("-- RESULTS --")
    print(f"{analyser.no_of_companies} of {len(companies)} companies had sufficient data.")
    print(f"Of those, {analyser.investable_amount} were deemed investable ({(analyser.investable_percent * 100):.1f}%).")
    print(f"Of those, {analyser.amount_successful} were actually good investments ({(analyser.average_accuracy * 100):.1f}%). [Backtracing]")
    print(f"Of those, {analyser.amount_exceeded_return_percent} exceeded return_percent sometime during the waiting period.")
    print(f"TOTAL RETURNS (in source currency): {analyser.total_returns:.2f}")
