use std::collections::HashMap;

use async_trait::async_trait;
use enum_iterator::IntoEnumIterator;
use ndarray::prelude::*;
use thiserror::Error;

use crate::fetching::{Fetch, StorageRepr};
use crate::financials::{self, Companies};

#[derive(Debug)]
struct MockFetcher;

#[derive(Error, Debug)]
#[error("Mock error")]
struct MockFetcherError;

#[async_trait(?Send)]
impl Fetch for MockFetcher {
    type StorageReprError = MockFetcherError;

    async fn to_storage_repr(&mut self) -> Result<StorageRepr, Self::StorageReprError> {
        let mut repr = StorageRepr {
            companies: Companies::new(),
            yearly: HashMap::new(),
            daily: HashMap::new(),
        };

        repr.companies.insert("AAPL".to_string(), 0);
        repr.companies.insert("MSFT".to_string(), 1);
        repr.companies.insert("GOOG".to_string(), 2);
        repr.companies.insert("SNAP".to_string(), 3);

        repr.yearly.insert(
            2018,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2019,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2020,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2021,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );
        repr.yearly.insert(
            2022,
            Array2::zeros((financials::YearlyField::VARIANT_COUNT, 4)),
        );

        repr.daily.insert(
            2017,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2018,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2019,
            Array3::zeros((365, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2020,
            Array3::zeros((366, financials::DailyField::VARIANT_COUNT, 4)),
        );
        repr.daily.insert(
            2021,
            Array3::zeros((366, financials::DailyField::VARIANT_COUNT, 4)),
        );

        Ok(repr)
    }
}
