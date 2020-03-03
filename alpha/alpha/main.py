from dataclasses import dataclass
import numpy as np
import argparse

from alpha.fmp import FmpDataFetcher


@dataclass
class Metrics:
    """
    Holds all the metrics required for calculation of investability.
    """
    cnav1: np.float64 = 0
    nav: np.float64 = 0
    pe_ratio: np.float64 = 0
    cash_flow_all_positive: np.float64 = 0
    debt_to_equity_ratio: np.float64 = 0
    potential_roi: np.float64 = 0
    market_cap: np.float64 = 0


def should_invest(company: str, investing_year: int, cash_flow_period: int = 3) -> bool:
    """
    Determines whether to invest in `company` in year `investing_year`.

    :param company: the symbol of the company in question.
    :param investing_year: the year of investing.
    :param cash_flow_period: for how many years in the past, including
        `investing_year`, does cash flow need to be positive?
    """

    # Use the financialmodelingprep.com fetcher for this
    fetcher = FmpDataFetcher(company, (investing_year - cash_flow_period + 1, investing_year))

    stock_data = fetcher.stock_data()
    financial_data = fetcher.financial_data()

    # Get a reference to the current year
    curr_year_row = financial_data[financial_data.index.year == investing_year]
    curr_year = curr_year_row.iloc[0]

    # Object in which to store all the metrics
    metrics = Metrics()

    # This is not correct
    total_good_assets = curr_year['cash_short_term_investments'] + (curr_year['ppe'] / 2)

    # CNAV1
    metrics.cnav1 = (total_good_assets - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # NAV
    metrics.nav = (curr_year['total_assets'] - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    # Get the share price a day before the report was released
    date_of_report = curr_year_row.index.values[0]
    share_price_at_date = stock_data.loc[date_of_report - np.timedelta64(1,'D')]['high']

    # P/E ratio
    metrics.pe_ratio = share_price_at_date / curr_year['eps']

    # Debt-to-equity ratio
    metrics.debt_to_equity_ratio = curr_year['total_debt'] / curr_year['total_shareholders_equity']

    # Potential ROI
    metrics.potential_roi = (metrics.nav / share_price_at_date) - 1

    # Market cap.
    metrics.market_cap = curr_year['total_outstanding_shares'] * share_price_at_date

    # Ensure that cash flow has been positive for the past `cash_flow_period` years
    metrics.cash_flow_all_positive = all(cash_flow > 0 for cash_flow in financial_data['operating_cashflow'])

    print(metrics)

    # Main logic for deciding whether to invest
    return metrics.cnav1 < metrics.nav \
            and metrics.pe_ratio < 10 \
            and metrics.cash_flow_all_positive \
            and metrics.debt_to_equity_ratio < 1 \
            and metrics.potential_roi > 1 \
            and metrics.market_cap > 10**9


def main():
    # Use command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('company')
    parser.add_argument('year', type=int)
    args = parser.parse_args()

    decision = should_invest(company=args.company, investing_year=args.year)

    if decision:
        print("Invest!")
    else:
        print("Don't invest.")
