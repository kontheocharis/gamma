use std::collections::{HashMap, HashSet};

use chrono::{Datelike, NaiveDate};
use enum_iterator::IntoEnumIterator;
use log::*;
use ndarray::prelude::*;
use num_enum::{IntoPrimitive, TryFromPrimitive};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::financials::{DailyField, Financials, YearlyField};
use crate::util::{CompanyId, IndexEnum};

#[derive(Debug)]
pub struct Metrics<'a> {
    data: Array2<f32>, // Axis0: metrics, Axis1: companies
    pub(self) financials: &'a Financials,
    pub(self) options: Options,
}

#[derive(Error, Debug)]
#[error("one or more options are invalid")]
pub struct OptionsError;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Options {
    pub buy_date: NaiveDate,
    pub sell_date: NaiveDate,
    pub cash_flows_back: usize, // how many years to consider positive cash flow including this one.
    pub max_pe_ratio: f32,
    pub max_debt_to_equity: f32,
    pub min_potential_roi: f32,
    pub min_market_cap: f32,
    pub return_percent: f32,
    pub ignore_cnav_cmp: bool,
}

impl Options {
    fn verify(&self) -> Result<(), OptionsError> {
        if self.buy_date >= self.sell_date {
            Err(OptionsError)
        } else {
            Ok(())
        }
    }
}

#[repr(usize)]
#[derive(
    PartialEq, Eq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone, Hash,
)]
pub enum Field {
    BuySharePrice, // from daily
    CashFlows,
    Cnav,
    CnavBuySharePriceDiff,
    CnavNavDiff,
    DebtToEquityRatio,
    MarketCap,
    Nav,
    PeRatio,
    PotentialRoi,
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

    pub fn calculate(financials: &'a Financials, options: Options) -> anyhow::Result<Self> {
        options.verify()?;
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
            Cnav,
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

        metric_set!(PotentialRoi, (metric!(Nav) - metric!(Cnav)) / metric!(Cnav));

        metric_set!(
            MarketCap,
            yearly_financial!(TotalOutstandingShares) * yearly_financial!(SharePriceAtReport)
        );

        metric_set!(CnavNavDiff, metric!(Cnav) - metric!(Nav));

        metric_set!(
            CnavBuySharePriceDiff,
            metric!(Cnav) - metric!(BuySharePrice)
        );

        metric_set!(CashFlows, {
            let year_i = financials.year_to_index(year);

            if year_i < options.cash_flows_back {
                return Err(CalculationError::InsufficientCashFlowData.into());
            }

            let (y_start, y_end) = (year_i - options.cash_flows_back, year_i + 1);

            let yearly = financials.yearly();
            let cash_flows = yearly.slice(s![y_start..y_end, YearlyField::CashFlow.index(), ..]);

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

    pub fn get_company(&self, company_index: CompanyId) -> ArrayView1<'_, f32> {
        self.data.index_axis(Self::COMPANY_AXIS, company_index)
    }

    pub fn inner(&self) -> ArrayView2<f32> {
        self.data.view()
    }
}

#[derive(Debug)]
pub struct Bounds {
    inner: Array1<(f32, f32)>,
}

impl Bounds {
    pub fn unconstained() -> Self {
        Bounds {
            inner: Array1::from_elem((Field::VARIANT_COUNT,), (f32::NEG_INFINITY, f32::INFINITY)),
        }
    }

    pub fn from_legacy_options(options: &Options) -> Self {
        let mut bounds = Self::unconstained();
        use Field::*;

        if !options.ignore_cnav_cmp {
            bounds.set(CnavBuySharePriceDiff, (0.0, f32::INFINITY));
        }

        bounds.set(CashFlows, (0.0, f32::INFINITY));
        bounds.set(CnavNavDiff, (f32::NEG_INFINITY, 0.0));
        bounds.set(
            DebtToEquityRatio,
            (f32::NEG_INFINITY, options.max_debt_to_equity),
        );
        bounds.set(MarketCap, (options.min_market_cap, f32::INFINITY));
        bounds.set(PeRatio, (f32::NEG_INFINITY, options.max_pe_ratio));
        bounds.set(PotentialRoi, (options.min_potential_roi, f32::INFINITY));

        bounds
    }

    pub fn set(&mut self, field: Field, new_bounds: (f32, f32)) {
        self.inner[field.index()] = new_bounds;
    }

    pub fn get(&self, field: Field) -> (f32, f32) {
        self.inner[field.index()]
    }
}

#[derive(Debug)]
pub struct Evaluator<'a> {
    metrics: &'a Metrics<'a>,
}

impl<'a> Evaluator<'a> {
    pub fn new(metrics: &'a Metrics<'a>) -> Self {
        Self { metrics }
    }

