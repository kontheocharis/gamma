use std::fmt;

use enum_iterator::IntoEnumIterator;
use ndarray::prelude::*;
use ndarray::{azip, Array1, Array2, ArrayView1, ArrayView2, Axis, ScalarOperand, Zip};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;

use crate::financials::{Financials, YearlyField};
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
        pub year: i32,
        pub cash_flows_back: usize, // how many years to consider positive cash flow including this one.
    }

    #[repr(usize)]
    #[derive(PartialEq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
    pub enum Field {
        Cnav1,
        Nav,
        PeRatio,
        CashFlows,
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

            macro_rules! financial {
                ($field: ident) => {
                    financials.yearly().slice(s![
                        financials.year_to_index(options.year),
                        YearlyField::$field as usize,
                        ..
                    ])
                };
            }

            metric_set!(
                Nav,
                (&financial!(TotalAssets) - &financial!(TotalLiabilities))
                    / &financial!(TotalOutstandingShares)
            );

            let total_good_assets =
                &financial!(CashShortTermInvestments) + &(&financial!(Ppe) / 2.0);

            metric_set!(
                Cnav1,
                (total_good_assets - &financial!(TotalLiabilities))
                    / &financial!(TotalOutstandingShares)
            );

            metric_set!(PeRatio, &financial!(SharePriceAtReport) / &financial!(Eps));

            metric_set!(
                DebtToEquityRatio,
                &financial!(TotalDebt) / &financial!(TotalShareholdersEquity)
            );

            metric_set!(
                PotentialRoi,
                (&metric!(Nav) / &financial!(SharePriceAtReport)) - 1.0
            );

            metric_set!(
                MarketCap,
                &financial!(TotalOutstandingShares) * &financial!(SharePriceAtReport)
            );

            metric_set!(CashFlows, {
                let year_i = financials.year_to_index(options.year);

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

        pub fn evaluate(&self) -> Investable {
            let companies_count = self.data.len_of(Self::COMPANY_AXIS);

            macro_rules! metric {
                ($field:ident, $index:expr) => {
                    self.get_metric(Field::$field)[$index]
                };
            }

            // ndarray::Zip doesn't support this many elements at once :(
            let investable = (0..companies_count)
                .map(|i| {
                    metric!(Cnav1, i) < metric!(Nav, i)
                        && metric!(PeRatio, i) < 15.0
                        && metric!(CashFlows, i) > 0.0
                        && metric!(DebtToEquityRatio, i) < 1.0
                        && metric!(PotentialRoi, i) > 1.0
                        && metric!(MarketCap, i) > 10.0_f32.powf(9.0)
                })
                .collect();

            Investable(investable)
        }
    }

    #[derive(Debug)]
    pub struct Investable(Array1<bool>); // Axis0: companies

    impl fmt::Display for Investable {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "Investable: {:.2}%", self.percent_investable() * 100.0)
        }
    }

    impl Investable {
        pub fn percent_investable(&self) -> f32 {
            self.0.iter().map(|&x| bool_to_f32(x)).sum::<f32>() / self.0.len() as f32
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

    fn f32_to_bool(value: f32) -> bool {
        if value > 0.0 {
            true
        } else {
            false
        }
    }
}
