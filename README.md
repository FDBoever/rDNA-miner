# rDNA-miner
Extract, assemble and classify rDNA from long reads

## Install 

Clone this repository and enter the directory

```bash
git clone <repo-url>
cd rDNA-miner
```

Install a fresh conda environment using the provided yml file

```bash
conda env create -f environment.yml
conda activate rdna-miner
```

or use mamba

```bash 
mamba env create -f environment.yml
```

Install the rdna-miner python package with pip

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

## Quickstart

1. **install required databases (if not already avialable on your system)**

```bash
rdna-miner db install all --db-dir ~/.rdna-miner/db
```

2. **Run pipeline**

```bash
rdna-miner run \
  --input input.fasta \
  --out-dir ./rDNA-out \
  --db-dir ~/.rdna-miner/db \
  --threads 4 \
  --platform pacbio
```

## Usage

```bash
rdna-miner run \
  --input <input_fasta> \
  --out-dir <output_directory> \
  --db-dir <database_directory> \
  [--rfam-db <rfam_path>] \
  [--pr2-db <pr2_path>] \
  [--silva-db <silva_path>] \
  [--threads N] \
  [--platform PLATFORM] \
  [--force]
```

#### Required options

| Option | Description |
|--------|-------------|
| --input, -i | Path to input FASTA file containing reads. |
| --out-dir, -o | Output directory for pipeline results. |
| --db-dir, -d | Directory containing the databases (Rfam, PR2, SILVA). |

#### Optional database overrides
In case rfam/pr2/silva are already on your system, please point to them.

| Option | Description |
|--------|-------------|
| --rfam-db | Override path for Rfam database. |
| --pr2-db | Override path for PR2 database. |
| --silva-db | Override path for SILVA database. |


#### Other options

| Option | Default | Description |
|--------|---------|-------------|
| --threads, -t | 4 | Number of threads to use. |
| --platform, -p | auto | Sequencing platform (`pacbio`, `nanopore`, `auto`). |
| --force, -f | False | Overwrite existing files |

**example**

```bash
rdna-miner run \
  --input sample.fasta \
  --out-dir ./sample-out-rdna \
  --db-dir ~/.rdna-miner/db \
  --threads 8 \
  --platform pacbio \
  --force
```

or specifying local paths to databases manually

```bash
rdna-miner run \
  --input sample.fasta \
  --out-dir ./sample-out-rdna \
  --rfam-db /custom_location/rfam \
  --pr2-db /custom_location/pr2 \
  --silva-db /custom_location/silva \
  --threads 6 \
  --platform nanopore
```

---

### Databases

#### Install databases

```bash
rdna-miner db install <db> [--db-dir <path>] [--force]
```

- `<db>`: `rfam`, `silva`, `pr2`, or `all`  
- `--db-dir, -d`: Directory for database installation (default: `~/.rdna-miner/db`)  
- `--force`: Force re-download even if database exists 

**Examples**

Install a single database:

```bash
rdna-miner db install pr2
```

Install all databases:

```bash
rdna-miner db install all --force
```

#### Check database status

```bash
rdna-miner db status [--db-dir <path>]
```

Displays which databases are installed and which are missing.


## References

rDNA-miner relies on a number of bioinformatics tools and databases. If you use rDNA-miner, please consider citing these tools where appropriate:

| Tool | Purpose                                       | Citation / URL                                        |
| --------------- | --------------------------------------------- | ----------------------------------------------------- |
| **barrnap**     | rRNA prediction from genome sequences         | [Barrnap GitHub](https://github.com/tseemann/barrnap) |
| **flye**        | Long-read genome assembler                    | Kolmogorov et al., *Nat Biotechnol* 2019              |
| **minimap2**    | Sequence mapping / alignment                  | Li, *Bioinformatics*, 2018                            |
| **samtools**    | Sequence alignment processing                 | Li et al., *Bioinformatics*, 2009                     |
| **infernal**    | RNA homology searches                         | Nawrocki & Eddy, *Bioinformatics*, 2013               |
| **DECIPHER**    | Taxonomic assignment / sequence analysis in R | Wright, *Bioinformatics*, 2016                        |
| **seqkit**      | FASTA/Q processing toolkit                    | Shen et al., *PLoS ONE*, 2016                         |
| **pigz**        | Parallel gzip compression                     | [pigz GitHub](https://github.com/madler/pigz)         |


Databases used:

| Database      | Purpose                              | Citation / URL                                                                     |
| ------------- | ------------------------------------ | ---------------------------------------------------------------------------------- |
| **PR2**       | Protist Ribosomal Reference database | Guillou et al., *Nucleic Acids Res*, 2013; [PR2 Website](https://pr2-database.org) |
| **SILVA SSU** | Ribosomal RNA reference database     | Quast et al., *Nucleic Acids Res*, 2013; [SILVA Website](https://www.arb-silva.de) |
| **Rfam**      | RNA family database                  | Kalvari et al., *Nucleic Acids Res*, 2018; [Rfam Website](https://rfam.org)        |
