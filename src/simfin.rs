use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::convert::{TryFrom, TryInto};
use std::hash::Hash;
use std::iter::FromIterator;
use std::path::{Path, PathBuf};

use async_trait::async_trait;
use chrono::{Datelike, NaiveDate};
use enum_iterator::IntoEnumIterator;
use futures::prelude::*;
use ndarray::prelude::*;
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;
use tokio::fs::File;
use tokio::io::{AsyncBufRead, AsyncBufReadExt, BufReader};
use tokio::try_join;

use crate::fetching::{DailyMap, Fetch, StorageRepr, YearlyMap};
use crate::financials::{Companies, DailyField, YearlyField};
use crate::util::{IndexEnum, CompanyId};

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
pub struct Fetcher<R> {
    balance_sheet: R,
    cash_flow: R,
    income_statement: R,
    share_prices: R,
    companies: R,
}

#[async_trait(?Send)]
impl<R: FetcherRead> Fetch for Fetcher<R> {
    type StorageReprError = anyhow::Error;

    async fn to_storage_repr(&mut self) -> anyhow::Result<StorageRepr> {
        let companies = Fetcher::parse_company_csv(&mut self.companies, COMPANIES_FILENAME).await?;

        let yearly_map = RefCell::new(YearlyMap::new());
        let daily_map = RefCell::new(DailyMap::new());

        macro_rules! parse_csv {
            (
                frequency: $frequency:tt,
                reader: $r:expr,
                sheet_name: $sheet_name:expr,
                fields: $fields:ident,
                entry_date: $entry_date_column:expr,
                classifying_year: $classifying_year_column:expr,
                classifying_year_is_date: $classifying_year_column_is_date:expr,
            ) => {{
                let opts = ParseOptions {
                    sheet_name: $sheet_name,
                    columns: HashSet::from_iter($fields::into_enum_iter()),
                    companies: &companies,
                    entry_date_column: $entry_date_column, // "Publish Date"
                    classifying_year_column: $classifying_year_column, // "Fiscal Year"
                    classifying_year_column_is_date: $classifying_year_column_is_date,
                };

                Fetcher::parse_sheet_csv(&mut $r, opts, |result| {
                    parse_csv!(@ $frequency, $sheet_name, result)
                })
            }};
            (@ "daily", $sheet_name:expr, $result:expr) => {
                handle_daily_result($result, &daily_map, &companies, $sheet_name)
            };
            (@ "yearly", $sheet_name:expr, $result:expr) => {
                handle_yearly_result($result, &yearly_map, &daily_map, &companies, $sheet_name)
            };
        }

        let share_prices_fut = parse_csv! {
            frequency: "daily",
            reader: self.share_prices,
            sheet_name: SHARE_PRICES_FILENAME,
            fields: SharePriceFields,
            entry_date: 2,
            classifying_year: 2,
            classifying_year_is_date: true,
        };

        let balance_sheet_fut = parse_csv! {
            frequency: "yearly",
            reader: self.balance_sheet,
            sheet_name: BALANCE_SHEET_FILENAME,
            fields: BalanceSheetFields,
            entry_date: 6,
            classifying_year: 3,
            classifying_year_is_date: false,
        };

        let cash_flow_fut = parse_csv! {
            frequency: "yearly",
            reader: self.cash_flow,
            sheet_name: CASH_FLOW_FILENAME,
            fields: CashFlowFields,
            entry_date: 6,
            classifying_year: 3,
            classifying_year_is_date: false,
        };

        let income_statement_fut = parse_csv! {
            frequency: "yearly",
            reader: self.income_statement,
            sheet_name: INCOME_STATEMENT_FILENAME,
            fields: IncomeStatementFields,
            entry_date: 6,
            classifying_year: 3,
            classifying_year_is_date: false,
        };

        // first the share_prices
        share_prices_fut.await?;

        // then the rest
        try_join!(balance_sheet_fut, cash_flow_fut, income_statement_fut)?;

        Ok(StorageRepr {
            companies,
            yearly: yearly_map.into_inner(),
            daily: daily_map.into_inner(),
        })
    }
}

#[derive(Error, Debug)]
#[error("File not found: {0}")]
pub struct FileNotFoundError(PathBuf);

impl Fetcher<BufReader<File>> {
    pub async fn from_local(path: impl AsRef<Path>) -> anyhow::Result<Self> {
        let path = path.as_ref();

        let read_file = async move |file_path: PathBuf| -> anyhow::Result<_> {
            if !file_path.exists() {
                Err(FileNotFoundError(file_path).into())
            } else {
                Ok(BufReader::with_capacity(
                    READ_CAPACITY,
                    File::open(file_path).await?,
                ))
            }
        };

        Ok(Fetcher {
            balance_sheet: read_file(path.join(BALANCE_SHEET_FILENAME)).await?,
            cash_flow: read_file(path.join(CASH_FLOW_FILENAME)).await?,
            income_statement: read_file(path.join(INCOME_STATEMENT_FILENAME)).await?,
            share_prices: read_file(path.join(SHARE_PRICES_FILENAME)).await?,
            companies: read_file(path.join(COMPANIES_FILENAME)).await?,
        })
    }
}

