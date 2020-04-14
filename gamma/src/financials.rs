use std::collections::HashMap;
use std::path::Path;

use chrono::{Datelike, NaiveDate};
use enum_iterator::IntoEnumIterator;
use ndarray::{s, Array3, ArrayView3, Axis};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;

use crate::fetching::StorageRepr;

#[repr(usize)]
#[derive(PartialEq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
pub enum YearlyField {
    CashShortTermInvestments,
    Ppe,
    TotalLiabilities,
    TotalAssets,
    TotalDebt,
    TotalShareholdersEquity,
    TotalOutstandingShares,
    Eps,
    SharePriceAtReport,
    CashFlow,
}

#[repr(usize)]
#[derive(PartialEq, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
pub enum DailyField {
    HighSharePrice,
    LowSharePrice,
    Volume,
}

#[derive(Debug, Clone)]
pub struct Options {
    pub yearly_min: i32,
    pub yearly_max: i32,
    pub daily_min: NaiveDate,
    pub daily_max: NaiveDate,
}

#[derive(Error, Debug)]
#[error("Invalid options: {0}")]
pub struct InvalidOptionsError(String);

impl Options {
    pub fn ensure_ok(&self) -> Result<(), InvalidOptionsError> {
        if self.yearly_min < self.yearly_max && self.daily_min < self.daily_max {
            Ok(())
        } else {
            Err(InvalidOptionsError("invalid date ranges".to_string()))
        }
    }
}

pub type Companies = HashMap<String, usize>;
pub type YearlyData = Array3<f32>;
pub type DailyData = Array3<f32>;

#[derive(Debug)]
pub struct Financials {
    companies: Companies,
    options: Options,
    yearly_data: YearlyData, // Axis(0): year, Axis(1): x::Field, Axis(2): company
    daily_data: DailyData,  // Axis(0): day, Axis(1): x::Field, Axis(2): company
}

impl Financials {
    pub const TIME_AXIS: Axis = Axis(0);
    pub const FIELD_AXIS: Axis = Axis(1);
    pub const COMPANY_AXIS: Axis = Axis(2);

    pub fn yearly<'a>(&'a self) -> &'a YearlyData {
        &self.yearly_data
    }

    pub fn daily<'a>(&'a self) -> &'a DailyData {
        &self.daily_data
    }

    pub fn companies<'a>(&'a self) -> &'a Companies {
        &self.companies
    }

    pub fn index_to_year(&self, index: usize) -> i32 {
        index as i32 + self.options.yearly_min
    }

    pub fn year_to_index(&self, year: i32) -> usize {
        (year - self.options.yearly_min) as usize
    }

    pub fn index_to_date(&self, index: usize) -> NaiveDate {
        NaiveDate::from_num_days_from_ce(index as i32 + self.options.daily_min.num_days_from_ce())
    }

    pub fn date_to_index(&self, date: NaiveDate) -> usize {
        (date.num_days_from_ce() - self.options.daily_min.num_days_from_ce()) as usize
    }

    pub fn company_to_index(&self, company: &str) -> usize {
        *self.companies.get(company).unwrap()
    }

    pub fn index_to_company(&self, index: usize) -> &str {
        self.companies
            .iter()
            .find_map(|(k, &v)| if v == index { Some(k.as_ref()) } else { None })
            .unwrap()
    }

    pub fn year_range(&self) -> (i32, i32) {
        (self.options.yearly_min, self.options.yearly_max)
    }

    pub fn date_range(&self) -> (NaiveDate, NaiveDate) {
        (self.options.daily_min, self.options.daily_max)
    }

    pub fn valid_year_index(&self, index: usize) -> bool {
        index < self.yearly_data.len_of(Self::TIME_AXIS)
    }

    pub fn valid_date_index(&self, index: usize) -> bool {
        index < self.daily_data.len_of(Self::TIME_AXIS)
    }

    pub fn from_repr(repr: StorageRepr, options: Options) -> anyhow::Result<Financials> {
        options.ensure_ok()?;
        Self::from_repr_unchecked(repr, options)
    }

    pub async fn from_path<P: AsRef<Path>>(
        path: P,
        options: Options,
    ) -> anyhow::Result<Financials> {
        let path_ref = path.as_ref();
        options.ensure_ok()?;

        let repr = StorageRepr::load_from_path(
            path_ref,
            (options.yearly_min, options.yearly_max),
            (options.daily_min.year(), options.daily_max.year()),
        )
        .await?;

        Self::from_repr_unchecked(repr, options)
    }

    fn from_repr_unchecked(repr: StorageRepr, options: Options) -> anyhow::Result<Financials> {
        let no_of_companies = repr.companies.len();

        let mut yearly_data = YearlyData::from_elem(
            (
                (options.yearly_max - options.yearly_min + 1) as usize,
                YearlyField::VARIANT_COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        for year in options.yearly_min..=options.yearly_max {
            let data = repr.yearly.get(&year).ok_or(InvalidOptionsError(format!(
                "year {} not found for yearly data",
                year
            )))?;

            yearly_data
                .slice_mut(s![(year - options.yearly_min) as usize, .., ..])
                .assign(&data);
        }

        let mut daily_data = DailyData::from_elem(
            (
                (options.daily_max.num_days_from_ce() - options.daily_min.num_days_from_ce() + 1)
                    as usize,
                DailyField::VARIANT_COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        let (daily_min_year, daily_max_year) = (options.daily_min.year(), options.daily_max.year());

        let mut curr_offset = 0;
        for year in daily_min_year..=daily_max_year {
            let data = repr.daily.get(&year).ok_or(InvalidOptionsError(format!(
                "year {} not found for daily data",
                year
            )))?;

            let days_in_year = NaiveDate::from_ymd(year, 12, 31).ordinal() as usize;

            let day_min = if year == daily_min_year {
                options.daily_min.ordinal0() as usize
            } else {
                0
            };

            let day_max = if year == daily_max_year {
                options.daily_max.ordinal0() as usize
            } else {
                (days_in_year - 1) as usize
            };

            daily_data
                .slice_mut(s![
                    (curr_offset)..(curr_offset + (day_max - day_min) + 1),
                    ..,
                    ..,
                ])
                .assign(&data.slice(s![day_min..(day_max + 1), .., ..]));

            curr_offset += day_max - day_min + 1;
        }

        Ok(Financials {
            companies: repr.companies,
            options,
            yearly_data,
            daily_data,
        })
    }
}
