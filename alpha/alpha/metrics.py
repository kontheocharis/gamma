from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List
from statistics import mean
from dataclasses import dataclass

import numpy as np


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
        print(f"{type(self).__name__}:")
        for k, v in self.__dict__.items():
            print(f"\t{k} = {v}")


class MetricAnalyser:
    """
    Container for all the metrics, for purposes of statistical analysis.
    """
    metrics: Dict[str, Metrics]

    def average_accuracy(self) -> float:
        """
        Averages amount of values in `self.metrics` which are investable.
        """
        return mean(m.are_investable() for m in self.metrics.values())


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
