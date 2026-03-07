# rDNA-miner
extract, assemble and classify rDNA from long reads

conda env create -f environment.yml
conda activate rdna-miner

or 
mamba env create -f environment.yml


barrnap --help
flye --help
minimap2 --help
samtools --help
Rscript --version

rdna-miner run \
  -i reads.fasta \
  -o results \
  -d databases \
  -t 16

