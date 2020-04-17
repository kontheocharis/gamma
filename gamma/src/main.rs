#![allow(dead_code)]
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
mod mock;
mod simfin;

use std::path::{Path, PathBuf};

use chrono::{Datelike, Duration, NaiveDate};
use structopt::StructOpt;

use crate::fetching::Fetch;
use crate::financials::{Financials, Options};
use crate::metrics::v1;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = arg::Options::from_args();
    setup_logger()?;

    match opt.mode {
        arg::OperatingMode::ParseSimfin { in_dir, out_dir } => {
            parse_simfin(&in_dir, &out_dir).await
        }
        arg::OperatingMode::RunV1 {
            repr_dir,
            buy_date,
            cash_flows_back,
            lookahead_years,
            return_percent: _,
        } => {
            let options = Options {
                yearly_min: buy_date.year() - cash_flows_back as i32,
                yearly_max: buy_date.year(),
                daily_min: buy_date - Duration::weeks(52),
                daily_max: buy_date + Duration::weeks(52 * lookahead_years as i64),
            };

            let financials = Financials::from_path(&repr_dir, options).await?;

            let metrics = v1::Metrics::calculate(
                &financials,
                v1::Options {
                    cash_flows_back: cash_flows_back,
                    buy_date: buy_date,
                },
            )?;

            let evaluated = metrics.evaluate();

            println!(
                "Result: {:?}",
                evaluated
                    .companies_investable()
                    .map(|i| financials.index_to_company(i))
                    .collect::<Vec<_>>()
            );

            Ok(())
        }
    }
}

mod arg {
    use super::*;

    #[derive(Debug, StructOpt)]
    #[structopt(about = "A value investment strategy tool.")]
    pub struct Options {
        /// Activate debug mode
        #[structopt(short, long)]
        pub debug: bool,

        /// The mode to run in.
        #[structopt(subcommand)]
        pub mode: OperatingMode,
    }

    #[derive(Debug, StructOpt)]
    pub enum OperatingMode {
        /// Parse simfin data into internal representation.
        ParseSimfin {
            /// The directory containing the raw data.
            #[structopt(parse(from_os_str))]
            in_dir: PathBuf,

            /// The directory to put the parsed representation into.
            #[structopt(parse(from_os_str))]
            out_dir: PathBuf,
        },

        /// Run v1 analysis.
        RunV1 {
            /// The directory containing the parsed representation.
            #[structopt(parse(from_os_str))]
            repr_dir: PathBuf,

            /// The date on which to buy stock.
            #[structopt(parse(try_from_str = parse_iso_date))]
            buy_date: NaiveDate,

            /// Number of years back to ensure positive cash flow.
            #[structopt(long, short, default_value = "3")]
            cash_flows_back: usize,

            /// Number of years ahead to run analysis for. (backtesting)
            #[structopt(long, short, default_value = "1")]
            lookahead_years: usize,

            /// Return percent at which to sell.
            #[structopt(long, short, default_value = "1.0")]
            return_percent: f32,
        },
    }

    fn parse_iso_date(src: &str) -> chrono::format::ParseResult<NaiveDate> {
        NaiveDate::parse_from_str(src, "%F")
    }
}

async fn parse_simfin(in_dir: &Path, out_dir: &Path) -> anyhow::Result<()> {
    let repr = simfin::Fetcher::from_local(in_dir)
        .await?
        .to_storage_repr()
        .await?;

    repr.save_to_path(out_dir).await
}

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
