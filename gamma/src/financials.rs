use std::error::{Error};
use std::fmt;
use std::io;
use std::path::{Path};
use std::collections::{HashMap};

use async_trait::async_trait;
use futures::prelude::*;
use bincode::{serialize_into, deserialize_from, Error as BincodeError};
use chrono::{NaiveDate, Duration};
use ndarray::{Array3, Array2, Array1, ArrayView2, ArrayView1, Axis, Ix1};
use ndarray_npy::{ReadNpyExt, WriteNpyExt, ReadNpyError, WriteNpyError};
use thiserror::{Error};

use crate::traits::{CountVariants};

const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";

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
    use ndarray::{Array3, Array2, ArrayView2, ArrayView1, Axis, Ix1};
    use chrono::{NaiveDate, Duration};

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
    use ndarray::{Array3, Array2, ArrayView2, ArrayView1, Axis, Ix1};
    use chrono::{NaiveDate, Duration};
    use std::collections::{HashMap};

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
        pub fn field(&'a self, field: Field) -> FieldView<'a> {
            (self.report_dates.reborrow(), self.data.index_axis(Axis(0), field.into()))
        }
    }

    type FieldView<'a> = (ArrayView1<'a, NaiveDate>, ArrayView1<'a, f32>);
}

#[derive(Debug)]
struct YearlyDataElement {
    pub report_dates: Array1<NaiveDate>,
    pub data: Array2<f32>,
}

#[derive(Debug)]
struct DailyDataElement {
    pub report_dates: Array1<NaiveDate>,
    pub data: Array2<f32>,
}

#[derive(Debug)]
pub struct FinancialStore {
    companies: HashMap<String, usize>,
    yearly_years: (u32, u32),
    yearly_data: Array1<YearlyDataElement>,
    daily_data: Array1<DailyDataElement>,
}

#[derive(Debug)]
pub struct LoaderOptions {
    /// Load financials closest to this date. (Never *after* it, though.)
    pub date: NaiveDate,
}

impl<'a> FinancialStore where Self: 'a {
    pub fn yearly(&'a self, year: u32) -> Option<yearly::Financials<'a>> {
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

    pub fn load(storage: FinancialsStorageRepr, options: &LoaderOptions) -> FinancialStore {
        unimplemented!()
    }

    pub async fn load_from_path(path: impl AsRef<Path>, options: &LoaderOptions) -> IoResult<FinancialStore> {
        unimplemented!()
    }
}

#[derive(Debug)]
pub struct FinancialsStorageRepr {
    companies: HashMap<String, usize>,
    yearly: HashMap<u32, Array2<f32>>,
    daily: HashMap<u32, Array3<f32>>,
}

pub trait FetcherError = Error;

#[derive(Error, Debug)]
pub enum FetcherSaveError<T: FetcherError> {
    #[error("I/O error while saving: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Fetcher error while saving: {0}")]
    FetcherError(T),
}

#[async_trait]
pub trait Fetcher {
    /// The error type returned if loading the financial data fails.
    type Error: FetcherError;

    /// Loads financials according to `options`.
    async fn to_storage_repr(&mut self) -> Result<FinancialsStorageRepr, Self::Error>;

    async fn save_to_path<P: AsRef<Path> + Send>(
        &mut self,
        path: P
    ) -> Result<(), FetcherSaveError<Self::Error>>
    {
        let path_ref = path.as_ref();
        let storage_repr = self.to_storage_repr().await.map_err(FetcherSaveError::FetcherError)?;

        create_if_nonexistent(path_ref).await?;
        create_if_nonexistent(path_ref.join("yearly")).await?;
        create_if_nonexistent(path_ref.join("daily")).await?;

        let year_to_path = |year: u32, prefix: &str| path_ref.join(prefix).join(year.to_string());

        let yearly_iterator = storage_repr.yearly.keys().map(|&year| year_to_path(year, "yearly"));
        let daily_iterator = storage_repr.yearly.keys().map(|&year| year_to_path(year, "daily"));

        future::try_join_all(yearly_iterator.chain(daily_iterator).map(create_if_nonexistent)).await?;

        // TODO

        Ok(())
    }
}

async fn create_if_nonexistent<P: AsRef<Path>>(path: P) -> Result<(), std::io::Error> {
    let path_ref = path.as_ref();
    if !path_ref.exists() {
        tokio::fs::create_dir(path_ref).await
    } else {
        Ok(())
    }
}
