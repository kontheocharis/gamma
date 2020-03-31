use std::collections::HashMap;
use std::convert::TryFrom;
use std::error::Error;
use std::iter;
use std::path::{Path, PathBuf};

use async_trait::async_trait;
use chrono::{Datelike, NaiveDate};
use futures::prelude::*;
use ndarray::{s, Array1, Array2, Array3, ArrayView1, ArrayView2, Axis};
use num_enum::{IntoPrimitive, TryFromPrimitive};
use thiserror::Error;
use tokio::fs;
use tokio::io::AsyncWriteExt;

use crate::traits::CountVariants;

#[repr(usize)]
#[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
pub enum YearlyField {
    CashShortTermInvestments,
    Ppe,
    TotalLiabilities,
    TotalAssets,
    TotalDebt,
    TotalShareholdersEquity,
    TotalOutstandingShares,
    Eps,
    SharePriceAtReport,
    CashFlow,
}

#[repr(usize)]
#[derive(CountVariants, Debug, IntoPrimitive, TryFromPrimitive, Copy, Clone)]
pub enum DailyField {
    HighSharePrice,
    LowSharePrice,
    Volume,
}

#[derive(Debug)]
pub struct Financials {
    companies: HashMap<String, usize>,
    yearly_data: Array3<f32>, // Axis(0): year, Axis(1): x::Field, Axis(2): company
    daily_data: Array3<f32>,  // Axis(0): day, Axis(1): x::Field, Axis(2): company
}

#[derive(Debug, Clone)]
pub struct LoadOptions {
    pub yearly_min: i32,
    pub yearly_max: i32,
    pub daily_min: NaiveDate,
    pub daily_max: NaiveDate,
}

#[derive(Error, Debug)]
#[error("Invalid options: {0}")]
pub struct InvalidOptionsError(String);

impl LoadOptions {
    pub fn ensure_ok(&self) -> Result<(), InvalidOptionsError> {
        if self.yearly_min < self.yearly_max && self.daily_min < self.daily_max {
            Ok(())
        } else {
            Err(InvalidOptionsError("invalid date ranges".to_string()))
        }
    }
}

