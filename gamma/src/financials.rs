use std::collections::HashMap;
use std::convert::TryFrom;
use std::error::Error;
use std::iter;
use std::path::Path;

use async_trait::async_trait;
use chrono::{Datelike, NaiveDate};
use futures::prelude::*;
use ndarray::{s, Array1, Array2, Array3, ArrayView1, ArrayView2, Axis};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;
use tokio::fs;
use tokio::io::AsyncWriteExt;

use crate::traits::CountVariants;

const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";

const YEARLY_FOLDER: &str = "yearly";
const DAILY_FOLDER: &str = "daily";
const COMPANY_FILE: &str = "companies";

/// Error returned by I/O methods on `Financials` (i.e. `save` and `load`).
#[derive(Error, Debug)]
pub enum IoError {
    #[error(transparent)]
    Internal(#[from] std::io::Error),
}

type IoResult<T> = Result<T, IoError>;

#[repr(usize)]
#[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
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
#[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
pub enum DailyField {
    HighSharePrice,
    LowSharePrice,
    Volume,
}

#[derive(Debug)]
pub struct Financials {
    companies: HashMap<String, usize>,
    yearly_data: Array3<f32>, // Axis(0): year, Axis(1): x::Field, Axis(2): company
    daily_data: Array3<f32>,  // Axis(0): day, Axis(1): x::Field, Axis(2): company
}

#[derive(Debug, Clone)]
pub struct LoaderOptions {
    pub yearly_min: i32,
    pub yearly_max: i32,
    pub daily_min: NaiveDate,
    pub daily_max: NaiveDate,
}

impl LoaderOptions {
    pub fn are_ok(&self) -> bool {
        self.yearly_min < self.yearly_max && self.daily_min < self.daily_max
    }
}

#[derive(Error, Debug)]
pub enum LoadError {
    #[error("Given LoaderOptions are invalid (check date ranges)")]
    InvalidOptions,

    #[error("Date bounds are not valid for input data: {0}")]
    OutOfBoundDates(String),
}

impl<'a> Financials
where
    Self: 'a,
{
    pub const TIME_AXIS: Axis = Axis(0);
    pub const FIELD_AXIS: Axis = Axis(1);
    pub const COMPANY_AXIS: Axis = Axis(2);

    pub fn load(repr: StorageRepr, options: &LoaderOptions) -> Result<Financials, LoadError> {
        if !options.are_ok() {
            return Err(LoadError::InvalidOptions);
        }

        let no_of_companies = repr.companies.len();

        let mut yearly_data = Array3::from_elem(
            (
                (options.yearly_max - options.yearly_min + 1) as usize,
                YearlyField::COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        for year in options.yearly_min..=options.yearly_max {
            let data = repr
                .yearly
                .get(&year)
                .ok_or(LoadError::OutOfBoundDates(format!(
                    "year {} not found for yearly data",
                    year
                )))?;

            yearly_data
                .slice_mut(s![(year - options.yearly_min) as usize, .., ..])
                .assign(&data);
        }

        let mut daily_data = Array3::from_elem(
            (
                (options.daily_max.num_days_from_ce() - options.daily_min.num_days_from_ce() + 1)
                    as usize,
                DailyField::COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        let (daily_min_year, daily_max_year) = (options.daily_min.year(), options.daily_max.year());

        let mut curr_offset = 0;
        for year in daily_min_year..=daily_max_year {
            let data = repr
                .daily
                .get(&year)
                .ok_or(LoadError::OutOfBoundDates(format!(
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
            yearly_data,
            daily_data,
        })
    }

    pub async fn load_from_path(
        path: impl AsRef<Path>,
        options: &LoaderOptions,
    ) -> IoResult<Financials> {
        unimplemented!()
    }
}

#[derive(Debug)]
pub struct StorageRepr {
    pub companies: HashMap<String, usize>,
    pub yearly: HashMap<i32, Array2<f32>>,
    pub daily: HashMap<i32, Array3<f32>>, // Axis(0): 0-365 or 0-364
}

pub trait FetcherError = Error;

#[derive(Error, Debug)]
pub enum FetcherSaveError<T: FetcherError> {
    #[error("I/O error while saving: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Fetcher error while saving: {0}")]
    FetcherError(T),

    #[error("Encoding error while saving: {0}")]
    EncodingError(#[from] bincode::Error),
}

#[async_trait]
pub trait Fetcher {
    /// The error type returned if loading the financial data fails.
    type Error: FetcherError;

    /// Loads financials according to `options`.
    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::Error>;

    async fn save_to_path<P: AsRef<Path> + Send>(
        &mut self,
        path: P,
    ) -> Result<(), FetcherSaveError<Self::Error>> {
        let path_ref = path.as_ref();
        let storage_repr = self
            .to_storage_repr()
            .await
            .map_err(FetcherSaveError::FetcherError)?;

        // Create paths needed
        future::try_join(
            fs::create_dir_all(path_ref.join(YEARLY_FOLDER)),
            fs::create_dir_all(path_ref.join(DAILY_FOLDER)),
        )
        .await?;

        let path_for = |year: i32, prefix: &str| path_ref.join(prefix).join(year.to_string());

        let yearly_files = storage_repr
            .yearly
            .iter()
            .map(|(&year, array)| (path_for(year, YEARLY_FOLDER), bincode::serialize(array)));

        let daily_files = storage_repr
            .daily
            .iter()
            .map(|(&year, array)| (path_for(year, DAILY_FOLDER), bincode::serialize(array)));

        let company_file = iter::once((
            path_ref.join(COMPANY_FILE),
            bincode::serialize(&storage_repr.companies),
        ));

        future::try_join_all(yearly_files.chain(daily_files).chain(company_file).map(
            |(path, data)| {
                fs::File::create(path)
                    .map_err(FetcherSaveError::IoError)
                    .and_then(async move |mut file| Ok(file.write_all(data?.as_ref()).await?))
            },
        ))
        .await?;

        Ok(())
    }
}
