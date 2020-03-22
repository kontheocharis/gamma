/// Ability to count the number of variants in an enum.
///
/// Meant to be used with `#[derive]`.
pub trait CountVariants {
    fn count_variants() -> usize;
}