impl<'a> Financials
where
    Self: 'a,
{
    pub const TIME_AXIS: Axis = Axis(0);
    pub const FIELD_AXIS: Axis = Axis(1);
    pub const COMPANY_AXIS: Axis = Axis(2);

    pub fn from_repr(
        repr: fetcher::StorageRepr,
        options: &LoadOptions,
    ) -> Result<Financials, anyhow::Error> {
        options.ensure_ok()?;

        Self::from_repr_unchecked(repr, options)
    }

    pub async fn from_path<P: AsRef<Path>>(
        path: P,
        options: &LoadOptions,
    ) -> Result<Financials, anyhow::Error> {
        let path_ref = path.as_ref();

        options.ensure_ok()?;

        let repr = fetcher::StorageRepr::load_from_path(path_ref).await?;

        Self::from_repr_unchecked(repr, options)
    }

    fn from_repr_unchecked(
        repr: fetcher::StorageRepr,
        options: &LoadOptions,
    ) -> Result<Financials, anyhow::Error> {
        let no_of_companies = repr.companies.len();

        let mut yearly_data = Array3::from_elem(
            (
                (options.yearly_max - options.yearly_min + 1) as usize,
                YearlyField::COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        for year in options.yearly_min..=options.yearly_max {
            let data = repr.yearly.get(&year).ok_or(InvalidOptionsError(format!(
                "year {} not found for yearly data",
                year
            )))?;

            yearly_data
                .slice_mut(s![(year - options.yearly_min) as usize, .., ..])
                .assign(&data);
        }

        let mut daily_data = Array3::from_elem(
            (
                (options.daily_max.num_days_from_ce() - options.daily_min.num_days_from_ce() + 1)
                    as usize,
                DailyField::COUNT,
                no_of_companies,
            ),
            std::f32::NAN,
        );

        let (daily_min_year, daily_max_year) = (options.daily_min.year(), options.daily_max.year());

        let mut curr_offset = 0;
        for year in daily_min_year..=daily_max_year {
            let data = repr.daily.get(&year).ok_or(InvalidOptionsError(format!(
                "year {} not found for daily data",
                year
            )))?;

            let days_in_year = NaiveDate::from_ymd(year, 12, 31).ordinal() as usize;

            let day_min = if year == daily_min_year {
                options.daily_min.ordinal0() as usize
            } else {
                0
            };

            let day_max = if year == daily_max_year {
                options.daily_max.ordinal0() as usize
            } else {
                (days_in_year - 1) as usize
            };

            daily_data
                .slice_mut(s![
                    (curr_offset)..(curr_offset + (day_max - day_min) + 1),
                    ..,
                    ..,
                ])
                .assign(&data.slice(s![day_min..(day_max + 1), .., ..]));

            curr_offset += day_max - day_min + 1;
        }

        Ok(Financials {
            companies: repr.companies,
            yearly_data,
            daily_data,
        })
    }
}

pub mod fetcher {
    use super::*;
    use anyhow::anyhow;
    use futures::stream::{StreamExt, TryStreamExt};
    use tokio::fs::{self, File};
    use tokio::io::AsyncReadExt;

    const NPY_SAVE_FILE: &str = "data.npy";
    const HASHMAP_SAVE_FILE: &str = "companies.bin";

    const YEARLY_FOLDER: &str = "yearly";
    const DAILY_FOLDER: &str = "daily";
    const COMPANY_FILE: &str = "companies";

    #[derive(Debug)]
    pub struct StorageRepr {
        pub companies: HashMap<String, usize>,
        pub yearly: HashMap<i32, Array2<f32>>,
        pub daily: HashMap<i32, Array3<f32>>, // Axis(0): 0-365 or 0-364
    }

    #[derive(Error, Debug)]
    #[error(
        "Missing items: folders '{}' and '{}', and file '{}' need to exist in path",
        YEARLY_FOLDER,
        DAILY_FOLDER,
        COMPANY_FILE
    )]
    pub struct MissingFoldersError;

    #[derive(Error, Debug)]
    #[error("Files in path subfolders must be in form 2018, 2019, 2020, etc.")]
    pub struct InvalidYearFilenameError;

    impl StorageRepr {
        pub async fn load_from_path<P: AsRef<Path>>(path: P) -> Result<StorageRepr, anyhow::Error> {
            let path_ref = path.as_ref();

            let (yearly_folder, daily_folder, company_file) = (
                path_ref.join(YEARLY_FOLDER),
                path_ref.join(DAILY_FOLDER),
                path_ref.join(COMPANY_FILE),
            );

            if !yearly_folder.exists() || !daily_folder.exists() || !company_file.exists() {
                return Err(MissingFoldersError)?;
            }

            async fn deserialize_from_path<'a, T: serde::de::DeserializeOwned>(
                path: &PathBuf,
            ) -> Result<T, anyhow::Error> {
                let mut data = Vec::new();
                File::open(path).await?.read_to_end(&mut data).await?;
                Ok(bincode::deserialize(&data)?)
            }

            macro_rules! get_time_series_for {
                ($folder:expr, $return_type:ty) => {
                    fs::read_dir($folder)
                        .await?
                        .then(
                            async move |entry| -> Result<(i32, $return_type), anyhow::Error> {
                                let entry = entry?;
                                let year = str::parse::<i32>(
                                    &entry
                                        .file_name()
                                        .into_string()
                                        .map_err(|_| InvalidYearFilenameError)?,
                                )
                                .map_err(|_| InvalidYearFilenameError)?;

                                Ok((year, deserialize_from_path(&entry.path()).await?))
                            },
                        )
                        .try_collect::<HashMap<i32, $return_type>>()
                };
            }

            let companies_fut = deserialize_from_path::<HashMap<String, usize>>(&company_file);
            let yearly_fut = get_time_series_for!(&yearly_folder, Array2<f32>);
            let daily_fut = get_time_series_for!(&daily_folder, Array3<f32>);

            let (companies, yearly, daily) =
                future::try_join3(companies_fut, yearly_fut, daily_fut).await?;

            Ok(StorageRepr {
                companies,
                yearly,
                daily,
            })
        }

        pub async fn save_to_path<P: AsRef<Path>>(&self, path: P) -> Result<(), anyhow::Error> {
            let path_ref = path.as_ref();

            // Create paths needed
            future::try_join(
                fs::create_dir_all(path_ref.join(YEARLY_FOLDER)),
                fs::create_dir_all(path_ref.join(DAILY_FOLDER)),
            )
            .await?;

            let path_for = |year: i32, prefix: &str| path_ref.join(prefix).join(year.to_string());

            macro_rules! files_for {
                ($prop:ident, $folder:expr) => {
                    self.$prop
                        .iter()
                        .map(|(&year, array)| (path_for(year, $folder), bincode::serialize(array)))
                };
            }

            let yearly_files = files_for!(yearly, YEARLY_FOLDER);
            let daily_files = files_for!(daily, DAILY_FOLDER);

            let company_file = iter::once((
                path_ref.join(COMPANY_FILE),
                bincode::serialize(&self.companies),
            ));

            future::try_join_all(yearly_files.chain(daily_files).chain(company_file).map(
                |(path, data)| {
                    fs::File::create(path)
                        .map_err(anyhow::Error::new)
                        .and_then(async move |mut file| Ok(file.write_all(data?.as_ref()).await?))
                },
            ))
            .await?;

            Ok(())
        }
    }

    #[derive(Error, Debug)]
    #[error("Fetcher error: {0}")]
    pub struct FetcherError<T: Error>(T);

    #[async_trait]
    pub trait Fetcher {
        type StorageReprError: Error + Send + Sync + 'static;

        async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::StorageReprError>; // do not call this directly from outside

        async fn load_financials(
            &mut self,
            options: &LoadOptions,
        ) -> Result<Financials, anyhow::Error> {
            Financials::from_repr(self.to_storage_repr().map_err(FetcherError).await?, options)
        }

        async fn save_repr_to_path<P: AsRef<Path> + Send>(
            &mut self,
            path: P,
        ) -> Result<(), anyhow::Error> {
            self.to_storage_repr()
                .await
                .map_err(FetcherError)?
                .save_to_path(path)
                .await
        }
    }
}
