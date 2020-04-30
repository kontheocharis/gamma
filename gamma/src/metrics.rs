use std::collections::HashMap;

use chrono::{Datelike, Duration, NaiveDate};
use enum_iterator::IntoEnumIterator;
use log::*;
use ndarray::prelude::*;
use ndarray::{Array1, Array2, ArrayView1, ArrayView2, Axis};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::financials::{Companies, DailyField, Financials, YearlyField};
use crate::util::IndexEnum;

pub mod v1 {
    use super::*;

    #[derive(Debug)]
    pub struct Metrics<'a> {
        data: Array2<f32>, // Axis0: metrics, Axis1: companies
        financials: &'a Financials,
        options: Options,
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Options {
        pub buy_date: NaiveDate,
        pub cash_flows_back: usize, // how many years to consider positive cash flow including this one.
        pub max_pe_ratio: f32,
        pub max_debt_to_equity: f32,
        pub min_potential_roi: f32,
        pub min_market_cap: f32,
        pub return_percent: f32,
        pub lookahead_years: usize,
        pub ignore_cnav_cmp: bool,
    }

    #[repr(usize)]
    #[derive(
        PartialEq, Eq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone,
    )]
    pub enum Field {
        Cnav1,
        Nav,
        PeRatio,
        CashFlows,
        BuySharePrice, // from daily
        DebtToEquityRatio,
        PotentialRoi,
        MarketCap,
    }

    impl IndexEnum for Field {}

    #[derive(Error, Debug)]
    pub enum CalculationError {
        #[error("insufficient data to calculate cash flow history")]
        InsufficientCashFlowData,
    }

    impl<'a> Metrics<'a> {
        pub const FIELD_AXIS: Axis = Axis(0);
        pub const COMPANY_AXIS: Axis = Axis(1);

        pub fn calculate(
            financials: &'a Financials,
            options: Options,
        ) -> Result<Self, CalculationError> {
            let mut metrics = Array2::from_elem(
                (Field::VARIANT_COUNT, financials.companies().len()),
                f32::NAN,
            );

            let year = options.buy_date.year();

            macro_rules! metric_set {
                ($field: ident, $contents: expr) => {
                    let contents = $contents;
                    metrics
                        .index_axis_mut(Self::FIELD_AXIS, Field::$field.index())
                        .assign(&(contents))
                };
            }

            macro_rules! metric {
                ($field: ident) => {
                    &metrics.index_axis(Self::FIELD_AXIS, Field::$field.index())
                };
            }

            macro_rules! yearly_financial {
                ($field: ident) => {
                    &financials.yearly().slice(s![
                        financials.year_to_index(year),
                        YearlyField::$field.index(),
                        ..
                    ])
                };
            }

            macro_rules! daily_financial {
                ($field: ident, $date: expr) => {
                    &financials
                        .daily()
                        .slice(s![$date, DailyField::$field.index(), ..])
                };
            }

            metric_set!(
                BuySharePrice,
                daily_financial!(HighSharePrice, financials.date_to_index(options.buy_date))
            );

            metric_set!(
                Nav,
                (yearly_financial!(TotalAssets) - yearly_financial!(TotalLiabilities))
                    / yearly_financial!(TotalOutstandingShares)
            );

            let total_good_assets =
                (yearly_financial!(Ppe) / 2.0) + yearly_financial!(CashShortTermInvestments);

            metric_set!(
                Cnav1,
                (total_good_assets - yearly_financial!(TotalLiabilities))
                    / yearly_financial!(TotalOutstandingShares)
            );

            metric_set!(
                PeRatio,
                yearly_financial!(SharePriceAtReport) / yearly_financial!(Eps)
            );

            metric_set!(
                DebtToEquityRatio,
                yearly_financial!(TotalDebt) / yearly_financial!(TotalShareholdersEquity)
            );

            metric_set!(
                PotentialRoi,
                (metric!(Nav) - metric!(Cnav1)) / metric!(Cnav1)
            );

            metric_set!(
                MarketCap,
                yearly_financial!(TotalOutstandingShares) * yearly_financial!(SharePriceAtReport)
            );

            metric_set!(CashFlows, {
                let year_i = financials.year_to_index(year);

                if year_i < options.cash_flows_back {
                    return Err(CalculationError::InsufficientCashFlowData);
                }

                let (y_start, y_end) = (year_i - options.cash_flows_back, year_i + 1);

                let yearly = financials.yearly();
                let cash_flows =
                    yearly.slice(s![y_start..y_end, YearlyField::CashFlow.index(), ..]);

                cash_flows.map_axis(Axis(0), |years| {
                    bool_to_f32(years.iter().all(|&flow| flow > 0.0))
                })
            });

            Ok(Metrics {
                data: metrics,
                financials: &financials,
                options,
            })
        }

        pub fn get_metric(&self, field: Field) -> ArrayView1<'_, f32> {
            self.data.index_axis(Self::FIELD_AXIS, field.index())
        }

        pub fn get_company(&self, company_index: usize) -> ArrayView1<'_, f32> {
            self.data.index_axis(Self::COMPANY_AXIS, company_index)
        }

        pub fn inner(&self) -> ArrayView2<f32> {
            self.data.view()
        }

        pub fn evaluate(&self) -> Evaluated<'_> {
            let companies_count = self.data.len_of(Self::COMPANY_AXIS);

            macro_rules! metric {
                ($field:ident, $index:expr) => {
                    self.get_metric(Field::$field)[$index]
                };
            }

            let evalutated = (0..companies_count)
                .map(|i| {
                    if self.get_company(i).iter().any(|value| value.is_nan()) {
                        Evaluation::InsufficientData
                    } else {
                        let decision = (self.options.ignore_cnav_cmp
                            || metric!(Cnav1, i) > metric!(BuySharePrice, i))
                            && metric!(CashFlows, i) > 0.0
                            && metric!(DebtToEquityRatio, i) < self.options.max_debt_to_equity
                            && metric!(PotentialRoi, i) > self.options.min_potential_roi
                            && metric!(MarketCap, i) > self.options.min_market_cap;

                        if decision {
                            Evaluation::Investable
                        } else {
                            Evaluation::NotInvestable
                        }
                    }
                })
                .collect();

            Evaluated {
                data: evalutated,
                metrics: self,
                financials: self.financials,
                options: &self.options,
            }
        }
    }

    #[derive(Debug, PartialEq, Eq, Clone, Copy)]
    pub enum Evaluation {
        InsufficientData,
        Investable,
        NotInvestable,
    }

    #[derive(Debug)]
    pub struct Evaluated<'a> {
        data: Array1<Evaluation>,
        metrics: &'a Metrics<'a>,
        financials: &'a Financials,
        options: &'a Options,
    }

    impl Evaluated<'_> {
        pub fn companies_sufficient<'a>(&'a self) -> impl Iterator<Item=usize> + 'a {
            self.data
                .iter()
                .enumerate()
                .filter(|(_, &evaluation)| evaluation != Evaluation::InsufficientData)
                .map(|(company_index, _)| company_index)
        }

        pub fn companies_investable<'a>(&'a self) -> impl Iterator<Item = usize> + 'a {
            self.data
                .iter()
                .enumerate()
                .filter(|(_, &evaluation)| evaluation == Evaluation::Investable)
                .map(|(company_index, _)| company_index)
        }

        pub fn backtrack(&self) -> Backtracked<'_> {
            let data = self
                .companies_investable()
                .map(|company_index| {
                    let date_start = self.financials.date_to_index(self.options.buy_date);
                    let date_end = self.financials.date_to_index(
                        self.options.buy_date
                            + Duration::weeks(52 * self.options.lookahead_years as i64),
                    );

                    let data = self.financials.daily().slice(s![
                        date_start..=date_end,
                        DailyField::HighSharePrice.index(),
                        company_index
                    ]);

                    let buy_price = self.metrics.get_metric(Field::BuySharePrice)[company_index];

                    let result = data
                        .iter()
                        .find(|&&price| price >= buy_price * (1.0 + self.options.return_percent))
                        .map(|_| BacktrackResult::ReachedReturnPercent)
                        .unwrap_or_else(|| {
                            if *data.iter().last().unwrap() > buy_price {
                                BacktrackResult::GainAtEnd
                            } else {
                                BacktrackResult::LossAtEnd
                            }
                        });

                    (company_index, result)
                })
                .collect();

            Backtracked {
                data,
                companies: self.financials.companies(),
            }
        }
    }

    #[derive(Debug, Eq, PartialEq, Clone, Copy)]
    pub enum BacktrackResult {
        ReachedReturnPercent,
        GainAtEnd,
        LossAtEnd,
    }

    #[derive(Debug)]
    pub struct Backtracked<'a> {
        data: HashMap<usize, BacktrackResult>,
        companies: &'a Companies,
    }

    #[derive(Debug, Default, Clone)]
    pub struct BacktrackStatistics {
        pub n_reached_percent: usize,
        pub n_gain_at_end: usize,
        pub n_loss_at_end: usize,
    }

    impl Backtracked<'_> {
        pub fn stats(&self) -> BacktrackStatistics {
            self.data
                .values()
                .fold(BacktrackStatistics::default(), |acc, res| match res {
                    BacktrackResult::ReachedReturnPercent => BacktrackStatistics {
                        n_reached_percent: acc.n_reached_percent + 1,
                        ..acc
                    },
                    BacktrackResult::GainAtEnd => BacktrackStatistics {
                        n_gain_at_end: acc.n_gain_at_end + 1,
                        ..acc
                    },
                    BacktrackResult::LossAtEnd => BacktrackStatistics {
                        n_loss_at_end: acc.n_loss_at_end + 1,
                        ..acc
                    },
                })
        }
    }

    // private
    fn bool_to_f32(value: bool) -> f32 {
        if value {
            1.0
        } else {
            0.0
        }
    }

    fn f32_to_bool(value: f32) -> Option<bool> {
        if value.is_nan() {
            None
        } else if value > 0.0 {
            Some(true)
        } else {
            Some(false)
        }
    }
}
