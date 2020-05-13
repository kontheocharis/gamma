use enum_iterator::IntoEnumIterator;
use std::convert::TryFrom;
use std::fmt::Debug;

pub trait IndexEnum:
    IntoEnumIterator + Into<usize> + TryFrom<usize> + Copy + Clone + PartialEq + Eq + Debug
{
    fn index(&self) -> usize {
        (*self).into()
    }
}

pub type CompanyId = usize;
