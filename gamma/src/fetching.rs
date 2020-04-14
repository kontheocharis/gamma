use std::collections::HashMap;
use std::fmt::{Debug, Display};
use std::iter::{self, FromIterator};
use std::path::{Path, PathBuf};

use async_trait::async_trait;
use futures::prelude::*;
use futures::stream::{StreamExt, TryStreamExt};
use ndarray::{Array2, Array3};
use thiserror::Error;
use tokio::fs::{self, File};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::try_join;

use crate::financials::{Financials, Options as FinancialsOptions, Companies};

const NPY_SAVE_FILE: &str = "data.npy";
const HASHMAP_SAVE_FILE: &str = "companies.bin";

const YEARLY_FOLDER: &str = "yearly";
const DAILY_FOLDER: &str = "daily";
const COMPANY_FILE: &str = "companies";

#[derive(Debug)]
pub struct StorageRepr {
    pub companies: Companies,
    pub yearly: HashMap<i32, Array2<f32>>, // Axis(0): Columns, Axis(1): Companies
    pub daily: HashMap<i32, Array3<f32>>, // Axis(0): 0-365 or 0-364, Axis(1): Columns, Axis(2): Companies
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
        let path_ref = path.as_ref();

        let (yearly_folder, daily_folder, company_file) = (
            path_ref.join(YEARLY_FOLDER),
            path_ref.join(DAILY_FOLDER),
            path_ref.join(COMPANY_FILE),
        );

        if !yearly_folder.exists() || !daily_folder.exists() || !company_file.exists() {
            return Err(MissingFoldersError)?;
        }

        async fn deserialize_from_path<T: serde::de::DeserializeOwned>(
            path: &PathBuf,
        ) -> anyhow::Result<T> {
            let mut file = File::open(path).await?;
            // let mut data = Vec::with_capacity(file.metadata().await?.len() as usize);
            let mut data = Vec::new();
            file.read_to_end(&mut data).await?;
            Ok(bincode::deserialize(&data)?)
        }

        async fn get_time_series_for<T: serde::de::DeserializeOwned>(
            folder: &PathBuf,
            year_range: (i32, i32),
        ) -> anyhow::Result<HashMap<i32, T>> {
            fs::read_dir(folder)
                .await?
                .map(|entry| {
                    let entry = entry?;
                    let year = entry
                        .file_name()
                        .to_str()
                        .and_then(|s| s.parse::<i32>().ok())
                        .ok_or(InvalidYearFilenameError)?;
                    Ok((year, entry.path()))
                })
                .try_filter(|(year, _)| {
                    future::ready(year >= &year_range.0 && year <= &year_range.1)
                })
                .and_then(async move |(year, path)| {
                    deserialize_from_path(&path)
                        .map_ok(|data| (year, data))
                        .await
                })
                .try_collect()
                .await
        }

        let companies_fut = deserialize_from_path::<Companies>(&company_file);
        let yearly_fut = get_time_series_for::<Array2<f32>>(&yearly_folder, yearly_years);
        let daily_fut = get_time_series_for::<Array3<f32>>(&daily_folder, daily_years);

        let (companies, yearly, daily) =
            future::try_join3(companies_fut, yearly_fut, daily_fut).await?;

        Ok(StorageRepr {
            companies,
            yearly,
            daily,
        })
    }

    pub async fn save_to_path<P: AsRef<Path>>(&self, path: P) -> anyhow::Result<()> {
        let path_ref = path.as_ref();

        // Create paths needed
        try_join!(
            fs::create_dir_all(path_ref.join(YEARLY_FOLDER)),
            fs::create_dir_all(path_ref.join(DAILY_FOLDER)),
        )?;

        let yearly_iter = self
            .yearly
            .iter()
            .map(|(year, array)| (year, bincode::serialize(array), YEARLY_FOLDER));

        let daily_iter = self
            .daily
            .iter()
            .map(|(year, array)| (year, bincode::serialize(array), DAILY_FOLDER));

        let company_file = iter::once((
            path_ref.join(COMPANY_FILE),
            bincode::serialize(&self.companies),
        ));

        future::try_join_all(
            yearly_iter
                .chain(daily_iter)
                .map(|(year, data, folder)| (path_ref.join(folder).join(year.to_string()), data))
                .chain(company_file)
                .map(|(path, data)| {
                    fs::File::create(path)
                        .map_err(anyhow::Error::new)
                        .and_then(async move |mut file| Ok(file.write_all(data?.as_ref()).await?))
                }),
        )
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
