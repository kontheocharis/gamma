use std::collections::{HashMap, HashSet};
use std::convert::TryFrom;
use std::hash::Hash;
use std::iter::FromIterator;
use std::path::{Path, PathBuf};

use async_trait::async_trait;
use chrono::{Datelike, NaiveDate};
use enum_iterator::IntoEnumIterator;
use futures::prelude::*;
use itertools::izip;
use ndarray::{s, Array1, Array2, Array3, ArrayView1, ArrayViewMut1};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;
use tokio::fs::File;
use tokio::io::{AsyncBufRead, AsyncBufReadExt, BufReader};
use tokio::try_join;

use crate::fetching::{Fetch, StorageRepr};
use crate::financials::{DailyField, YearlyField};
use crate::util;

const BALANCE_SHEET_FILENAME: &str = "us-balance-annual.csv";
const CASH_FLOW_FILENAME: &str = "us-cashflow-annual.csv";
const INCOME_STATEMENT_FILENAME: &str = "us-income-annual.csv";
const SHARE_PRICES_FILENAME: &str = "us-shareprices-daily.csv";
const COMPANIES_FILENAME: &str = "us-companies.csv";

const READ_CAPACITY: usize = 1 << 15;
const CSV_SEP: char = ';';

const MIN_DAYS_AFTER_REPORT_SHARE_PRICE: usize = 1;
const MAX_DAYS_AFTER_REPORT_SHARE_PRICE: usize = 10;

pub trait FetcherRead = AsyncBufRead + Sync + Send + Unpin;

#[derive(Debug)]
pub struct Fetcher<R: FetcherRead> {
    balance_sheet: R,
    cash_flow: R,
    income_statement: R,
    share_prices: R,
    companies: R,
}

#[derive(Error, Debug)]
#[error("File not found: {0}")]
struct FileNotFoundError(PathBuf);

impl Fetcher<BufReader<File>> {
    pub async fn from_local(path: impl AsRef<Path>) -> anyhow::Result<Self> {
        let path_ref = path.as_ref();

        let read_file = async move |file_path: PathBuf| -> anyhow::Result<_> {
            if !file_path.exists() {
                Err(FileNotFoundError(file_path))?
            } else {
                Ok(BufReader::with_capacity(
                    READ_CAPACITY,
                    File::open(file_path).await?,
                ))
            }
        };

        let files = try_join!(
            read_file(path_ref.join(BALANCE_SHEET_FILENAME)),
            read_file(path_ref.join(CASH_FLOW_FILENAME)),
            read_file(path_ref.join(INCOME_STATEMENT_FILENAME)),
            read_file(path_ref.join(SHARE_PRICES_FILENAME)),
            read_file(path_ref.join(COMPANIES_FILENAME)),
        )?;

        Ok(Fetcher {
            balance_sheet: files.0,
            cash_flow: files.1,
            income_statement: files.2,
            share_prices: files.3,
            companies: files.4,
        })
    }
}

#[derive(Error, Debug)]
#[error("Simfin file parsing error in {0}: {1}")]
struct FileParsingError(String, String);

#[derive(Debug)]
struct ParseOptions<'a, F: Fields> {
    sheet_name: &'a str,
    columns: HashSet<F>, // returned columns will be ordered in the way they appear
    companies: &'a HashMap<String, usize>,
    entry_date_column: usize,
    classifying_year_column: usize,
    classifying_year_column_is_date: bool,
}

#[derive(Debug)]
struct ParseResult<F: Fields> {
    pub company_index: usize,
    pub entry_date: NaiveDate,
    pub classifying_year: i32,
    pub data: HashMap<F, f32>,
}

impl<R: FetcherRead> Fetcher<R> {
    async fn parse_company_csv(
        company_sheet: &mut R,
        sheet_name: &str,
    ) -> anyhow::Result<HashMap<String, usize>> {
        company_sheet
            .lines()
            .enumerate()
            .map(|(i, line)| {
                Ok((
                    line?
                        .split(CSV_SEP)
                        .nth(0)
                        .ok_or(FileParsingError(
                            sheet_name.to_string(),
                            "company column not found".to_string(),
                        ))?
                        .to_string(),
                    i,
                ))
            })
            .try_collect()
            .await
    }

