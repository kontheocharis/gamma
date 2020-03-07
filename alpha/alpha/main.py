from dataclasses import dataclass
import numpy as np
import argparse
from pprint import pprint
from datetime import date, timedelta

from alpha.fmp import FmpDataFetcher
from alpha.metrics import V1Metrics, BacktrackingAnalyser


def get_v1_metrics_for(company: str, investing_date: date, cash_flow_period: int = 3) -> bool:
    """
    Determines whether to invest in `company` in year `investing_year`.

    :param company: the symbol of the company in question.
    :param investing_year: the year of investing.
    :param cash_flow_period: for how many years in the past, including
        `investing_year`, does cash flow need to be positive?
    """

    # Use the financialmodelingprep.com fetcher for this
    fetcher = FmpDataFetcher(company, (investing_date.year - cash_flow_period + 1, investing_date.year))

    stock_data = fetcher.stock_data()
    financial_data = fetcher.financial_data()

    # Get a reference to the current year
    curr_year_row = financial_data[financial_data.index.year == investing_date.year]
    curr_year = curr_year_row.iloc[0]

    metrics = V1Metrics()

    # This is not correct
    total_good_assets = curr_year['cash_short_term_investments'] + (curr_year['ppe'] / 2)

    # CNAV1
    metrics.cnav1 = (total_good_assets - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # NAV
    metrics.nav = (curr_year['total_assets'] - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # Get the share price a day before the report was released
    date_of_report = curr_year_row.index[0]
    share_price_at_date = stock_data.loc[date_of_report - timedelta(days=1)]['high']

    # P/E ratio
    metrics.pe_ratio = share_price_at_date / curr_year['eps']

    # Debt-to-equity ratio
    metrics.debt_to_equity_ratio = curr_year['total_debt'] / curr_year['total_shareholders_equity']

    # Potential ROI
    metrics.potential_roi = (metrics.nav / share_price_at_date) - 1

    # Market cap.
    metrics.market_cap = curr_year['total_outstanding_shares'] * share_price_at_date

    # Ensure that cash flow has been positive for the past `cash_flow_period` years
    metrics.cash_flows = [cash_flow for cash_flow in financial_data['operating_cashflow']]

    return metrics


def main():
    # Use command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('company')
    parser.add_argument('date', type=lambda s: date.fromisoformat(s))
    args = parser.parse_args()


    metrics = get_v1_metrics_for(company=args.company, investing_date=args.date)

    print(metrics)
