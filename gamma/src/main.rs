#![feature(async_closure)]
#![feature(trait_alias)]

#[macro_use]
extern crate gamma_derive;

mod traits;
mod financials;
mod simfin;

use async_trait::async_trait;
use ndarray::{Array2, Array3};
use std::collections::{HashMap};
use thiserror::{Error};
use tokio::prelude::*;
use chrono::{NaiveDate};

use crate::financials::{Fetcher, StorageRepr, FinancialStore, LoaderOptions};
use crate::traits::{CountVariants};

fn setup_logger() -> Result<(), fern::InitError> {
    fern::Dispatch::new()
        .format(|out, message, record| {
            out.finish(format_args!(
                    "{}[{}][{}] {}",
                    chrono::Local::now().format("[%Y-%m-%d][%H:%M:%S]"),
                    record.target(),
                    record.level(),
                    message)) })
        .level(log::LevelFilter::Debug)
        .chain(std::io::stdout())
        .apply()?;
    Ok(())
}

#[derive(Debug)]
struct MockFetcher;

#[derive(Error, Debug)]
#[error("Nonexistent error")]
struct MockFetcherError;

#[async_trait]
impl Fetcher for MockFetcher {
    type Error = MockFetcherError;

    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::Error> {
        let mut repr = StorageRepr {
            companies: HashMap::new(),
            yearly: HashMap::new(),
            daily: HashMap::new()
        };

        repr.companies.insert("AAPL".to_string(), 0);
        repr.companies.insert("MSFT".to_string(), 1);
        repr.companies.insert("GOOG".to_string(), 2);
        repr.companies.insert("SNAP".to_string(), 3);

        repr.yearly.insert(2018, Array2::zeros((financials::yearly::Field::COUNT + 1, 4)));
        repr.yearly.insert(2019, Array2::zeros((financials::yearly::Field::COUNT + 1, 4)));
        repr.yearly.insert(2020, Array2::zeros((financials::yearly::Field::COUNT + 1, 4)));

        repr.daily.insert(2018, Array3::zeros((financials::yearly::Field::COUNT + 1, 4, 365)));
        repr.daily.insert(2019, Array3::zeros((financials::yearly::Field::COUNT + 1, 4, 365)));
        repr.daily.insert(2020, Array3::zeros((financials::yearly::Field::COUNT + 1, 4, 366)));

        Ok(repr)
    }
}


#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    let args: Vec<String> = std::env::args().collect();
    setup_logger()?;

    let mut fetcher = MockFetcher;
    let repr = fetcher.to_storage_repr().await?;

    let store = FinancialStore::load(repr, &LoaderOptions {
        from: NaiveDate::from_ymd(2010, 3, 14),
        to: NaiveDate::from_ymd(2020, 3, 14)
    });

    println!("{:#?}", &store);

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