    fn parse_sheet_csv<'a, F: Fields>(
        sheet: &'a mut R,
        options: &'a ParseOptions<'a, F>,
    ) -> impl TryStream<Ok = ParseResult<F>, Error = anyhow::Error> + 'a {
        sheet
            .lines()
            .skip(1) // We don't want the headers
            .filter_map(async move |line| -> Option<anyhow::Result<_>> {
                let mut company_index = None;
                let mut entry_date = None;
                let mut classifying_year = None;
                let mut data = HashMap::new(); // Vec::with_capacity(options.columns.len());

                for (i, element) in try_some!(line).split(CSV_SEP).enumerate() {
                    if i == 0 {
                        if element.contains("_old") {
                            return None;
                        } else {
                            if let Some(&index) = options.companies.get(element) {
                                company_index = Some(index);
                            } else {
                                log::info!(
                                    "skipping company {} in {} not present in company map",
                                    element,
                                    options.sheet_name,
                                );
                                return None;
                            }
                        }
                    }
                    if i == options.entry_date_column {
                        entry_date = Some(try_some!(NaiveDate::parse_from_str(element, "%F")));
                    }
                    if i == options.classifying_year_column {
                        classifying_year = Some(if options.classifying_year_column_is_date {
                            try_some!(NaiveDate::parse_from_str(element, "%F")).year()
                        } else {
                            try_some!(element.parse::<i32>().map_err(|_| {
                                FileParsingError(
                                    options.sheet_name.to_string(),
                                    format!("unable to parse into year: {}", element),
                                )
                            }))
                        });
                    }

                    if let Ok((true, field @ _)) =
                        F::try_from(i).map(|f| (options.columns.contains(&f), f))
                    {
                        if element.is_empty() {
                            data.insert(field, f32::NAN);
                        } else {
                            data.insert(
                                field,
                                try_some!(element.parse::<f32>().map_err(|_| {
                                    FileParsingError(
                                        options.sheet_name.to_string(),
                                        format!("unable to parse into float: {}", element),
                                    )
                                })),
                            );
                        }
                    }
                }

                Some(Ok(try_some!((|| {
                    Some(ParseResult {
                        company_index: company_index?,
                        entry_date: entry_date?,
                        classifying_year: classifying_year?,
                        data: data,
                    })
                })()
                .ok_or(FileParsingError(
                    options.sheet_name.to_string(),
                    "something went wrong, some indices could not be parsed".to_string(),
                )))))
            })
    }
}

trait Fields: Into<usize> + TryFrom<usize> + IntoEnumIterator + Eq + Hash {}

trait YearlyFields: Fields {
    fn to_yearly(
        self_data: &HashMap<Self, f32>,
        stock_data_after: ArrayView1<'_, f32>,
        out: ArrayViewMut1<'_, f32>,
    ) -> Option<()>;
}

trait DailyFields: Fields {
    fn to_daily(self_data: &HashMap<Self, f32>, out: ArrayViewMut1<'_, f32>) -> Option<()>;
}

#[repr(usize)]
#[derive(
    PartialEq, Eq, Hash, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone,
)]
enum BalanceSheetFields {
    CashCashEq = 9,
    Ppe = 13,
    TotalAssets = 17,
    ShortTermDebt = 19,
    LongTermDebt = 21,
    TotalLiabilities = 23,
    TotalEquity = 27,
}
impl Fields for BalanceSheetFields {}

