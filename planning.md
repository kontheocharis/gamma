# Data structure

FILES:
```
companies: { HashMap<String, usize>, // for dim1 } // indices have to be the same always

yearly/
    2017/
        {
            Array2<f32> {
                dim0: [ Date (reinterpreted num_days_from_ce() as f32), Col1, Col2, Col3, ... (Financial Fields) ]
                dim1: each company's data (Vec[f32])
                 -> empty (nonexistent) values are NaN
            }
        }
    2018/
        (see above)
    2019/
        (see above)
    2020/
        (see above)

daily/
    2017/
        {
            Array3<f32> {
                dim0: [ Col1, Col2, Col3, ... (Financial Fields) ]
                dim1: Vec[Date (reinterpreted num_days_from_ce() as f32)]
                dim2: each company's data (Vec[f32])
                 -> empty (nonexistent) values are NaN
            }
        }
    2018/
        (see above)
    2019/
        (see above)
    2020/
        (see above)
    
```


IN RUST:
```
companies: { HashMap<String, usize>, // for dim1 } // indices have to be the same always

yearly/
    {
        starting_year: usize,
        ending_year: usize,
        Array3<f32> {
            dim0: each year (indexed by (i - starting_year) as usize)
            dim1: [ Date (reinterpreted num_days_from_ce() as f32), Col1, Col2, Col3, ... (Financial Fields) ]
            dim2: each company's data (Vec[f32])
             -> empty (nonexistent) values are NaN
        }
    }

daily/
    {
        starting_date: NaiveDate,
        ending_date: NaiveDate,
        Array3<f32> {
            dim0: [ Col1, Col2, Col3, ... (Daily Financial Fields) ]
            dim1: each company (indexed by companies hashmap)
            dim2: each company's data at Date 
                (indexed by (num_days_from_ce(i) - num_days_from_ce(starting_date))) as usize)
             -> empty (nonexistent) values are NaN
        }
    }
    
```
