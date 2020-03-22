/// Implements `From<$from>` for `$enum` by constructing `$enum::$variant(value.into())`, where
/// `value: $from`.
#[macro_export]
macro_rules! impl_from {
    ($enum:ty { $($variant:ident => {$($from:ty),*}),* }) => {
        $(
            $(
                impl From<$from> for $enum {
                    fn from(value: $from) -> Self {
                        Self::$variant(value.into())
                    }
                }
            )*
        )*
    };
}
