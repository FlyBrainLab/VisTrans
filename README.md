# Visual Transduction Library for FlyBrainLab

This library provides executable neural circuit implementation of the retina of the fruit fly,
including the visual transduction process. It is largely based on [Neurokernel Request for Comment #3](http://dx.doi.org/10.5281/zenodo.30036), and the implementation in the [retina](https://github.com/neurokernel/retina) package for [Neurokernel](https://neurokernel.github.io).
This library is meant to work within [FlyBrainLab](https://flybrainlab.fruitflybrain.org), with visualization of biological data and an interactive circuit diagram.

## Installation

Clone the repository and install by
```bash
python setup.py install
```

To work properly, it must be installed in the environment where you launch FlyBrainLab and in the server-side backend.


## Basic Usage

At the backend, start a NeuroArch server with dataset retina, and a NLP server with dataset retina and app name medulla. Then configure FlyBrainLab to connect to the FFBO Process hosting the retina dataset. In Neu3D settings, set `minSomaRadius` to 0.

To load the setup in the NeuroArch database, run the notebook [create_retina.ipynb](notebooks/create_retina.ipynb).

To explore the retina circuit, an example is given by the notebook [explore_retina.ipynb](notebooks/explore_retina.ipynb).


