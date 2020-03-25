use std::collections::{HashMap};
use std::fmt;
use std::error::{Error};
use std::path::{Path, PathBuf};
use std::marker::{Sync, Send, Unpin};

use log::{debug, error, info, trace, warn};
use async_trait::async_trait;
use chrono::{NaiveDate, Duration, Datelike};
use futures::future::TryFutureExt;
use futures::prelude::*;
use ndarray::{Array2};
use tokio::io::{BufReader, AsyncBufRead, AsyncBufReadExt};
use tokio::fs::{File};
use thiserror::{Error};

use crate::financials::{self};
use crate::traits::{CountVariants};


const BALANCE_SHEET_FILENAME:    &str = "us-balance-annual.csv";
const CASH_FLOW_FILENAME:        &str = "us-cashflow-annual.csv";
const INCOME_STATEMENT_FILENAME: &str = "us-income-annual.csv";
const SHARE_PRICES_FILENAME:     &str = "us-shareprices-daily.csv";

const READ_CAPACITY: usize = 1 << 15;

#[derive(Error, Debug)]
pub enum FromLocalError {
    #[error("I/O Error: {0}")]
    IoError(#[from] std::io::Error),

    #[error(
        "Files need to be named: {}, {}, {}, {}",
        BALANCE_SHEET_FILENAME, CASH_FLOW_FILENAME,
        INCOME_STATEMENT_FILENAME, SHARE_PRICES_FILENAME
    )]
    FileNotFound(PathBuf),
}

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

        let read_file = async move |file_path: PathBuf| {
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


#[derive(Error, Debug)]
pub enum LoadError {
    #[error("I/O Error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("File parsing error: {0}")]
    FileParsingError(String),

    #[error("Date parsing error: {0}")]
    DateParsingError(#[from] chrono::format::ParseError),
}

struct ParsedData {
    pub companies: HashMap<String, usize>,
    pub rows: HashMap<String, Vec<(NaiveDate, Vec<f32>)>>,
    pub min_year: u32,
    pub max_year: u32,
}

async fn parse_csv<R: LoaderRead>(
    reader: &mut R,
    fields_to_retain: &[&str],
) -> Result<ParsedData, LoadError> 
{
    let mut parsed = ParsedData {
        companies: HashMap::new(),
        rows: HashMap::new(),
        min_year: std::u32::MAX,
        max_year: std::u32::MIN,
    };

    let mut headers: HashMap<String, usize> = HashMap::new();

    const SEP: char = ';';

    let mut it = reader.lines().enumerate();
    let mut curr_company_index = 0;
    while let Some((i, maybe_line)) = it.next().await {
        // Return if there's an error matching a line
        let line = maybe_line?;

        // Parse headers
        if i == 0 {
            line.split(SEP)
                .map(|c| c.trim_matches('\"')) // Remove quotes
                .enumerate()
                .for_each(|(i, header)| { headers.insert(header.to_string(), i); });
            continue;
        }

        let curr_row: Vec<&str> = line.split(SEP).collect();

        let get_col = |header: &str| -> Result<&str, LoadError> { 
            curr_row.get(*headers.get(header).unwrap())
                .cloned()
                .ok_or(LoadError::FileParsingError(format!("column {} not found", header)))
                // If we don't find the column, there's a problem with the data.
        };

        let company = get_col("Ticker")?;
        parsed.companies.entry(company.to_string())
            .or_insert_with(|| { curr_company_index += 1; curr_company_index - 1 }); 
            // ew why can rust not have curr_company_index++

        let curr_date = NaiveDate::parse_from_str(
            get_col("Publish Date").or(get_col("Date"))?, "%F"
        )?;

        let fiscal_year = get_col("Fiscal Year")
            .map(str::parse::<u32>)
            .unwrap_or(Ok(curr_date.year() as u32))
            .or(Err(LoadError::FileParsingError(format!("could not parse year as u32 at row {}", i))))?;

        if fiscal_year < parsed.min_year { parsed.min_year = fiscal_year; }
        if fiscal_year > parsed.max_year { parsed.max_year = fiscal_year; }

        let mut company_rows = parsed.rows.entry(company.to_string())
            .or_insert_with(|| Vec::new()); 

        let rows = fields_to_retain.iter()
            .map(|field| -> Result<f32, LoadError> {
                str::parse::<f32>(
                    get_col(field)?
                ).or(Err(LoadError::FileParsingError(format!("could not parse col {} at row {}", field, i))))
            })
            .collect::<Result<Vec<_>, _>>()?;

        company_rows.push((curr_date, rows))
    }

    Ok(parsed)
}


#[async_trait]
impl<R: LoaderRead> financials::Fetcher for Loader<R> {
    type Error = LoadError;

    async fn to_storage_repr(&mut self) -> Result<financials::StorageRepr, Self::Error> {

        const BS_FIELDS: &[&str] = &[
            "Cash, Cash Equivalents & Short Term Investments",
            "Property, Plant & Equipment, Net",
            "Total Assets",
            "Total Liabilities",
            "Total Equity",
            "Long Term Debt",
        ];

        const IS_FIELDS: &[&str] = &[
            "Shares (Basic)", // Is this right?
            // "EPS", // Not there?
        ];

        const CF_FIELDS: &[&str] = &[
            "Net Cash from Operating Activities", // Is this right?
        ];

        const SP_FIELDS: &[&str] = &[
            "High",
        ];

        let (
            mut balance_sheet_data,
            mut cash_flow_data,
            mut income_statement_data,
            mut share_prices_data
        ) = {
            future::try_join4(
                parse_csv(&mut self.balance_sheet,    BS_FIELDS),
                parse_csv(&mut self.cash_flow,        CF_FIELDS),
                parse_csv(&mut self.income_statement, IS_FIELDS),
                parse_csv(&mut self.share_prices,     SP_FIELDS),
            ).await?
        };

        let storage_repr = financials::StorageRepr {
            companies: balance_sheet_data.companies, //FIXME: we are calculating the hashmap 3 times!
            yearly: HashMap::new(),
            daily: HashMap::new(),
        };

        // TODO

        unimplemented!()
    }
}
