use std::collections::{HashMap};
use std::error::{Error};
use std::fmt;
use std::fs::{File};
use std::io;
use std::path::{Path};
use std::mem::{Rc};

use async_trait::async_trait;
use bincode::{serialize_into, deserialize_from, Error as BincodeError};
use chrono::{NaiveDate, Duration};
use ndarray::{Array3, ArrayView2, Axis, Ix1};
use ndarray_npy::{ReadNpyExt, WriteNpyExt, ReadNpyError, WriteNpyError};
use num_enum::{IntoPrimitive, TryFromPrimitive};

use crate::traits::{CountVariants};


const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";


/// Error returned by I/O methods on `Financials` (i.e. `save` and `load`).
#[derive(Debug)]
pub enum IoError {
    NotADirectory(Box<Path>),
    Internal(Box<dyn Error>),
}

impl fmt::Display for IoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotADirectory(ref path) => write!(f, "{} is an invalid/nonexistent directory.", path.display()),
            Self::Internal(ref error) => write!(f, "{}", error)
        }
    }
}

impl Error for IoError { }

impl_from!(IoError {
    Internal => { BincodeError, io::Error, ReadNpyError, WriteNpyError }
});

type IoResult<T> = Result<T, IoError>;

pub mod yearly {

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
        pub(parent) companies: &'a HashMap<String, usize>,
        pub(parent) report_dates: ArrayView1<'a, NaiveDate>,
        pub(parent) data: ArrayView2<'a, f32>,
    }

    impl<'a> Financials<'a> {
        pub fn field(&'a self, field: Field) -> FieldView<'a> {
            self.data[field.into()]
        }

        pub fn fields(&'a self) -> impl Iterator<Item=(Field, FieldView<'a>)> {
            self.data.outer_iter()
                .enumerate()
                .map(|(i, data)| (Field::try_from(i).unwrap(), data))
        }

        pub fn row(&'a self, company: &str) -> Option<RowView<'a>> {
            self.companies.get(company)
                .map(|index| (self.report_dates.index_axis(Axis(0), index), self.data.index_axis(Axis(1), index)))
        }
    }

    type FieldView<'a> = ArrayView1<'a, f32>;
    type RowView<'a> = (NaiveDate, ArrayView1<'a, f32>);
}

pub mod daily {

    #[repr(usize)]
    #[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
    pub enum Field {
        HighSharePrice,
        LowSharePrice,
        Volume,
    }

    pub struct Financials<'a> {
        pub(parent) report_dates: ArrayView1<'a, NaiveDate>,
        pub(parent) data: ArrayView2<'a, f32>,
    }

    impl<'a> Financials<'a> {
        pub fn field(&'a self, field: Field) -> FieldView<'a> {
            (self.report_dates.reborrow(), self.data.index_axis(Axis(0), field.into()))
        }
    }

    type FieldView<'a> = (ArrayView1<'a, NaiveDate>, ArrayView1<'a, f32>);
}


struct YearlyDataElement {
    pub report_dates: Array1<NaiveDate>,
    pub data: Array2<f32>,
}

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
}


// TODO: Implement validation.
/// Options to be passed to `Loader`
pub struct LoaderOptions {
    /// Load financials closest to this date. (Never *after* it, though.)
    pub date: NaiveDate,

    /// The amount of time before `date` for which cash flows need to be positive in order
    /// for `Field::CashFlowsPositive` to be `1.0`.
    pub cash_flows_back: Duration,
}


/// A trait that can be implemented in order to allow loading `Financials` from any arbitrary data
/// source.
#[async_trait]
pub trait Loader {
    /// The error type returned if loading the financial data fails.
    type LoadError: Error;

    /// Loads financials according to `options`.
    async fn load(&mut self, options: &LoaderOptions) -> Result<Financials, Self::LoadError>;
}
