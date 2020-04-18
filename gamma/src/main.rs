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
use serde::de::DeserializeOwned;
use structopt::StructOpt;
use tokio::io::AsyncReadExt;

use crate::fetching::Fetch;
use crate::financials::Financials;
use crate::metrics::v1;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = arg::Options::from_args();
    setup_logger(if opt.debug {
        log::LevelFilter::Debug
    } else {
        log::LevelFilter::Warn
    })?;

    match opt.mode {
        arg::OperatingMode::ParseSimfin { in_dir, out_dir } => {
            parse_simfin(&in_dir, &out_dir).await
        }
        arg::OperatingMode::RunV1 {
            repr_dir,
            options_file,
        } => {
            let v1_opts: v1::Options = parse_yaml_from_path(&options_file).await?;

            let options = financials::Options {
                yearly_min: v1_opts.buy_date.year() - v1_opts.cash_flows_back as i32,
                yearly_max: v1_opts.buy_date.year(),
                daily_min: v1_opts.buy_date - Duration::weeks(52),
                daily_max: v1_opts.buy_date + Duration::weeks(52 * v1_opts.lookahead_years as i64),
            };

            let financials = Financials::from_path(&repr_dir, options).await?;

            let metrics = v1::Metrics::calculate(&financials, v1_opts)?;

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

            /// The options file for V1 metrics in yaml.
            #[structopt(parse(from_os_str))]
            options_file: PathBuf,
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

async fn parse_yaml_from_path<T>(path: &Path) -> anyhow::Result<T>
where
    T: DeserializeOwned,
{
    let mut file = tokio::fs::File::open(path).await?;
    let mut buf = Vec::new();
    file.read_to_end(&mut buf).await?;
    Ok(serde_yaml::from_slice(&buf)?)
}

fn setup_logger(level: log::LevelFilter) -> Result<(), fern::InitError> {
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
        .level(level)
        .chain(std::io::stdout())
        .apply()?;
    Ok(())
}
