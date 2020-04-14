#![feature(async_closure)]
#![feature(trait_alias)]
#![feature(nll)]

// #[macro_use]
// extern crate gamma_derive;

#[macro_use]
mod util;

mod fetching;
mod financials;
mod metrics;
mod simfin;

use std::collections::HashMap;
use std::path;

use async_trait::async_trait;
use chrono::NaiveDate;
use enum_iterator::IntoEnumIterator;
use ndarray::{s, Array2, Array3};
use thiserror::Error;

use crate::fetching::{Fetch, StorageRepr};
use crate::financials::{Companies, Financials, Options, YearlyField};
use crate::metrics::v1;

fn setup_logger() -> Result<(), fern::InitError> {
    fern::Dispatch::new()
        .format(|out, message, record| {
            out.finish(format_args!(
                "{}[{}][{}] {}",
                chrono::Local::now().format("[%Y-%m-%d][%H:%M:%S]"),
                record.target(),
                record.level(),
                message
            ))
        })
        .level(log::LevelFilter::Debug)
        .chain(std::io::stdout())
        .apply()?;
    Ok(())
}

#[derive(Debug)]
struct MockFetcher;

#[derive(Error, Debug)]
#[error("Mock error")]
struct MockFetcherError;

#[async_trait]
impl Fetch for MockFetcher {
    type StorageReprError = MockFetcherError;

    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::StorageReprError> {
        let mut repr = StorageRepr {
            companies: Companies::new(),
            yearly: HashMap::new(),
            daily: HashMap::new(),
        };

        repr.companies.insert("AAPL".to_string(), 0);
        repr.companies.insert("MSFT".to_string(), 1);
        repr.companies.insert("GOOG".to_string(), 2);
        repr.companies.insert("SNAP".to_string(), 3);

        repr.yearly.insert(
            2018,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2019,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2020,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2021,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2022,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );

        repr.daily.insert(
            2017,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2018,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2019,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2020,
            Array3::zeros((366, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2021,
            Array3::zeros((366, financials::DailyField::VARIANT_COUNT, 4)),
        );

        Ok(repr)
    }
}

async fn save_simfin(dir: &str, options: Options) -> anyhow::Result<Financials> {
    let repr = simfin::Fetcher::from_local(dir)
        .await?
        .to_storage_repr()
        .await?;

    repr.save_to_path(&format!("{}_repr", dir)).await?;

    Ok(Financials::from_repr(repr, options)?)
}

async fn cached_simfin(dir: &str, options: Options) -> anyhow::Result<Financials> {
    Ok(Financials::from_path(&format!("{}_repr", dir), options).await?)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    setup_logger()?;

    if args.len() != 3 {
        Err(anyhow::anyhow!("Usage: (reparse|cached) <dir>"))?
    }

    let options = Options {
        yearly_min: 2013,
        yearly_max: 2016,
        daily_min: NaiveDate::from_ymd(2013, 1, 1),
        daily_max: NaiveDate::from_ymd(2016, 12, 1),
    };

    let financials = match args[1].as_ref() {
        "reparse" => save_simfin(&args[2], options).await?,
        "cached" => cached_simfin(&args[2], options).await?,
        _ => panic!("Unexpected argument"),
    };

    let metrics = v1::Metrics::calculate(
        &financials,
        v1::Options {
            cash_flows_back: 3,
            buy_date: NaiveDate::from_ymd(2016, 12, 1),
        },
    )?;

    let evaluated = metrics.evaluate();

    println!(
        "{:?}",
        evaluated
            .companies_investable()
            .map(|i| financials.index_to_company(i))
            .collect::<Vec<_>>()
    );

    // OLD:

    // println!(
    //     "{:#?}",
    //     financials.yearly().get((
    //         financials.year_to_index(2016),
    //         YearlyField::CashShortTermInvestments as usize,
    //         financials.company_to_index("AAON")
    //     )).unwrap()
    // );

    // let _fetcher = MockFetcher;
    // let repr = fetcher.to_storage_repr().await?;

    // repr.save_to_path(&args[1]).await?;

    // let fin = Financials::from_path(
    //     &args[1],
    //     Options {
    //         yearly_min: 2018,
    //         yearly_max: 2020,
    //         daily_min: NaiveDate::from_ymd(2018, 3, 14),
    //         daily_max: NaiveDate::from_ymd(2020, 12, 10),
    //     },
    // )
    // .await?;

    // let financials = Financials::load("save_test")?;
    // // financials.save("save_test");

    // let mut loader = simfin::Loader::from_local(&args[1]).await?;

    // // println!("{:#?}", loader);

    // loader.load(&LoaderOptions {
    //     date: NaiveDate::from_ymd(2017, 4, 20),
    //     cash_flows_back: Duration::weeks(52)
    // }).await?;

    Ok(())
}
