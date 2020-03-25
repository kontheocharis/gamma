#![feature(async_closure)]
#![feature(trait_alias)]

#[macro_use]
extern crate gamma_derive;

mod traits;
mod financials;
// mod simfin;

use std::env;
use std::error::{Error};

use chrono::{NaiveDate, Duration};
use log::{debug, error, info, trace, warn};
use tokio::prelude::*;

use crate::financials::{FinancialStore, Fetcher, yearly, daily};
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
async fn main() -> Result<(), anyhow::Error> {
    let args: Vec<String> = env::args().collect();

    setup_logger()?;

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
