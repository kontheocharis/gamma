
# DESCRIPTION --> Calculating metrics and deciding if a stock fits inveting criteria


class calculating_ratios(object):
    
    def __init__(self, eps, total_outstanding_shares, \
        cash, ppe_net, total_assets, total_debt, total_liabilities, total_equity, operating_cashflow_0, operating_cashflow_1year_before, operating_cashflow_2year_before, free_cashflow, \
        buy_share_price):
        
        # Income Statement
        self.eps = eps
        self.total_outstanding_shares = total_outstanding_shares

        # Balance Sheet
        self.cash = cash
        self.ppe_net = ppe_net
        self.total_assets = total_assets
        self.total_debt = total_debt
        self.total_liabilities = total_liabilities
        self.total_equity = total_equity

        # Cashflow Statement
        self.operating_cashflow_0 = operating_cashflow_0
        self.operating_cashflow_1year_before = operating_cashflow_1year_before
        self.operating_cashflow_2year_before = operating_cashflow_2year_before
        self.free_cashflow = free_cashflow

        # Share Price
        self.buy_share_price = buy_share_price


    def pe_ratio(self):

        self.pe_ratio = self.buy_share_price / self.eps
        return self.pe_ratio


    def years_of_positive_operating_cashflow(self):

        self.years_of_positive_operating_cashflow = 0

        if self.operating_cashflow_0 > 0:   # Checking if given year's cashflow is positive
            self.years_of_positive_operating_cashflow = self.years_of_positive_operating_cashflow + 1
        
        if self.operating_cashflow_1year_before > 0:    # Checking if previous year's cashflow is positive
            self.years_of_positive_operating_cashflow = self.years_of_positive_operating_cashflow + 1

        if self.operating_cashflow_2year_before:    # Checking if 2 years back cashflow is positive
            self.years_of_positive_operating_cashflow = self.years_of_positive_operating_cashflow + 1

        return self.years_of_positive_operating_cashflow


    def debt_to_equity_ratio(self):

        self.debt_to_equity_ratio = self.total_debt / self.total_equity
        return self.debt_to_equity_ratio

    def market_cap(self):

        self.market_cap = self.total_outstanding_shares * self.buy_share_price
        return self.market_cap


    def cnav1(self):

        self.total_good_assets = self.cash + (self.ppe_net / 2)   # This ain't actually the calculation for total good assets bc I should not take Net PP&E and exclude short-term investments 
        self.cnav1 = (self.total_good_assets - self.total_liabilities) / self.total_outstanding_shares
        return self.cnav1


    def nav(self):
        
        self.nav = (self.total_assets - self.total_liabilities) / self.total_outstanding_shares
        return self.nav

    def potential_roi(self):

        self.potential_roi = (self.nav /self.buy_share_price) - 1
        # potential_roi = 1  -->  for a 100% gain from buy_share_price
        return self.potential_roi






class investing_strategy_requirements(object):
    
    def __init__(self, pe_ratio, years_of_positive_operating_cashflow, debt_to_equity_ratio, market_cap, cnav1, nav, potential_roi, \
        pe_ratio_requirement, years_of_positive_operating_cashflow_requirement, debt_to_equity_ratio_requirement, market_cap_requirement, potential_roi_requirement):
        
        # Metrics calculated from calling previous class calculating_ratios(object)
        self.pe_ratio = pe_ratio
        self.years_of_positive_operating_cashflow = years_of_positive_operating_cashflow
        self.debt_to_equity_ratio = debt_to_equity_ratio
        self.market_cap = market_cap
        self.cnav1 = cnav1
        self.nav = nav
        self.potential_roi = potential_roi

        # Requirements calculated from metrics
        self.pe_ratio_requirement = pe_ratio_requirement
        self.years_of_positive_operating_cashflow_requirement = years_of_positive_operating_cashflow_requirement
        self.debt_to_equity_ratio_requirement = debt_to_equity_ratio_requirement
        self.market_cap_requirement = market_cap_requirement
        self.potential_roi_requirement = potential_roi_requirement



    def fulfil_requirements(self):

        self.fulfil_requirements = 0

        if (self.pe_ratio >= self.pe_ratio_requirement) and (self.years_of_positive_operating_cashflow >= self.years_of_positive_operating_cashflow_requirement) and (self.debt_to_equity_ratio >= self.debt_to_equity_ratio_requirement) and (self.market_cap >= self.market_cap_requirement) and (self.potential_roi >= self.potential_roi_requirement):
            
            self.fulfil_requirements = 1

        return self.fulfil_requirements