#[derive(Error, Debug)]
#[error("Simfin file parsing error in {0}: {1}")]
pub struct FileParsingError(String, String);

// Private

#[derive(Debug)]
struct ParseOptions<'a, F> {
    sheet_name: &'a str,
    columns: HashSet<F>, // returned columns will be ordered in the way they appear
    companies: &'a Companies,
    entry_date_column: usize,
    classifying_year_column: usize,
    classifying_year_column_is_date: bool,
}

#[derive(Debug)]
struct ParseResult<F> {
    pub company_index: CompanyId,
    pub entry_date: NaiveDate,
    pub classifying_year: i32,
    pub data: HashMap<F, f32>,
}

impl<R: FetcherRead> Fetcher<R> {
    async fn parse_company_csv(
        company_sheet: &mut R,
        sheet_name: &str,
    ) -> anyhow::Result<Companies> {
        let mut line = String::new();
        let mut company_i = 0;
        let mut companies = Companies::new();

        for i in 0.. {
            line.clear();
            if company_sheet.read_line(&mut line).await? == 0 {
                break;
            }

            if i == 0 {
                continue;
            }

            let company_name = line
                .split(CSV_SEP)
                .next() // only headers
                .ok_or_else(|| {
                    FileParsingError(
                        sheet_name.to_string(),
                        "company column not found".to_string(),
                    )
                })?;

            if company_name.contains("_old") {
                continue;
            }

            companies.insert(company_name.to_string(), company_i);
            company_i += 1;
        }

        Ok(companies)
    }

    async fn parse_sheet_csv<F, E, EFut>(
        sheet: &mut R,
        options: ParseOptions<'_, F>,
        mut run_for_each: E,
    ) -> anyhow::Result<()>
    where
        F: Fields,
        EFut: Future<Output = anyhow::Result<()>>,
        E: FnMut(ParseResult<F>) -> EFut,
    {
        let mut line = String::new();

        for i in 0.. {
            line.clear();
            if sheet.read_line(&mut line).await? == 0 {
                break;
            }

            if i == 0 {
                continue;
            }

            // remove the new line because BufRead::read_line includes it.
            let line = &line[..(line.len() - 1)];

            match handle_csv_line(line, &options)? {
                CsvLineDecision::Keep(outcome) => {
                    let result = outcome.try_into().map_err(|_| {
                        FileParsingError(
                            options.sheet_name.to_string(),
                            "something went wrong, some indices could not be parsed".to_string(),
                        )
                    })?;
                    run_for_each(result).await?;
                }
                CsvLineDecision::Skip => continue,
            }
        }

        Ok(())
    }
}

#[derive(Debug)]
enum CsvLineDecision<F> {
    Keep(CsvLineOutcome<F>),
    Skip,
}

#[derive(Debug)]
struct CsvLineOutcome<F> {
    company_index: Option<CompanyId>,
    entry_date: Option<NaiveDate>,
    classifying_year: Option<i32>,
    data: HashMap<F, f32>,
}

impl<F> Default for CsvLineOutcome<F> {
    fn default() -> Self {
        CsvLineOutcome {
            company_index: None,
            entry_date: None,
            classifying_year: None,
            data: HashMap::new(),
        }
    }
}

impl<F: Fields> TryFrom<CsvLineOutcome<F>> for ParseResult<F> {
    type Error = ();
    fn try_from(outcome: CsvLineOutcome<F>) -> Result<Self, ()> {
        Ok(ParseResult {
            company_index: outcome.company_index.ok_or(())?,
            entry_date: outcome.entry_date.ok_or(())?,
            classifying_year: outcome.classifying_year.ok_or(())?,
            data: outcome.data,
        })
    }
}

