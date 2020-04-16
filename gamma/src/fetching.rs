use std::collections::HashMap;
use std::fmt::{Debug, Display};
use std::iter::{self, FromIterator};
use std::path::{Path, PathBuf};

use async_trait::async_trait;
use futures::prelude::*;
use futures::stream::{FuturesUnordered, StreamExt, TryStreamExt};
use ndarray::{Array2, Array3};
use thiserror::Error;
use tokio::fs::{self, File};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::try_join;

use crate::financials::{Companies, Financials, Options as FinancialsOptions};

const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";

const YEARLY_FOLDER: &str = "yearly";
const DAILY_FOLDER: &str = "daily";
const COMPANY_FILE: &str = "companies";

pub type YearlyMap = HashMap<i32, Array2<f32>>;
pub type DailyMap = HashMap<i32, Array3<f32>>;

#[derive(Debug)]
pub struct StorageRepr {
    pub companies: Companies,
    pub yearly: YearlyMap, // Axis(0): Columns, Axis(1): Companies
    pub daily: DailyMap, // Axis(0): 0-365 or 0-364, Axis(1): Columns, Axis(2): Companies
}

#[derive(Error, Debug)]
#[error(
    "Missing items: specified folder, subfolders '{}' and '{}', and file '{}' need to exist",
    YEARLY_FOLDER,
    DAILY_FOLDER,
    COMPANY_FILE
)]
pub struct MissingFoldersError;

#[derive(Error, Debug)]
#[error("All filenames in path subfolders must be in form '2018', '2019', '2020', etc.")]
pub struct InvalidYearFilenameError;

impl StorageRepr {
    pub async fn load_from_path<P: AsRef<Path>>(
        path: P,
        yearly_years: (i32, i32),
        daily_years: (i32, i32),
    ) -> anyhow::Result<StorageRepr> {
        let path = path.as_ref();

        let (yearly_folder, daily_folder, company_file) = (
            path.join(YEARLY_FOLDER),
            path.join(DAILY_FOLDER),
            path.join(COMPANY_FILE),
        );

        if !yearly_folder.exists() || !daily_folder.exists() || !company_file.exists() {
            return Err(MissingFoldersError.into());
        }

        let companies_fut = deserialize_from_path::<Companies, _>(&company_file);
        let yearly_fut = get_time_series_for::<Array2<f32>>(&yearly_folder, yearly_years);
        let daily_fut = get_time_series_for::<Array3<f32>>(&daily_folder, daily_years);

        let (companies, yearly, daily) = try_join!(companies_fut, yearly_fut, daily_fut)?;

        Ok(StorageRepr {
            companies,
            yearly,
            daily,
        })
    }

    pub async fn save_to_path<P: AsRef<Path>>(&self, path: P) -> anyhow::Result<()> {
        let path = path.as_ref();

        // Create paths needed
        try_join!(
            fs::create_dir_all(path.join(YEARLY_FOLDER)),
            fs::create_dir_all(path.join(DAILY_FOLDER)),
        )?;

        let yearly_iter = self
            .yearly
            .iter()
            .map(|(year, array)| (year, bincode::serialize(array), YEARLY_FOLDER));

        let daily_iter = self
            .daily
            .iter()
            .map(|(year, array)| (year, bincode::serialize(array), DAILY_FOLDER));

        let company_file = (
            path.join(COMPANY_FILE),
            bincode::serialize(&self.companies),
        );

        FuturesUnordered::from_iter(
            yearly_iter
                .chain(daily_iter)
                .map(|(year, data, folder)| (path.join(folder).join(year.to_string()), data))
                .chain(iter::once(company_file))
                .map(|(path, data)| {
                    fs::File::create(path)
                        .map_err(anyhow::Error::new)
                        .and_then(async move |mut file| Ok(file.write_all(data?.as_ref()).await?))
                }),
        )
        .try_collect()
        .await?;

        Ok(())
    }
}

#[derive(Error, Debug)]
#[error("Fetch error: {0}")]
pub struct FetchError<T: Display + Debug>(T);

#[async_trait]
pub trait Fetch {
    type StorageReprError: Display + Debug + Send + Sync + 'static;

    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::StorageReprError>;

    async fn load_financials(&mut self, options: FinancialsOptions) -> anyhow::Result<Financials> {
        Financials::from_repr(self.to_storage_repr().map_err(FetchError).await?, options)
    }

    async fn save_repr_to_path<P: AsRef<Path> + Send>(&mut self, path: P) -> anyhow::Result<()> {
        self.to_storage_repr()
            .await
            .map_err(FetchError)?
            .save_to_path(path)
            .await
    }
}

// Private

async fn deserialize_from_path<T: serde::de::DeserializeOwned, P: AsRef<Path>>(
    path: P,
) -> anyhow::Result<T> {
    let mut file = File::open(path.as_ref()).await?;
    let mut data = Vec::new();
    file.read_to_end(&mut data).await?;
    Ok(bincode::deserialize(&data)?)
}

async fn get_time_series_for<T: serde::de::DeserializeOwned>(
    folder: &PathBuf,
    year_range: (i32, i32),
) -> anyhow::Result<HashMap<i32, T>> {
    let files: Vec<_> = fs::read_dir(folder)
        .await?
        .map(|entry| -> anyhow::Result<_> {
            let entry = entry?;
            let year = entry
                .file_name()
                .to_str()
                .and_then(|s| s.parse::<i32>().ok())
                .ok_or(InvalidYearFilenameError)?;
            Ok((year, entry.path()))
        })
        .try_filter(|(year, _)| future::ready(year >= &year_range.0 && year <= &year_range.1))
        .try_collect()
        .await?;

    let result = FuturesUnordered::from_iter(
        files
            .into_iter()
            .map(|(year, path)| deserialize_from_path(path).map_ok(move |data| (year, data))),
    );

    result.try_collect().await
}
