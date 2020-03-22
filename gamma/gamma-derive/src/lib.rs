extern crate proc_macro;

use quote::{quote};
use proc_macro::{TokenStream};
use syn::{parse_macro_input, DeriveInput, Data};

#[proc_macro_derive(CountVariants)]
pub fn count_variants_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let len = match input.data {
        Data::Enum(enum_item) => enum_item.variants.len(),
        _ => panic!("CountVariants only works on enums"),
    };
    let name = &input.ident;
    let expanded = quote! {
        impl crate::traits::CountVariants for #name {
            const COUNT: usize = #len;
        }
    };
    expanded.into()
}
