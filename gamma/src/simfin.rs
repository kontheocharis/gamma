use std::collections::{HashMap, HashSet};
use std::convert::TryFrom;
use std::hash::Hash;
use std::iter::FromIterator;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};

use async_trait::async_trait;
use chrono::{Datelike, NaiveDate};
use enum_iterator::IntoEnumIterator;
use futures::prelude::*;
use itertools::izip;
use ndarray::{s, Array1, Array2, Array3, ArrayView1, ArrayViewMut1};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;
use tokio::fs::File;
use tokio::io::{self, AsyncBufRead, AsyncBufReadExt, BufReader};
use tokio::try_join;

use crate::fetching::{Fetch, StorageRepr};
use crate::financials::{Companies, DailyField, YearlyField};
use crate::util::IndexEnum;

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

        // We could do this concurrently with a ConcurrentHashMap, but who cares? It's already so
        // fast.
        run_for_daily(sp_stream, &mut daily_map, &companies, SHARE_PRICES_FILENAME).await?;

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

#[derive(Error, Debug)]
#[error("File not found: {0}")]
pub struct FileNotFoundError(PathBuf);

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
pub struct FileParsingError(String, String);

// Private

#[derive(Debug)]
struct ParseOptions<'a, F: Fields> {
    sheet_name: &'a str,
    columns: HashSet<F>, // returned columns will be ordered in the way they appear
    companies: &'a Companies,
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
    ) -> anyhow::Result<Companies> {
        let mut curr_i = AtomicUsize::new(0);

        let parse_line = |line: io::Result<String>| -> anyhow::Result<Option<_>> {
            let result = line?
                .split(CSV_SEP)
                .nth(0)
                .ok_or(FileParsingError(
                        sheet_name.to_string(),
                        "company column not found".to_string(),
                ))?
                .to_string();

            if result.contains("_old") {
                Ok(None)
            } else {
                let old_i = curr_i.fetch_add(1, Ordering::SeqCst);
                Ok(Some((result, old_i)))
            }
        };

        company_sheet
            .lines()
            .skip(1)
            .filter_map(async move |line| parse_line(line).transpose())
            .try_collect()
            .await
    }

    fn parse_sheet_csv<'a, F: Fields>(
        sheet: &'a mut R,
        options: &'a ParseOptions<'a, F>,
    ) -> impl Stream<Item = anyhow::Result<ParseResult<F>, anyhow::Error>> + 'a {
        let parse_line = move |line: io::Result<String>| -> anyhow::Result<Option<_>> {
            let mut company_index = None;
            let mut entry_date = None;
            let mut classifying_year = None;
            let mut data = HashMap::new(); // Vec::with_capacity(options.columns.len());

            for (i, element) in line?.split(CSV_SEP).enumerate() {
                if i == 0 {
                    if let Some(&index) = options.companies.get(element) {
                        company_index = Some(index);
                    } else {
                        // Skip if not present
                        return Ok(None);
                    }
                }
                if i == options.entry_date_column {
                    entry_date = Some(NaiveDate::parse_from_str(element, "%F")?);
                }
                if i == options.classifying_year_column {
                    classifying_year = Some(if options.classifying_year_column_is_date {
                        NaiveDate::parse_from_str(element, "%F")?.year()
                    } else {
                        element.parse::<i32>().map_err(|_| {
                            FileParsingError(
                                options.sheet_name.to_string(),
                                format!("unable to parse into year: {}", element),
                            )
                        })?
                    });
                }

                if let Ok((true, field @ _)) =
                    F::try_from(i).map(|f| (options.columns.contains(&f), f))
                {
                    if element.is_empty() {
                        data.insert(field, f32::NAN);
                    } else {
                        let parsed_float = element.parse::<f32>().map_err(|_| {
                            FileParsingError(
                                options.sheet_name.to_string(),
                                format!("unable to parse into float: {}", element),
                            )
                        })?;

                        data.insert(field, parsed_float);
                    }
                }
            }

            if company_index.is_none() || entry_date.is_none() || classifying_year.is_none() {
                Err(FileParsingError(
                    options.sheet_name.to_string(),
                    "something went wrong, some indices could not be parsed".to_string(),
                ))?
            } else {
                Ok(Some(ParseResult {
                    company_index: company_index.unwrap(),
                    entry_date: entry_date.unwrap(),
                    classifying_year: classifying_year.unwrap(),
                    data: data,
                }))
            }
        };

        sheet
            .lines()
            .skip(1) // We don't want the headers
            .filter_map(async move |line| parse_line(line).transpose())
    }
}

