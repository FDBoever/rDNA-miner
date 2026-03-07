import os
import pandas as pd

def run(ctx):
    ctx.log_step("Compile taxonomy assignments")
    mapping_file = ctx.require("mapping")
    decipher_file = os.path.join(ctx.output_dir, "decipher_pr2.tsv")
    out_file = ctx.artifact("taxa_ssu_reads", "taxonomy", ".tsv")

    mapping = pd.read_csv(mapping_file, sep="\t")
    if os.path.exists(decipher_file):
        df = pd.read_csv(decipher_file, sep="\t")
    else:
        df = pd.DataFrame(columns=["query","confidence_long","taxon_long"])

    # normalize origin to merge with mapping RNAME
    df['origin'] = (
        df['query']
        .str.replace(r'_SSU.*','',regex=True)
        .str.split().str[0]
        .str.replace(r':\d+-\d+\([+-]\)\|.*$','',regex=True))

    contig_tax = (
        df.sort_values(['origin','confidence_long'], ascending=[True, False])
          .groupby('origin', as_index=False)
          .first())

    df_annotated_reads = (
        mapping[['QNAME','RNAME','FLAG','POS','MAPQ']]
        .merge(contig_tax, left_on='RNAME', right_on='origin', how='left')
        .dropna(subset=['taxon_long']))

    df_annotated_reads.to_csv(out_file, sep="\t", index=False)
    ctx.register("taxa_ssu_reads", out_file)