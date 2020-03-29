use std::error::{Error};
use std::path::{Path};
use std::collections::{HashMap};
use std::iter;

use async_trait::async_trait;
use futures::prelude::*;
use chrono::{NaiveDate, Datelike};
use ndarray::{Array3, Array2, Array1, Axis, s};
use thiserror::{Error};
use tokio::fs;
use tokio::io::{AsyncWriteExt};

use crate::traits::{CountVariants};

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

pub mod yearly {
    use std::convert::{TryFrom};
    use std::collections::{HashMap};

    use num_enum::{IntoPrimitive, TryFromPrimitive};
    use ndarray::{ArrayView2, ArrayView1, Axis};
    use chrono::{NaiveDate};

    #[repr(usize)]
    #[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
    pub enum Field {
        CashShortTermInvestments,
        Ppe,
        TotalLiabilities,
        TotalAssets,
        TotalDebt,
        TotalShareholdersEquity,
        TotalOutstandingShares,
        Eps,
        SharePriceAtReport,
        CashFlow
    }

    pub struct Financials<'a> {
        pub(super) companies: &'a HashMap<String, usize>,
        pub(super) report_dates: ArrayView1<'a, NaiveDate>,
        pub(super) data: ArrayView2<'a, f32>,
    }

    impl<'a> Financials<'a> {
        pub fn field(&'a self, field: Field) -> FieldView<'a> {
            self.data.index_axis(Axis(0), field.into())
        }

        pub fn fields(&'a self) -> impl Iterator<Item=(Field, FieldView<'a>)> {
            self.data.outer_iter()
                .enumerate()
                .map(|(i, data)| (Field::try_from(i).unwrap(), data))
        }

        pub fn row(&'a self, company: &str) -> Option<RowView<'a>> {
            self.companies.get(company)
                .map(|&index| (self.report_dates[index], self.data.index_axis(Axis(1), index)))
        }
    }

    type FieldView<'a> = ArrayView1<'a, f32>;
    type RowView<'a> = (NaiveDate, ArrayView1<'a, f32>);
}

pub mod daily {
    use num_enum::{IntoPrimitive, TryFromPrimitive};
    use ndarray::{ArrayView2, ArrayView1, Axis};
    use chrono::{NaiveDate};
    

    #[repr(usize)]
    #[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
    pub enum Field {
        HighSharePrice,
        LowSharePrice,
        Volume,
    }

    pub struct Financials<'a> {
        pub(super) report_dates: ArrayView1<'a, NaiveDate>,
        pub(super) data: ArrayView2<'a, f32>,
    }

    impl<'a> Financials<'a> {
        pub fn date_range(&self) -> Option<(&NaiveDate, &NaiveDate)> {
            let slice = self.report_dates.as_slice().unwrap();
            (slice.first()?, slice.last()?)
        }

        pub fn field(&'a self, field: Field) -> FieldView<'a> {
            (self.report_dates.reborrow(), self.data.index_axis(Axis(0), field.into()))
        }
    }

    type FieldView<'a> = (ArrayView1<'a, NaiveDate>, ArrayView1<'a, f32>);
}

#[derive(Debug)]
struct YearlyDataElement {
    pub report_dates: Array1<NaiveDate>,
    pub data: Array2<f32>, // Axis(0): yearly::Field, Axis(1): company
}

#[derive(Debug)]
struct DailyDataElement {
    pub report_dates: Array1<NaiveDate>, // Axis(0): no of days since beginning date
    pub data: Array2<f32>, // Axis(0): daily::Field, Axis(1): no of days since beginning date
}

#[derive(Debug)]
pub struct FinancialStore {
    companies: HashMap<String, usize>,
    yearly_years: (i32, i32),
    yearly_data: Vec<YearlyDataElement>, // length = yearly_years.1 - yearly_years.0
    daily_data: Vec<DailyDataElement>, // length = self.companies.len()
}

#[derive(Debug)]
pub struct LoaderOptions {
    pub yearly_min: i32,
    pub yearly_max: i32,
    pub daily_min: NaiveDate,
    pub daily_max: NaiveDate,
}

#[derive(Error, Debug)]
pub enum LoadError {
    #[error("Date bounds specified are not valid for the given data")]
    OutOfBoundDates()
}