async fn run_for_yearly<F: YearlyFields>(
    stream: impl Stream<Item = anyhow::Result<ParseResult<F>>>,
    yearly_map: &mut HashMap<i32, Array2<f32>>,
    daily_map: &HashMap<i32, Array3<f32>>,
    companies: &Companies,
    sheet_name: &str,
) -> anyhow::Result<()> {
    stream
        .try_for_each(|parse_result| {
            let mut yearly_array = yearly_map
                .entry(parse_result.classifying_year)
                .or_insert_with(|| {
                    Array2::from_elem((YearlyField::VARIANT_COUNT, companies.len()), f32::NAN)
                });

            let result = F::to_yearly(
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
            );

            future::ready(result)
        })
        .await
}

async fn run_for_daily<F: DailyFields>(
    stream: impl Stream<Item = anyhow::Result<ParseResult<F>>>,
    daily_map: &mut HashMap<i32, Array3<f32>>,
    companies: &Companies,
    sheet_name: &str,
) -> anyhow::Result<()> {
    stream
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

            let result = F::to_daily(
                &parse_result.data,
                array.slice_mut(s![
                    parse_result.entry_date.ordinal0() as usize,
                    ..,
                    parse_result.company_index
                ]),
            )
            .ok_or(
                FileParsingError(
                    sheet_name.to_string(),
                    "error while mapping to StorageRepr".to_string(),
                )
                .into(),
            );

            future::ready(result)
        })
        .await
}

trait Fields: IndexEnum + Hash {}

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

macro_rules! impl_yearly {
    ($($t:ty => $body:expr)*) => {
        $(
            impl YearlyFields for $t {
                fn to_yearly(
                    self_data: &HashMap<Self, f32>,
                    stock_data_after: ArrayView1<'_, f32>,
                    mut out: ArrayViewMut1<'_, f32>,
                ) -> Option<()> {
                    macro_rules! yearly_financial {
                        ($field: ident) => {
                            out[YearlyField::$field as usize]
                        };
                    }

                    macro_rules! data {
                        ($field: ident) => {
                            *self_data.get(&Self::$field)?
                        };
                    }

                    // ew macro hygiene sucks sometimes...
                    macro_rules! stock_data_after {
                        () => {
                            stock_data_after
                        };
                    }

                    Some($body)
                }
            }
        )*
    }
}

macro_rules! impl_daily {
    ($($t:ty => $body:expr)*) => {
        $(
            impl DailyFields for $t {
                fn to_daily(self_data: &HashMap<Self, f32>, mut out: ArrayViewMut1<'_, f32>) -> Option<()> {
                    macro_rules! daily_financial {
                        ($field: ident) => {
                            out[DailyField::$field as usize]
                        };
                    }

                    macro_rules! data {
                        ($field: ident) => {
                            *self_data.get(&Self::$field)?
                        };
                    }

                    Some($body)
                }
            }
        )*
    }
}

macro_rules! derive_fields {
    ($(enum $t:ident $body:tt)*) => {
        $(
            #[repr(usize)]
            #[derive(
                PartialEq,
                Eq,
                Hash,
                IntoEnumIterator,
                Debug,
                IntoPrimitive,
                TryFromPrimitive,
                Copy,
                Clone,
            )]
            enum $t $body
            impl Fields for $t {}
        )*
    };
}

derive_fields! {
    enum BalanceSheetFields {
        CashCashEq = 9,
        Ppe = 13,
        TotalAssets = 17,
        ShortTermDebt = 19,
        LongTermDebt = 21,
        TotalLiabilities = 23,
        TotalEquity = 27,
    }

    enum IncomeStatementFields {
        Shares = 8,
        NetIncome = 25,
    }

    enum CashFlowFields {
        NetCash = 17,
    }

    enum SharePriceFields {
        High = 5,
    }
}

impl_yearly! {
    BalanceSheetFields => {
        yearly_financial!(CashShortTermInvestments) = data!(CashCashEq);

        yearly_financial!(Ppe) = data!(Ppe);

        yearly_financial!(TotalLiabilities) = data!(TotalLiabilities);

        yearly_financial!(TotalAssets) = data!(TotalAssets);

        yearly_financial!(TotalDebt) = data!(ShortTermDebt) + data!(LongTermDebt);

        yearly_financial!(TotalShareholdersEquity) = data!(TotalEquity);

        yearly_financial!(SharePriceAtReport) = *stock_data_after!()
            .iter()
            .enumerate()
            .skip(MIN_DAYS_AFTER_REPORT_SHARE_PRICE)
            .find(|(i, price)| !price.is_nan() && *i <= MAX_DAYS_AFTER_REPORT_SHARE_PRICE)
            .map(|(i, price)| price)
            .unwrap_or(&f32::NAN);
    }

    IncomeStatementFields => {
        yearly_financial!(TotalOutstandingShares) = data!(Shares);
        yearly_financial!(Eps) = (data!(NetIncome) * 0.90) / data!(Shares);
    }

    CashFlowFields => {
        yearly_financial!(CashFlow) = data!(NetCash);
    }
}

impl_daily! {
    SharePriceFields => {
        daily_financial!(HighSharePrice) = data!(High);
    }
}