impl YearlyFields for BalanceSheetFields {
    fn to_yearly(
        self_data: &HashMap<Self, f32>,
        stock_data_after: ArrayView1<'_, f32>,
        mut out: ArrayViewMut1<'_, f32>,
    ) -> Option<()> {
        out[YearlyField::CashShortTermInvestments as usize] = *self_data.get(&Self::CashCashEq)?;
        out[YearlyField::Ppe as usize] = *self_data.get(&Self::Ppe)?;
        out[YearlyField::TotalLiabilities as usize] = *self_data.get(&Self::TotalLiabilities)?;
        out[YearlyField::TotalAssets as usize] = *self_data.get(&Self::TotalAssets)?;
        out[YearlyField::TotalDebt as usize] =
            *self_data.get(&Self::ShortTermDebt)? + *self_data.get(&Self::LongTermDebt)?;
        out[YearlyField::TotalShareholdersEquity as usize] = *self_data.get(&Self::TotalEquity)?;

        out[YearlyField::SharePriceAtReport as usize] = *stock_data_after
            .iter()
            .enumerate()
            .skip(MIN_DAYS_AFTER_REPORT_SHARE_PRICE)
            .find(|(i, price)| !price.is_nan() && *i <= MAX_DAYS_AFTER_REPORT_SHARE_PRICE)
            .map(|(i, price)| price)
            .unwrap_or(&f32::NAN);

        Some(())
    }
}

#[repr(usize)]
#[derive(
    PartialEq, Eq, Hash, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone,
)]
enum IncomeStatementFields {
    Shares = 7,
}
impl Fields for IncomeStatementFields {}

impl YearlyFields for IncomeStatementFields {
    fn to_yearly(
        self_data: &HashMap<Self, f32>,
        _: ArrayView1<'_, f32>,
        mut out: ArrayViewMut1<'_, f32>,
    ) -> Option<()> {
        // TODO: what to do here?
        Some(())
    }
}

#[repr(usize)]
#[derive(
    PartialEq, Eq, Hash, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone,
)]
enum CashFlowFields {
    NetCash = 17,
}
impl Fields for CashFlowFields {}

impl YearlyFields for CashFlowFields {
    fn to_yearly(
        self_data: &HashMap<Self, f32>,
        _: ArrayView1<'_, f32>,
        mut out: ArrayViewMut1<'_, f32>,
    ) -> Option<()> {
        out[YearlyField::CashFlow as usize] = *self_data.get(&Self::NetCash)?;

        Some(())
    }
}

#[repr(usize)]
#[derive(
    PartialEq, Eq, Hash, IntoEnumIterator, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone,
)]
enum SharePriceFields {
    High = 5,
}
impl Fields for SharePriceFields {}

impl DailyFields for SharePriceFields {
    fn to_daily(self_data: &HashMap<Self, f32>, mut out: ArrayViewMut1<'_, f32>) -> Option<()> {
        out[DailyField::HighSharePrice as usize] = *self_data.get(&Self::High)?;

        Some(())
    }
}

#[async_trait]
impl<R: FetcherRead> Fetch for Fetcher<R> {
    type StorageReprError = anyhow::Error;

