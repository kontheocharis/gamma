#![feature(async_closure)]
#![feature(trait_alias)]

#[macro_use]
extern crate gamma_derive;

mod financials;
// mod simfin;
mod traits;

use async_trait::async_trait;
use chrono::NaiveDate;
use ndarray::{Array2, Array3};
use std::collections::{HashMap};
use thiserror::Error;
use tokio::prelude::*;

use crate::financials::{Financials, LoadOptions, fetcher::{Fetcher, StorageRepr}};
use crate::traits::CountVariants;

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
#[error("Nonexistent error")]
struct MockFetcherError;

#[async_trait]
impl Fetcher for MockFetcher {
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

        repr.yearly
            .insert(2018, Array2::zeros((financials::YearlyField::COUNT, 4)));
        repr.yearly
            .insert(2019, Array2::zeros((financials::YearlyField::COUNT, 4)));
        repr.yearly
            .insert(2020, Array2::zeros((financials::YearlyField::COUNT, 4)));
        repr.yearly
            .insert(2021, Array2::zeros((financials::YearlyField::COUNT, 4)));
        repr.yearly
            .insert(2022, Array2::zeros((financials::YearlyField::COUNT, 4)));

        repr.daily
            .insert(2017, Array3::zeros((365, financials::DailyField::COUNT, 4)));
        repr.daily
            .insert(2018, Array3::zeros((365, financials::DailyField::COUNT, 4)));
        repr.daily
            .insert(2019, Array3::zeros((365, financials::DailyField::COUNT, 4)));
        repr.daily
            .insert(2020, Array3::zeros((366, financials::DailyField::COUNT, 4)));
        repr.daily
            .insert(2021, Array3::zeros((366, financials::DailyField::COUNT, 4)));

        Ok(repr)
    }
}

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    let args: Vec<String> = std::env::args().collect();
    setup_logger()?;

    let mut fetcher = MockFetcher;
    // let repr = fetcher.to_storage_repr().await?;

    // repr.save_to_path(&args[1]).await?;

    let fin = Financials::from_path(
        &args[1],
        &LoadOptions {
            yearly_min: 2018,
            yearly_max: 2020,
            daily_min: NaiveDate::from_ymd(2018, 3, 14),
            daily_max: NaiveDate::from_ymd(2020, 12, 10),
        },
    ).await?;

    println!("{:#?}", fin);

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
