use std::collections::{HashMap};
use std::fmt;
use std::error::{Error};
use std::path::{Path, PathBuf};
use std::marker::{Sync, Send, Unpin};

use log::{debug, error, info, trace, warn};
use async_trait::async_trait;
use chrono::{NaiveDate, Duration};
use futures::future::TryFutureExt;
use futures::prelude::*;
use ndarray::{Array2};
use tokio::io::{BufReader, AsyncBufRead, AsyncBufReadExt};
use tokio::fs::{File};

use crate::financials::{self, Financials};
use crate::traits::{CountVariants};


const BALANCE_SHEET_FILENAME:    &str = "us-balance-annual.csv";
const CASH_FLOW_FILENAME:        &str = "us-cashflow-annual.csv";
const INCOME_STATEMENT_FILENAME: &str = "us-income-annual.csv";
const SHARE_PRICES_FILENAME:     &str = "us-shareprices-daily.csv";

const READ_CAPACITY: usize = 1 << 15;

#[derive(Debug)]
pub enum FromLocalError {
    IoError(std::io::Error),
    FileNotFound(PathBuf),
}

impl_from!(FromLocalError {
    IoError => { std::io::Error }
});

impl fmt::Display for FromLocalError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::IoError(ref error) => write!(f, "{}", error),
            Self::FileNotFound(ref file) => {
                write!(f, "The following file was not found: {}", file.display())?;
                write!(
                    f, "Files need to be named: {}, {}, {}, {}",
                    BALANCE_SHEET_FILENAME, CASH_FLOW_FILENAME,
                    INCOME_STATEMENT_FILENAME, SHARE_PRICES_FILENAME
                )
            },
        }
    }
}

impl Error for FromLocalError {}


pub trait LoaderRead = AsyncBufRead + Sync + Send + Unpin;

#[derive(Debug)]
pub struct Loader<R: LoaderRead> {
    balance_sheet: R,
    cash_flow: R,
    income_statement: R,
    share_prices: R,
}

impl Loader<BufReader<File>> {
    pub async fn from_local(path: impl AsRef<Path>) -> Result<Loader<BufReader<File>>, FromLocalError> {
        let path_ref = path.as_ref();

        let read_file = async move |file_path: PathBuf| -> Result<BufReader<File>, FromLocalError> {
            if !file_path.exists() {
                return Err(FromLocalError::FileNotFound(file_path));
            }

            Ok(BufReader::with_capacity(READ_CAPACITY, File::open(file_path).await?))
        };

        let files = future::try_join4(
            read_file(path_ref.join(BALANCE_SHEET_FILENAME)),
            read_file(path_ref.join(CASH_FLOW_FILENAME)),
            read_file(path_ref.join(INCOME_STATEMENT_FILENAME)),
            read_file(path_ref.join(SHARE_PRICES_FILENAME)),
        ).await?;

        Ok(Loader {
            balance_sheet:    files.0,
            cash_flow:        files.1,
            income_statement: files.2,
            share_prices:     files.3,
        })
    }
}


#[derive(Debug)]
pub enum LoadError {
    IoError(std::io::Error),
    FileParsingError(String),
    DateParsingError(chrono::format::ParseError),
}

impl_from!(LoadError {
    IoError => { std::io::Error },
    DateParsingError => { chrono::format::ParseError }
});

impl fmt::Display for LoadError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::IoError(ref error) => write!(f, "{}", error),
            Self::FileParsingError(ref msg) => write!(f, "{}", msg),
            Self::DateParsingError(ref error) => write!(f, "{}", error),
        }
    }
}

impl Error for LoadError {}


#[derive(Debug)]
struct LoaderProgress {
    pub best_date: NaiveDate,
    pub best_entry: Vec<String>
}


async fn parse_csv<R: LoaderRead>(
    options: &financials::LoaderOptions,
    reader: &mut R,
    date_column: &str,
    sheet: &str
) -> Result<(HashMap<String, usize>, HashMap<String, LoaderProgress>), LoadError> 
{
    info!("Starting: {}", sheet);

    let mut headers: HashMap<String, usize> = HashMap::new();
    let mut progress_map: HashMap<String, LoaderProgress> = HashMap::new();

    let sep = ';';

    let mut it = reader.lines().enumerate();
    while let Some((i, maybe_line)) = it.next().await {
        // Return if there's an error matching a line
        let line = maybe_line?;

        // Parse headers
        if i == 0 {
            line.split(sep)
                .map(|c| c.trim_matches('\"')) // Remove quotes
                .enumerate()
                .for_each(|(i, header)| { headers.insert(header.to_string(), i); });
            continue;
        }

        let entry: Vec<&str> = line.split(sep).collect();

        let get_col = |header: &str| -> Result<&str, LoadError> { 
            entry.get(*headers.get(header).unwrap())
                .cloned()
                .ok_or(LoadError::FileParsingError(format!("column {} not found", header)))
                // If we don't find the column, there's a problem.
        };

        let company = get_col("Ticker")?;

        let progress = progress_map.entry(company.to_string()).or_insert_with(|| LoaderProgress {
            best_date: chrono::naive::MIN_DATE,
            best_entry: Vec::new()
        });

        let curr_date = NaiveDate::parse_from_str(get_col(date_column)?, "%F")?;

        if curr_date > options.date || curr_date < progress.best_date {
            continue;
        }

        progress.best_date = curr_date;
        progress.best_entry = entry.into_iter().map(String::from).collect();
    }

    info!("Done: {}", sheet);
    Ok((headers, progress_map))
}


#[async_trait]
impl<R: LoaderRead> financials::Loader for Loader<R> {
    type LoadError = LoadError;

    async fn load(&mut self, options: &financials::LoaderOptions) -> Result<Financials, LoadError> {

        let result = future::try_join4(
            parse_csv(options, &mut self.balance_sheet,    "Publish Date", "balance sheet"),
            parse_csv(options, &mut self.cash_flow,        "Publish Date", "cash flow"),
            parse_csv(options, &mut self.income_statement, "Publish Date", "income statement"),
            parse_csv(options, &mut self.share_prices,     "Date",         "share prices"),
        ).await?;

        println!("{:#?}", ((result.0).1).len());
        println!("{:#?}", ((result.1).1).len());
        println!("{:#?}", ((result.2).1).len());
        println!("{:#?}", ((result.3).1).len());

        Ok(Financials::empty(10))
    }
}
