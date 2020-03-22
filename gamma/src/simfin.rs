use std::collections::{HashMap};
use std::fmt;
use std::error::{Error};
use std::io::{Cursor, Read, BufReader, BufRead};

use async_trait::async_trait;
use futures::prelude::*;
use futures::future::TryFutureExt;
use chrono::{NaiveDate, Duration};
use ndarray::{Array2};
use url::{Url};
use zip::read::{ZipArchive, ZipFile};

use crate::financials::{self, Financials};
use crate::traits::{CountVariants};


#[derive(Debug)]
pub enum FromNetError {
    NetworkError(reqwest::Error),
    UnexpectedResponse(String),
    Internal(Box<dyn Error>),
}

impl_from!(FromNetError {
    NetworkError => { reqwest::Error },
    Internal => { std::io::Error }
});

impl fmt::Display for FromNetError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NetworkError(ref error) => write!(f, "Network error: {}", error),
            Self::UnexpectedResponse(ref msg) => write!(f, "Unexpected response: {}", msg),
            Self::Internal(ref error) => write!(f, "Internal error: {}", error),
        }
    }
}

impl Error for FromNetError {}


#[derive(Debug)]
pub struct Fetcher {
    balance_sheet: Vec<String>,
    cash_flow: Vec<String>,
    income: Vec<String>,
}

impl Fetcher {
    pub async fn from_net() -> Result<Fetcher, FromNetError> {
        let client = reqwest::Client::new();

        type ResponseResult = Result<reqwest::Response, reqwest::Error>;

        let handle_response = async move |result: ResponseResult| -> Result<Vec<String>, FromNetError> {
            let response = result?;
            let url = response.url().to_string();
            let bytes = response.bytes().await?;

            let mut archive = ZipArchive::new(Cursor::new(bytes)).
                map_err(|err| FromNetError::UnexpectedResponse(
                        format!("{} returns an invalid zip archive: {}", url, err)
                ))?;

            if archive.len() != 1 {
                return Err(FromNetError::UnexpectedResponse(
                        format!("was expecting one file in archive for {}, got {}", url, archive.len())
                ));
            }

            Ok(BufReader::new(archive.by_index(0).unwrap()).lines().collect::<Result<Vec<_>, _>>()?)
        };

        let mut requests = [
            "https://simfin.com/api/bulk?dataset=balance&market=us&variant=annual",
            "https://simfin.com/api/bulk?dataset=cashflow&market=us&variant=annual",
            "https://simfin.com/api/bulk?dataset=income&market=us&variant=annual",
        ].iter().map(|&url| client.get(url).send().then(handle_response));

        let csv_files = future::try_join3(
            requests.next().unwrap(),
            requests.next().unwrap(),
            requests.next().unwrap()
        ).await?;

        Ok(Fetcher {
            balance_sheet: csv_files.0,
            cash_flow: csv_files.1,
            income: csv_files.2,
        })
    }
}

#[async_trait]
impl financials::Fetcher for Fetcher {
    type FetchError = ();

    async fn fetch(&self, options: &financials::FetcherOptions) -> Result<Financials, ()> {
        Ok(Financials::empty(10))
    }
}