    async fn to_storage_repr(&mut self) -> anyhow::Result<StorageRepr> {
        let companies = Fetcher::parse_company_csv(&mut self.companies, COMPANIES_FILENAME).await?;

        let bs_opts = ParseOptions {
            sheet_name: BALANCE_SHEET_FILENAME,
            columns: HashSet::from_iter(BalanceSheetFields::into_enum_iter()),
            companies: &companies,
            entry_date_column: 6,       // "Publish Date"
            classifying_year_column: 3, // "Fiscal Year"
            classifying_year_column_is_date: false,
        };

        let bs_stream = Fetcher::parse_sheet_csv(&mut self.balance_sheet, &bs_opts);

        let cf_opts = ParseOptions {
            sheet_name: CASH_FLOW_FILENAME,
            columns: HashSet::from_iter(CashFlowFields::into_enum_iter()),
            companies: &companies,
            entry_date_column: 6,       // "Publish Date"
            classifying_year_column: 3, // "Fiscal Year"
            classifying_year_column_is_date: false,
        };

        let cf_stream = Fetcher::parse_sheet_csv(&mut self.cash_flow, &cf_opts);

        let is_opts = ParseOptions {
            sheet_name: INCOME_STATEMENT_FILENAME,
            columns: HashSet::from_iter(IncomeStatementFields::into_enum_iter()),
            companies: &companies,
            entry_date_column: 6,       // "Publish Date"
            classifying_year_column: 3, // "Fiscal Year"
            classifying_year_column_is_date: false,
        };

        let is_stream = Fetcher::parse_sheet_csv(&mut self.income_statement, &is_opts);

        let sp_opts = ParseOptions {
            sheet_name: SHARE_PRICES_FILENAME,
            columns: HashSet::from_iter(SharePriceFields::into_enum_iter()),
            companies: &companies,
            entry_date_column: 2,       // "Publish Date"
            classifying_year_column: 2, // "Fiscal Year"
            classifying_year_column_is_date: true,
        };

        let sp_stream = Fetcher::parse_sheet_csv(&mut self.share_prices, &sp_opts);

        let mut yearly_map: HashMap<i32, Array2<f32>> = HashMap::new();
        let mut daily_map: HashMap<i32, Array3<f32>> = HashMap::new();

        sp_stream
            .try_for_each(|parse_result| {
                let mut array = daily_map
                    .entry(parse_result.classifying_year)
                    .or_insert_with(|| {
                        Array3::from_elem(
                            (
                                NaiveDate::from_ymd(parse_result.classifying_year, 12, 31).ordinal()
                                    as usize,
                                DailyField::VARIANT_COUNT,
                                companies.len(),
                            ),
                            f32::NAN,
                        )
                    });

                future::ready(Ok(SharePriceFields::to_daily(
                    &parse_result.data,
                    array.slice_mut(s![
                        parse_result.entry_date.ordinal0() as usize,
                        ..,
                        parse_result.company_index
                    ]),
                )
                .expect("something went wrong while mapping to StorageRepr")))
            })
            .await?;

        async fn run_for_yearly<F: YearlyFields>(
            stream: impl TryStream<Ok = ParseResult<F>, Error = anyhow::Error>,
            yearly_map: &mut HashMap<i32, Array2<f32>>,
            daily_map: &HashMap<i32, Array3<f32>>,
            companies: &HashMap<String, usize>,
            sheet_name: &str,
        ) -> anyhow::Result<()> {
            stream
                .try_for_each(|parse_result| {
                    let mut yearly_array = yearly_map
                        .entry(parse_result.classifying_year)
                        .or_insert_with(|| {
                            Array2::from_elem(
                                (YearlyField::VARIANT_COUNT, companies.len()),
                                f32::NAN,
                            )
                        });

                    future::ready(
                        F::to_yearly(
                            &parse_result.data,
                            daily_map
                                .get(&parse_result.classifying_year)
                                .expect(&format!(
                                    "no daily data for year {}!",
                                    parse_result.classifying_year
                                ))
                                .slice(s![
                                    parse_result.entry_date.ordinal0() as usize..,
                                    DailyField::HighSharePrice as usize,
                                    parse_result.company_index
                                ]),
                            yearly_array.slice_mut(s![.., parse_result.company_index]),
                        )
                        .ok_or(
                            FileParsingError(
                                sheet_name.to_string(),
                                "error while mapping to StorageRepr".to_string(),
                            )
                            .into(),
                        ),
                    )
                })
                .await
        };

        // We could do this concurrently with a ConcurrentHashMap, but who cares? It's already so
        // fast.
        run_for_yearly(
            bs_stream,
            &mut yearly_map,
            &daily_map,
            &companies,
            BALANCE_SHEET_FILENAME,
        )
        .await?;
        run_for_yearly(
            cf_stream,
            &mut yearly_map,
            &daily_map,
            &companies,
            CASH_FLOW_FILENAME,
        )
        .await?;
        run_for_yearly(
            is_stream,
            &mut yearly_map,
            &daily_map,
            &companies,
            INCOME_STATEMENT_FILENAME,
        )
        .await?;

        Ok(StorageRepr {
            companies,
            yearly: yearly_map,
            daily: daily_map,
        })
    }
}
