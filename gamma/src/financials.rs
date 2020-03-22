use std::collections::{HashMap};
use std::error::{Error};
use std::fmt;
use std::fs::{File};
use std::io;
use std::path::{Path};

use async_trait::async_trait;
use bincode::{serialize_into, deserialize_from, Error as BincodeError};
use chrono::{NaiveDate, Duration};
use ndarray::{Array2, ArrayView1};
use ndarray_npy::{ReadNpyExt, WriteNpyExt, ReadNpyError, WriteNpyError};
use num_enum::{IntoPrimitive, TryFromPrimitive};

use crate::traits::{CountVariants};


const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";


/// Defines all the different types of financial "fields" that the `Financials` struct can hold.
///
/// Convertible to and from `usize` for indexing into `Financials`.
#[repr(usize)]
#[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive)]
pub enum Field {
    CashShortTermInvestments,
    Ppe,
    TotalLiabilities,
    TotalAssets,
    TotalDebt,
    TotalShareholdersEquity,
    TotalOutstandingShares,
    Eps,
    SharePrice,
    CashFlowsPositive,
}


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


/// Holds all the financial data that is used in analysis.
///
/// Provides a strongly-typed way to interface with the different types of financial data described
/// in the `Field` enum.
///
/// Also, it provides a way to save to and load from disk through the `load` and `save` methods.
#[derive(Debug)]
pub struct Financials {
    data: Array2<f32>,
    companies: HashMap<String, usize>,
}

impl<'a> Financials where Self: 'a {

    /// Constructs an empty `Financials` instance, mainly used for testing.
    pub fn empty(no_of_companies: usize) -> Financials {
        Financials { 
            data: Array2::zeros((Field::count_variants(), no_of_companies)),
            companies: HashMap::new(),
        }
    }

    /// Constructs a `Financials` instance from an `ndarray::Array2` holding financial data
    /// and a `HashMap<String, usize>` that maps company symbols to column indices of `data`.
    ///
    /// The `data` array's columns are indexed by company, and its rows are indexed by financial
    /// fields (i.e. the variants of `Field`).
    pub fn from_raw_parts(data: Array2<f32>, companies: HashMap<String, usize>) -> Financials {
        Financials { data: data, companies: companies }
    }

    /// Loads a `Financials` instance from folder `directory`, where it was previously saved
    /// through the `save` method.
    ///
    /// If `directory` does not exist, `Err(IoError::NotADirectory)` is returned.
    pub fn load(directory: impl AsRef<Path>) -> IoResult<Financials> {
        let directory_path = directory.as_ref();
        if !directory_path.is_dir() {
            return Err(IoError::NotADirectory(directory_path.into()));
        }

        Ok(Financials {
            data: Array2::read_npy(File::open(directory_path.join(NPY_SAVE_FILE))?)?,
            companies: bincode::deserialize_from(File::open(directory_path.join(HASHMAP_SAVE_FILE))?)?
        })
    }

    /// Saves a `Financials` instance in folder `directory`. 
    ///
    /// If `directory` does not exist, `Err(IoError::NotADirectory)` is returned.
    pub fn save(&self, directory: impl AsRef<Path>) -> IoResult<()> {
        let directory_path = directory.as_ref();
        if !directory_path.is_dir() {
            return Err(IoError::NotADirectory(directory_path.into()));
        }

        // Write the numpy file
        self.data.write_npy(File::create(directory_path.join(NPY_SAVE_FILE))?)?;

        // Write the hashmap
        bincode::serialize_into(File::create(directory_path.join(HASHMAP_SAVE_FILE))?, &self.companies)?;

        Ok(())
    }

    /// Selects data of type `field` and returns it as an `ndarray::ArrayView1`, where
    /// each element corresponds to a different company.
    pub fn field(&'a self, field: Field) -> ArrayView1<'a, f32> {
        self.data.row(field as usize)
    }

    /// Selects data for `company` and returns it as an `ndarray::ArrayView1`, where each element
    /// corresponds to a different `Field`.
    pub fn for_company(&'a self, company: &str) -> Option<ArrayView1<'a, f32>> {
        self.companies.get(company).map(|&index| self.data.column(index))
    }

}


/// Options to be passed to `Fetcher`
pub struct FetcherOptions {
    /// Fetch financials closest to this date. (Never *after* it, though.)
    pub date: NaiveDate,

    /// The amount of time before `date` for which cash flows need to be positive in order
    /// for `Field::CashFlowsPositive` to be `1.0`.
    pub cash_flows_back: Duration,
}


/// A trait that can be implemented in order to allow loading `Financials` from any arbitrary data
/// source.
#[async_trait]
pub trait Fetcher {
    /// The error type returned if fetching the financial data fails.
    type FetchError: Error;

    /// Fetches financials according to `options`.
    async fn fetch(&self, options: &FetcherOptions) -> Result<Financials, Self::FetchError>;
}
