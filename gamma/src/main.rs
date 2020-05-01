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

use std::collections::HashSet;
use std::path::{Path, PathBuf};
use std::time::Instant;

use chrono::{Datelike, Duration, NaiveDate};
use log::*;
use serde::de::DeserializeOwned;
use structopt::StructOpt;
use tokio::io::AsyncReadExt;

use crate::fetching::Fetch;
use crate::financials::Financials;

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
        arg::OperatingMode::Run {
            repr_dir,
            options_file,
        } => {
            let metrics_opts: metrics::Options = parse_yaml_from_path(&options_file).await?;
            let buy_date = metrics_opts.buy_date;
            let sell_date = metrics_opts.sell_date;

            info!("Using metrics options: {:#?}", &metrics_opts);

            let fin_opts = financials::Options {
                yearly_min: buy_date.year() - metrics_opts.cash_flows_back as i32,
                yearly_max: buy_date.year(),
                daily_min: buy_date - Duration::weeks(52),
                daily_max: sell_date,
            };

            info!("Using financials options: {:#?}", &fin_opts);

            let financials_time = Instant::now();
            let financials = Financials::from_path(&repr_dir, fin_opts).await?;
            info!("Loaded financials in {:.2?}", financials_time.elapsed());

            let metrics_bounds = metrics::Bounds::from_legacy_options(&metrics_opts);

            let metrics_time = Instant::now();
            let metrics = metrics::Metrics::calculate(&financials, metrics_opts)?;
            info!("Calculated metrics in {:.2?}", metrics_time.elapsed());

            let evaluator = metrics::Evaluator::new(&metrics);

            let ignore_fields = HashSet::new();
            let evaluated = evaluator.evaluate(metrics_bounds, &ignore_fields);
            let backtracked = evaluated.backtrack();
            let stats = backtracked.stats();

            info!(
                "Companies which reached return percent: {:#?}",
                backtracked
                    .companies_which(metrics::BacktrackResult::ReachedReturnPercent)
                    .map(|(i, price)| format!(
                        "{}: {:.2} to {:.2}",
                        financials.index_to_company(i),
                        metrics.get_metric(metrics::Field::BuySharePrice)[i],
                        price,
                    ))
                    .collect::<Vec<_>>()
            );

            info!(
                "Companies which gained in the end: {:#?}",
                backtracked
                    .companies_which(metrics::BacktrackResult::GainAtEnd)
                    .map(|(i, price)| format!(
                        "{}: {:.2} to {:.2}",
                        financials.index_to_company(i),
                        metrics.get_metric(metrics::Field::BuySharePrice)[i],
                        price,
                    ))
                    .collect::<Vec<_>>()
            );

            print_results(
                buy_date,
                sell_date,
                &financials,
                &evaluated,
                &backtracked,
                &stats,
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

        /// Run analysis.
        Run {
            /// The directory containing the parsed representation.
            #[structopt(parse(from_os_str))]
            repr_dir: PathBuf,

            /// The options file for metrics in yaml.
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

fn print_results(
    buy_date: NaiveDate,
    sell_date: NaiveDate,
    financials: &Financials,
    evaluated: &metrics::Evaluated,
    _backtracked: &metrics::Backtracked,
    stats: &metrics::BacktrackStatistics,
) {
    let companies_considered = financials.companies().len();

    let companies_sufficient = evaluated.companies_sufficient().count();
    let companies_investable = evaluated.companies_investable().count();

    let total_successful = stats.n_reached_percent + stats.n_gain_at_end;
    let successful_pct = (total_successful as f32 / companies_investable as f32) * 100.0;

    println!(
        "RESULTS for investment: {} to {}",
        buy_date.format("%d %B %Y"),
        sell_date.format("%d %B %Y")
    );
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