fn handle_csv_line<F>(line: &str, options: &ParseOptions<F>) -> anyhow::Result<CsvLineDecision<F>>
where
    F: Fields,
{
    let mut outcome = CsvLineOutcome::default();

    for (i_element, element) in line.split(CSV_SEP).enumerate() {
        if i_element == 0 {
            if let Some(&index) = options.companies.get(element) {
                outcome.company_index = Some(index);
            } else {
                // Skip if not present
                return Ok(CsvLineDecision::Skip);
            }
        }
        if i_element == options.entry_date_column {
            outcome.entry_date = Some(NaiveDate::parse_from_str(element, "%F")?);
        }
        if i_element == options.classifying_year_column {
            outcome.classifying_year = if options.classifying_year_column_is_date {
                Some(NaiveDate::parse_from_str(element, "%F")?.year())
            } else {
                let parsed = element.parse::<i32>().map_err(|_| {
                    FileParsingError(
                        options.sheet_name.to_string(),
                        format!("unable to parse into year: {}", element),
                    )
                })?;

                Some(parsed)
            };
        }

        if let Ok((true, field)) = F::try_from(i_element).map(|f| (options.columns.contains(&f), f))
        {
            if element.is_empty() {
                outcome.data.insert(field, f32::NAN);
            } else {
                let parsed_float = element.parse::<f32>().map_err(|_| {
                    FileParsingError(
                        options.sheet_name.to_string(),
                        format!("unable to parse into float: {}", element),
                    )
                })?;

                outcome.data.insert(field, parsed_float);
            }
        }
    }

    Ok(CsvLineDecision::Keep(outcome))
}

async fn handle_yearly_result<F>(
    parse_result: ParseResult<F>,
    yearly_map: &RefCell<YearlyMap>,
    daily_map: &RefCell<DailyMap>,
    companies: &Companies,
    sheet_name: &str,
) -> anyhow::Result<()>
where
    F: YearlyFields,
{
    let mut yearly_map = yearly_map.borrow_mut();
    let daily_map = daily_map.borrow();

    let yearly_array = yearly_map
        .entry(parse_result.classifying_year)
        .or_insert_with(|| {
            Array2::from_elem((YearlyField::VARIANT_COUNT, companies.len()), f32::NAN)
        });

    let daily_data_slice = daily_map
        .get(&parse_result.classifying_year)
        .unwrap_or_else(|| panic!("no daily data for year {}!", parse_result.classifying_year))
        .slice(s![
            parse_result.entry_date.ordinal0() as usize..,
            ..,
            parse_result.company_index
        ]);

    F::to_yearly(
        &parse_result.data,
        daily_data_slice,
        yearly_array.slice_mut(s![.., parse_result.company_index]),
    )
    .ok_or_else(|| {
        FileParsingError(
            sheet_name.to_string(),
            "error while mapping to StorageRepr".to_string(),
        )
        .into()
    })
}

async fn handle_daily_result<F>(
    parse_result: ParseResult<F>,
    daily_map: &RefCell<DailyMap>,
    companies: &Companies,
    sheet_name: &str,
) -> anyhow::Result<()>
where
    F: DailyFields,
{
    let mut daily_map = daily_map.borrow_mut();

    let array = daily_map
        .entry(parse_result.classifying_year)
        .or_insert_with(|| {
            Array3::from_elem(
                (
                    NaiveDate::from_ymd(parse_result.classifying_year, 12, 31).ordinal() as usize,
                    DailyField::VARIANT_COUNT,
                    companies.len(),
                ),
                f32::NAN,
            )
        });

    F::to_daily(
        &parse_result.data,
        array.slice_mut(s![
            parse_result.entry_date.ordinal0() as usize,
            ..,
            parse_result.company_index
        ]),
    )
    .ok_or_else(|| {
        FileParsingError(
            sheet_name.to_string(),
            "error while mapping to StorageRepr".to_string(),
        )
        .into()
    })
}

trait Fields: IndexEnum + Hash {}

trait YearlyFields: Fields {
    fn to_yearly(
        self_data: &HashMap<Self, f32>,
        stock_data_after: ArrayView2<'_, f32>,
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
                // Rust does not handle this nested macro business very well. Maybe a bug should be
                // filed. In any case, this code is rather horrible.
                #[allow(unused_variables)]
                #[allow(unused_macros)]
                fn to_yearly(
                    self_data: &HashMap<Self, f32>,
                    daily_data_after: ArrayView2<'_, f32>,
                    mut out: ArrayViewMut1<'_, f32>,
                ) -> Option<()> {
                    macro_rules! yearly_financial {
                        ($field: ident) => {
                            out[YearlyField::$field.index()]
                        };
                    }

                    macro_rules! data {
                        ($field: ident) => {
                            *self_data.get(&Self::$field)?
                        };
                    }

                    macro_rules! daily_data {
                        ($field: ident) => {
                            daily_data_after.index_axis(Axis(1), DailyField::$field.index())
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
                            out[DailyField::$field.index()]
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
            impl IndexEnum for $t {}
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

        yearly_financial!(SharePriceAtReport) = daily_data!(HighSharePrice)
            .iter()
            .enumerate()
            .skip(MIN_DAYS_AFTER_REPORT_SHARE_PRICE)
            .find(|&(i, price)| !price.is_nan() && i <= MAX_DAYS_AFTER_REPORT_SHARE_PRICE)
            .map(|(_i, &price)| price)
            .unwrap_or(f32::NAN);
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
