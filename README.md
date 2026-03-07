# rDNA-miner
Extract, assemble and classify rDNA from long reads


## Install 


Clone this repository and enter the directory

```bash
git clone <repo-url>
cd rDNA-miner
```

Install a fresh conda environment using the provided iml

```bash
conda env create -f environment.yml
conda activate rdna-miner
```

or use mamba

```bash 
mamba env create -f environment.yml
```

Install the rona-miner python package with pip

```bash
pip install -e .
```

Quick test is dependencies are installed correctly


```bash
barrnap --help
flye --help
minimap2 --help
samtools --help
Rscript --version
```

## Usage


```
rdna-miner \
  -i reads.fasta \
  -o results \
  -d databases \
  -t 16
```
