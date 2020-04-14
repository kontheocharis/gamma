use std::fmt;

use chrono::{NaiveDate, Datelike};
use enum_iterator::IntoEnumIterator;
use ndarray::prelude::*;
use ndarray::{azip, Array1, Array2, ArrayView1, ArrayView2, Axis, ScalarOperand, Zip};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;

use crate::financials::{Companies, DailyField, Financials, YearlyField};
use crate::util::IndexEnum;

pub mod v1 {
    use super::*;

    #[derive(Debug)]
    pub struct Metrics {
        data: Array2<f32>, // Axis0: metrics, Axis1: companies
        options: Options,
    }

    #[derive(Debug, Clone)]
    pub struct Options {
        pub cash_flows_back: usize, // how many years to consider positive cash flow including this one.
        pub buy_date: NaiveDate,
    }

    #[repr(usize)]
    #[derive(PartialEq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
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

    #[derive(Error, Debug)]
    pub enum CalculationError {
        #[error("insufficient data to calculate cash flow history")]
        InsufficientCashFlowData,
    }

    impl Metrics {
        pub const FIELD_AXIS: Axis = Axis(0);
        pub const COMPANY_AXIS: Axis = Axis(1);

        pub fn calculate(
            financials: &Financials,
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
                        .index_axis_mut(Self::FIELD_AXIS, Field::$field as usize)
                        .assign(&(contents))
                };
            }

            macro_rules! metric {
                ($field: ident) => {
                    metrics.index_axis(Self::FIELD_AXIS, Field::$field as usize)
                };
            }

            macro_rules! yearly_financial {
                ($field: ident) => {
                    financials.yearly().slice(s![
                        financials.year_to_index(year),
                        YearlyField::$field as usize,
                        ..
                    ])
                };
            }

            macro_rules! daily_financial {
                ($field: ident, $date: expr) => {
                    financials
                        .daily()
                        .slice(s![$date, DailyField::$field as usize, ..])
                };
            }

            metric_set!(
                BuySharePrice,
                daily_financial!(HighSharePrice, financials.date_to_index(options.buy_date))
            );

            metric_set!(
                Nav,
                (&yearly_financial!(TotalAssets) - &yearly_financial!(TotalLiabilities))
                    / &yearly_financial!(TotalOutstandingShares)
            );

            let total_good_assets =
                &yearly_financial!(CashShortTermInvestments) + &(&yearly_financial!(Ppe) / 2.0);

            metric_set!(
                Cnav1,
                (total_good_assets - &yearly_financial!(TotalLiabilities))
                    / &yearly_financial!(TotalOutstandingShares)
            );

            metric_set!(
                PeRatio,
                &yearly_financial!(SharePriceAtReport) / &yearly_financial!(Eps)
            );

            metric_set!(
                DebtToEquityRatio,
                &yearly_financial!(TotalDebt) / &yearly_financial!(TotalShareholdersEquity)
            );

            metric_set!(
                PotentialRoi,
                (&metric!(Nav) - &metric!(Cnav1)) / &metric!(Cnav1)
            );

            metric_set!(
                MarketCap,
                &yearly_financial!(TotalOutstandingShares) * &yearly_financial!(SharePriceAtReport)
            );

            metric_set!(CashFlows, {
                let year_i = financials.year_to_index(year);

                if year_i < options.cash_flows_back {
                    return Err(CalculationError::InsufficientCashFlowData);
                }

                let (y_start, y_end) = (year_i - options.cash_flows_back, year_i + 1);

                let yearly = financials.yearly();
                let cash_flows =
                    yearly.slice(s![y_start..y_end, YearlyField::CashFlow as usize, ..]);

                cash_flows.map_axis(Axis(0), |years| {
                    bool_to_f32(years.iter().all(|&flow| flow > 0.0))
                })
            });

            Ok(Metrics {
                data: metrics,
                options,
            })
        }

        pub fn get_metric<'a>(&'a self, field: Field) -> ArrayView1<'a, f32> {
            self.data.index_axis(Self::FIELD_AXIS, field as usize)
        }

        pub fn get_company<'a>(&'a self, company_index: usize) -> ArrayView1<'a, f32> {
            self.data.index_axis(Self::COMPANY_AXIS, company_index)
        }

        pub fn inner(&self) -> ArrayView2<f32> {
            self.data.view()
        }

        pub fn evaluate(&self) -> Evaluated {
            let companies_count = self.data.len_of(Self::COMPANY_AXIS);

            macro_rules! metric {
                ($field:ident, $index:expr) => {
                    self.get_metric(Field::$field)[$index]
                };
            }

            // ndarray::Zip doesn't support this many elements at once :(
            let evalutated = (0..companies_count)
                .filter_map(|i| {
                    if Field::into_enum_iter()
                        .map(|field| self.get_metric(field)[i])
                        .any(f32::is_nan)
                    {
                        None
                    } else {
                        let decision = metric!(Cnav1, i) > metric!(BuySharePrice, i)
                            && metric!(PeRatio, i) < 15.0
                            && metric!(CashFlows, i) > 0.0
                            && metric!(DebtToEquityRatio, i) < 1.0
                            && metric!(PotentialRoi, i) > 2.0
                            && metric!(MarketCap, i) > 10.0_f32.powf(9.0);
                        Some(decision)
                    }
                })
                .collect();

            Evaluated { data: evalutated }
        }
    }

    #[derive(Debug)]
    pub struct Evaluated {
        data: Array1<bool>,
    }

    impl fmt::Display for Evaluated {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "Evaluated: {:.2}%", self.percent_investable() * 100.0)
        }
    }

    impl Evaluated {
        pub fn percent_investable(&self) -> f32 {
            self.data.iter().map(|&x| bool_to_f32(x)).sum::<f32>() / self.data.len() as f32
        }

        pub fn companies_investable<'a>(&'a self) -> impl Iterator<Item = usize> + 'a {
            self.data
                .iter()
                .enumerate()
                .filter(|(_, &x)| x)
                .map(|(i, _)| i)
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
        } else {
            if value > 0.0 {
                Some(true)
            } else {
                Some(false)
            }
        }
    }
}
