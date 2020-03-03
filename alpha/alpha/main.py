from dataclasses import dataclass
import numpy as np
import argparse

from alpha.fmp import FmpDataFetcher


@dataclass
class Metrics:
    cnav1: np.float64 = 0
    nav: np.float64 = 0
    pe_ratio: np.float64 = 0
    cash_flow_all_positive: np.float64 = 0
    debt_to_equity_ratio: np.float64 = 0
    potential_roi: np.float64 = 0
    market_cap: np.float64 = 0


def should_invest(company: str, investing_year: int, cash_flow_period: int = 3) -> bool:
    fetcher = FmpDataFetcher(company, (investing_year - cash_flow_period + 1, investing_year))

    investing_year_sel = slice(str(investing_year), str(investing_year + 1))

    stock_data = fetcher.stock_data()
    financial_data = fetcher.financial_data()

    curr_year_row = financial_data[financial_data.index.year == investing_year]
    curr_year = curr_year_row.iloc[0]

    metrics = Metrics()

    total_good_assets = curr_year['cash_short_term_investments'] + (curr_year['ppe'] / 2)

    metrics.cnav1 = (total_good_assets - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    metrics.nav = (curr_year['total_assets'] - curr_year['total_liabilities']) \
        / curr_year['total_outstanding_shares']

    date_of_report = curr_year_row.index.values[0]
    share_price_at_date = stock_data.loc[date_of_report]['high']

    metrics.pe_ratio = share_price_at_date / curr_year['eps']

    metrics.debt_to_equity_ratio = curr_year['total_debt'] / curr_year['total_shareholders_equity']

    metrics.potential_roi = (metrics.nav / share_price_at_date) - 1

    metrics.market_cap = curr_year['total_outstanding_shares'] * share_price_at_date

    metrics.cash_flow_all_positive = all(cash_flow > 0 for cash_flow in financial_data['operating_cashflow'])

    print(metrics)

    if metrics.cnav1 < metrics.nav \
            and metrics.pe_ratio < 10 \
            and metrics.cash_flow_all_positive \
            and metrics.debt_to_equity_ratio < 1 \
            and metrics.potential_roi > 1 \
            and metrics.market_cap > 10**9:
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('company')
    parser.add_argument('year', type=int)

    args = parser.parse_args()

    decision = should_invest(company=args.company, investing_year=args.year)

    if decision:
        print("Invest!")
    else:
        print("Don't invest!")
