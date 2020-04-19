#![allow(dead_code)]
#![feature(async_closure)]
#![feature(trait_alias)]

#[macro_use]
mod util;

mod fetching;
mod financials;
mod metrics;
mod mock;
mod simfin;

use std::path::{Path, PathBuf};

use chrono::{Datelike, Duration, NaiveDate};
use log::*;
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
            let buy_date = v1_opts.buy_date;

            info!("Using V1 options: {:#?}", &v1_opts);

            let fin_opts = financials::Options {
                yearly_min: buy_date.year() - v1_opts.cash_flows_back as i32,
                yearly_max: buy_date.year(),
                daily_min: buy_date - Duration::weeks(52),
                daily_max: buy_date + Duration::weeks(52 * v1_opts.lookahead_years as i64),
            };

            info!("Using financials options: {:#?}", &fin_opts);

            let financials = Financials::from_path(&repr_dir, fin_opts).await?;

            info!("Fetched financials");

            let metrics = v1::Metrics::calculate(&financials, v1_opts)?;

            info!("Calculated metrics");

            let evaluated = metrics.evaluate();
            let backtracked = evaluated.backtrack();
            let stats = backtracked.stats();

            print_v1_results(buy_date, &financials, &evaluated, &backtracked, &stats);

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

fn print_v1_results(
    buy_date: NaiveDate,
    financials: &Financials,
    evaluated: &v1::Evaluated,
    _backtracked: &v1::Backtracked,
    stats: &v1::BacktrackStatistics,
) {
    let companies_considered = financials.companies().len();

    let companies_sufficient = evaluated.companies_sufficient().count();
    let companies_investable = evaluated.companies_investable().count();

    let total_successful = stats.n_reached_percent + stats.n_gain_at_end;
    let successful_pct = (total_successful as f32 / companies_investable as f32) * 100.0;

    println!("-- RESULTS for buy date {} --", buy_date.format("%d %B %Y"));
    println!("Total companies considered: {},", companies_considered);

    println!("Companies with sufficient data: {},", companies_sufficient);

    if companies_sufficient == 0 {
        // No point in printing anything else.
        println!("Insufficient data to continue.");
        return;
    }

    println!(
        "Companies that were deemed investable: {} ({:.2}% of sufficient),",
        companies_investable,
        (companies_investable as f32 / companies_sufficient as f32) * 100.0,
    );

    if companies_investable == 0 {
        // no point in printing anything else.
        println!("Insufficient data to continue.");
        return;
    }

    println!(
        "Companies that yielded return percent: {} ({:.2}% of investable),",
        stats.n_reached_percent,
        (stats.n_reached_percent as f32 / companies_investable as f32) * 100.0,
    );
    println!(
        "Companies that only increased in price: {} ({:.2}% of investable),",
        stats.n_gain_at_end,
        (stats.n_gain_at_end as f32 / companies_investable as f32) * 100.0
    );
    println!(
        "Companies that decreased in price: {} ({:.2}% of investable),",
        stats.n_loss_at_end,
        (stats.n_loss_at_end as f32 / companies_investable as f32) * 100.0
    );

    println!(
        "Total successful predictions: {} ({:.2}% of investable),",
        total_successful, successful_pct
    );
    println!(
        "Overall: {}",
        if successful_pct > 50.0 {
            "GAIN"
        } else {
            "LOSS"
        }
    );
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