    pub fn evaluate(&self, bounds: Bounds, ignore: &HashSet<Field>) -> Evaluated<'a> {
        let companies_count = self.metrics.data.len_of(Metrics::COMPANY_AXIS);

        let evalutated = (0..companies_count)
            .map(|company_idx| {
                if self
                    .metrics
                    .get_company(company_idx)
                    .iter()
                    .any(|value| value.is_nan())
                {
                    Evaluation::InsufficientData
                } else {
                    let decision = Field::into_enum_iter()
                        .filter(|field| !ignore.contains(&field))
                        .all(|field| {
                            let metric_value = self.metrics.get_metric(field)[company_idx];
                            let (min, max) = bounds.get(field);

                            min < metric_value && metric_value < max
                        });

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
            metrics: self.metrics,
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
}

impl Evaluated<'_> {
    pub fn companies_sufficient<'a>(&'a self) -> impl Iterator<Item = CompanyId> + 'a {
        self.data
            .iter()
            .enumerate()
            .filter(|(_, &evaluation)| evaluation != Evaluation::InsufficientData)
            .map(|(company_index, _)| company_index)
    }

    pub fn companies_investable<'a>(&'a self) -> impl Iterator<Item = CompanyId> + 'a {
        self.data
            .iter()
            .enumerate()
            .filter(|(_, &evaluation)| evaluation == Evaluation::Investable)
            .map(|(company_index, _)| company_index)
    }

    pub fn backtrack(&self) -> Backtracked {
        let data = self
            .companies_investable()
            .map(|company_index| {
                let financials = self.metrics.financials;
                let date_start = financials.date_to_index(self.metrics.options.buy_date);
                let date_end = financials.date_to_index(self.metrics.options.sell_date);

                let data = financials.daily().slice(s![
                    date_start..=date_end,
                    DailyField::HighSharePrice.index(),
                    company_index
                ]);

                let buy_price = self.metrics.get_metric(Field::BuySharePrice)[company_index];

                let result_tup = data
                    .iter()
                    .find(|&&price| {
                        price >= buy_price * (1.0 + self.metrics.options.return_percent)
                    })
                    .map(|&price| (price, BacktrackResult::ReachedReturnPercent))
                    .unwrap_or_else(|| {
                        let last_price = *data.iter().last().unwrap();
                        if last_price > buy_price {
                            (last_price, BacktrackResult::GainAtEnd)
                        } else {
                            (last_price, BacktrackResult::LossAtEnd)
                        }
                    });

                (company_index, result_tup)
            })
            .collect();

        Backtracked { data }
    }
}

#[derive(Debug, Eq, PartialEq, Clone, Copy)]
pub enum BacktrackResult {
    ReachedReturnPercent,
    GainAtEnd,
    LossAtEnd,
}

#[derive(Debug)]
pub struct Backtracked {
    data: HashMap<CompanyId, (f32, BacktrackResult)>,
}

#[derive(Debug, Default, Clone)]
pub struct BacktrackStatistics {
    pub n_reached_percent: usize,
    pub n_gain_at_end: usize,
    pub n_loss_at_end: usize,
}

impl Backtracked {
    pub fn stats(&self) -> BacktrackStatistics {
        self.data.values().map(|(_, result)| result).fold(
            BacktrackStatistics::default(),
            |acc, res| match res {
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
            },
        )
    }

    pub fn companies_which<'a>(
        &'a self,
        condition: BacktrackResult,
    ) -> impl Iterator<Item = (CompanyId, f32)> + 'a {
        self.data
            .iter()
            .filter_map(move |(&company_idx, &(price, result))| {
                if result == condition {
                    Some((company_idx, price))
                } else {
                    None
                }
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