impl<'a> FinancialStore where Self: 'a {
    pub fn yearly(&'a self, year: i32) -> Option<yearly::Financials<'a>> {
        if year < self.yearly_years.0 || year > self.yearly_years.1 {
            None
        } else {
            let year_idx = (year - self.yearly_years.0) as usize;

            Some(yearly::Financials {
                companies: &self.companies,
                report_dates: self.yearly_data[year_idx].report_dates.view(),
                data: self.yearly_data[year_idx].data.view(),
            })
        }
    }

    pub fn daily(&'a self, company: &str) -> Option<daily::Financials<'a>> {
        self.companies.get(company)
            .cloned()
            .map(|company_idx| daily::Financials {
                report_dates: self.daily_data[company_idx].report_dates.view(),
                data: self.daily_data[company_idx].data.view(),
            })
    }

    pub fn load(repr: StorageRepr, options: &LoaderOptions) -> FinancialStore {
        let no_of_companies = repr.companies.len();

        let mut store = FinancialStore {
            companies: repr.companies,
            yearly_years: (std::i32::MAX, std::i32::MIN),
            yearly_data: Vec::with_capacity((options.yearly_max - options.yearly_min) as usize), // might be smaller
            daily_data: Vec::with_capacity(no_of_companies),
        };

        for (year, data) in repr.yearly.into_iter() {
            if yearly < options.yearly_min || year < options.yearly_max { continue; }

            if year < store.yearly_years.0 { store.yearly_years.0 = year; }
            if year > store.yearly_years.1 { store.yearly_years.1 = year; }

            let report_dates = data.index_axis(Axis(0), 0)
                .map(|date_float| NaiveDate::from_num_days_from_ce(date_float.to_bits() as i32));

            store.yearly_data.push(YearlyDataElement {
                report_dates: report_dates,
                data: data.slice_move(s![1.., ..])
            });
        }
        store.yearly_data.shrink_to_fit();

        // for company_index in store.companies.values() {

        //     pub report_dates: Array1<NaiveDate>,
        //     pub data: Array2<f32>,

        //     for (&year, data) in repr.daily.iter() {
        //         store.daily_data.push(DailyDataElement {

        //         });
        //     }
        //     daily.get(&company_index).unwrap()
        // }

        store
    }

    pub async fn load_from_path(path: impl AsRef<Path>, options: &LoaderOptions) -> IoResult<FinancialStore> {
        unimplemented!()
    }
}

#[derive(Debug)]
pub struct StorageRepr {
    pub companies: HashMap<String, usize>,
    pub yearly: HashMap<i32, Array2<f32>>,
    pub daily: HashMap<i32, Array3<f32>>,
}

pub trait FetcherError = Error;

#[derive(Error, Debug)]
pub enum FetcherSaveError<T: FetcherError> {
    #[error("I/O error while saving: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Fetcher error while saving: {0}")]
    FetcherError(T),

    #[error("Encoding error while saving: {0}")]
    EncodingError(#[from] bincode::Error)
}

#[async_trait]
pub trait Fetcher {
    /// The error type returned if loading the financial data fails.
    type Error: FetcherError;

    /// Loads financials according to `options`.
    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::Error>;

    async fn save_to_path<P: AsRef<Path> + Send>(
        &mut self,
        path: P
    ) -> Result<(), FetcherSaveError<Self::Error>>
    {
        let path_ref = path.as_ref();
        let storage_repr = self.to_storage_repr().await.map_err(FetcherSaveError::FetcherError)?;

        // Create paths needed
        future::try_join(
            fs::create_dir_all(path_ref.join(YEARLY_FOLDER)),
            fs::create_dir_all(path_ref.join(DAILY_FOLDER))
        ).await?;

        let path_for = |year: i32, prefix: &str| path_ref.join(prefix).join(year.to_string());

        let yearly_files = storage_repr.yearly.iter()
            .map(|(&year, array)| (path_for(year, YEARLY_FOLDER), bincode::serialize(array)));

        let daily_files = storage_repr.daily.iter()
            .map(|(&year, array)| (path_for(year, DAILY_FOLDER), bincode::serialize(array)));

        let company_file = iter::once((path_ref.join(COMPANY_FILE), bincode::serialize(&storage_repr.companies)));

        future::try_join_all(yearly_files.chain(daily_files).chain(company_file)
            .map(|(path, data)| {
                fs::File::create(path)
                    .map_err(FetcherSaveError::IoError)
                    .and_then(async move |mut file| Ok(file.write_all(data?.as_ref()).await?))
            }))
            .await?;

        Ok(())
    }
}
