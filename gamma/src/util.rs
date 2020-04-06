#[macro_export]
macro_rules! try_some {
    ($expr:expr) => {
        match $expr {
            std::result::Result::Ok(val) => val,
            std::result::Result::Err(err) => {
                return Some(std::result::Result::Err(std::convert::From::from(err)));
            }
        }
    };
    ($expr:expr,) => {
        try_some!($expr)
    };
}
