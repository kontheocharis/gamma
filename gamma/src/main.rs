#![feature(async_closure)]

#[macro_use]
extern crate gamma_derive;

#[macro_use]
mod utils;

mod traits;
mod financials;

// financials::FinancialsFetcher implementors:
mod simfin;

use log::{debug, error, info, trace, warn};
use std::error::{Error};
use std::mem::{size_of};
use chrono::{NaiveDate, Duration};
use tokio::prelude::*;

use crate::financials::{Financials, Field, Fetcher, FetcherOptions};
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


#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {

    setup_logger()?;

    // let financials = Financials::load("save_test")?;
    // // financials.save("save_test");

    println!("Hello, world!");

    let fetcher = simfin::Fetcher::from_net().await?;

    println!("{:?}", fetcher);

    // fetcher.fetch(&FetcherOptions {
    //     date: NaiveDate::from_ymd(2020, 4, 20),
    //     cash_flows_back: Duration::weeks(52)
    // }).await?;

    Ok(())
}
