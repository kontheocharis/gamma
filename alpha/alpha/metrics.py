from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List
from statistics import mean, StatisticsError
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

@dataclass(init=False)
class Metrics(ABC):
    """
    Holds all the metrics required for calculation of investability.
    """
    @abstractmethod
    def are_investable(self) -> bool:
        """
        Calculates investability from `self` attributes.
        """
        pass

    def print(self, func=print):
        func(f"{type(self).__name__}:")
        for k, v in self.__dict__.items():
            func(f"\t{k} = {v}")


# TODO: add documentation
class BacktrackingAnalyser:
    """
    Container for all the metrics, for purposes of statistical analysis.
    """
    _metric_data: Dict[str, Metrics] = {}
    _stock_data: Dict[str, pd.DataFrame] = {}

    _investing_date: date
    _return_percent: float

    _amount_exceeded_return_percent: int = 0
    _amount_successful: int = 0

    def __init__(self, investing_date: date, return_percent: float):
        self._investing_date = investing_date
        self._return_percent = return_percent


    def add_metrics_for(self, company: str, metrics: Metrics):
        self._metric_data[company] = metrics

    def add_stock_df_for(self, company: str, stock_df: pd.DataFrame):
        self._stock_data[company] = stock_df


    def average_accuracy(self) -> float:
        try:
            return mean(
            float(self._prediction_was_sucessful(
                self._stock_data[company],
                self._stock_data[company].loc[self._investing_date]["high"]
            )) for company, metrics in self._metric_data.items() if metrics.are_investable())
        except StatisticsError:
            return 0

    def investable_amount(self) -> int:
        return sum(int(metrics.are_investable()) for metrics in self._metric_data.values())

    def successful_amount(self) -> int:
        return self._amount_successful

    def exceeded_return_amount(self) -> int:
        return self._amount_exceeded_return_percent

    def investable_percent(self) -> float:
        """
        Averages amount of values in `self.metrics` which are investable.
        """
        try:
            return mean(float(metrics.are_investable()) for metrics in self._metric_data.values())
        except StatisticsError:
            return 0

    def _prediction_was_sucessful(self, stock_df: pd.DataFrame, investing_price: np.float64) -> bool:
        relevant_df = stock_df[stock_df.index.date > self._investing_date]
        max_price = relevant_df.max()["high"]
        if max_price >= self._return_percent * investing_price:
            self._amount_exceeded_return_percent += 1
            self._amount_successful += 1
            return True

        if relevant_df.iloc[-1]["high"] > investing_price:
            self._amount_successful += 1
            return True
        return False


# Actual metric definitions:

@dataclass(init=False)
class V1Metrics(Metrics):
    """
    First version of metrics.
    """
    cnav1: np.float64
    nav: np.float64
    pe_ratio: np.float64
    cash_flows: List[np.float64]
    debt_to_equity_ratio: np.float64
    potential_roi: np.float64
    market_cap: np.float64

    def are_investable(self) -> bool:
        return self.cnav1 < self.nav \
            and self.pe_ratio < 10 \
            and all(cash_flow > 0 for cash_flow in self.cash_flows) \
            and self.debt_to_equity_ratio < 1 \
            and self.potential_roi > 1 \
            and self.market_cap > 10**9
