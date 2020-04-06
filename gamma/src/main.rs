#![feature(async_closure)]
#![feature(trait_alias)]

// #[macro_use]
// extern crate gamma_derive;

#[macro_use]
mod util;

mod fetching;
mod financials;
mod simfin;

use std::collections::HashMap;

use async_trait::async_trait;
use chrono::NaiveDate;
use enum_iterator::IntoEnumIterator;
use ndarray::{Array2, Array3};
use thiserror::Error;

use crate::fetching::{Fetch, StorageRepr};
use crate::financials::{Financials, Options};

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
            companies: HashMap::new(),
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

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    setup_logger()?;

    if args.len() != 2 {
        Err(anyhow::anyhow!("Need path argument!"))?
    }

    let mut fetcher = simfin::Fetcher::from_local(&args[1]).await?;
    let repr = fetcher.to_storage_repr().await?;
    println!("{:?}", repr);

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

    // println!(
    //     "{:#?}",
    //     (
    //         fin.index_to_date(1002),
    //         fin.date_to_index(NaiveDate::from_ymd(2018, 3, 15)),
    //         fin.date_to_index(NaiveDate::from_ymd(2020, 12, 10)),
    //         fin.year_to_index(2019),
    //         fin.date_range(),
    //         fin.year_range(),
    //         fin.valid_year_index(2)
    //     )
    // );

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
