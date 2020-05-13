use ndarray::prelude::*;
use tch::{nn, nn::Module, nn::OptimizerConfig, Device};

pub trait Net<InputDim: Dimension, OutputDim: Dimension> {
    fn train<D>(&self, dataset: D, epochs: usize) -> f32
    where
        D: IntoIterator<Item = Array<f32, InputDim>>;

    fn test(&self, input: Array<f32, InputDim>) -> Array<f32, OutputDim>;
}

mod torch {
    use super::*;

    pub struct Network {
        var_store: nn::VarStore,
        network: Box<dyn nn::Module>,
    }

    impl Network {
        fn new<A>(layers: &[usize], activation: A) -> Self
        where
            A: Fn(&tch::Tensor) -> tch::Tensor,
        {
            let mut net = nn::seq();

            for (i, layer_window) in layers.iter().windows(2).enumerate() {
                net.add(nn::linear(
                    root / format!("layer{}", i),
                    layer_window[0],
                    layer_window[1],
                    Default::default(),
                ))
                .add_fn(|a| activation(a))
            }

            let var_store = nn::VarStore::new(Device::Cpu);
            let network = Box::new(net(&var_store.root()));

            Self { var_store, network }
        }
    }

    impl Net<Ix1, Ix1> for Network {
        fn train<D>(&self, dataset: D, epochs: usize) -> f32
        where
            D: IntoIterator<Item = Array<f32, InputDim>>
        {

        }

        fn test(&self, input: Array<f32, InputDim>) -> Array<f32, OutputDim>;
    }
}

// #[derive(Debug)]
// pub struct Network {
//     var_store: nn::VarStore,
//     input_size: usize,
//     network: Box<dyn nn::Module>,
// }

// impl NetworkBuilder {
//     fn construct(input_size: usize) -> Self {
//         let var_store = nn::VarStore::new(Device::Cpu);
//         let network = Box::new(make_tch_net(&var_store.root()));
//         Self { var_store, input_size }
//     }
// }

// const IMAGE_DIM: i64 = 784;
// const HIDDEN_NODES: i64 = 128;
// const LABELS: i64 = 10;

// fn net(vs: &nn::Path) -> impl Module {
// }

// pub fn run() -> anyhow::Result<()> {
//     let m = tch::vision::mnist::load_dir("data")?;
//     let vs = nn::VarStore::new(Device::Cpu);
//     let net = net(&vs.root());
//     let mut opt = nn::Adam::default().build(&vs, 1e-3).map_err(|e| e.compat())?;
//     for epoch in 1..200 {
//         let loss = net
//             .forward(&m.train_images)
//             .cross_entropy_for_logits(&m.train_labels);
//         opt.backward_step(&loss);
//         let test_accuracy = net
//             .forward(&m.test_images)
//             .accuracy_for_logits(&m.test_labels);
//         println!(
//             "epoch: {:4} train loss: {:8.5} test acc: {:5.2}%",
//             epoch,
//             f64::from(&loss),
//             100. * f64::from(&test_accuracy),
//         );
//     }
//     Ok(())
// }
