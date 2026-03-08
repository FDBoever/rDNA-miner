import os
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def extract_genus_and_type(taxon_long: str):
    """
    Extract genus name and origin type from taxon_long.
    Example:
    'Root;Eukaryota:mito;Obazoa:mito;...;Ophiostoma:mito;Ophiostoma_longirostellatum:mito'
    -> genus = 'Ophiostoma', origin_type = 'mito'
    """
    parts = taxon_long.split(";")
    if len(parts) < 2:
        return ("Unknown", "nuclear")
    
    genus_part = parts[-2]  # second-to-last
    if ":" in genus_part:
        genus, origin_type = genus_part.split(":", 1)
    else:
        genus, origin_type = genus_part, "nuclear"
    
    return genus, origin_type


def plot_genus_abundance(df: pd.DataFrame, out_pdf: Path, top_n=20):
    """
    Plot total read abundances per genus, stacked by origin_type.
    """
    # Group by genus and origin type
    counts = df.groupby(['genus', 'origin_type']).size().unstack(fill_value=0)

    # Collapse small genera into "Other"
    total_counts = counts.sum(axis=1)
    if len(total_counts) > top_n:
        top_genera = total_counts.nlargest(top_n).index
        counts_top = counts.loc[top_genera]
        counts_other = counts.drop(top_genera).sum()
        counts_top.loc["Other"] = counts_other
        counts = counts_top

    counts = counts.sort_values(total_counts.name if total_counts.name else counts.columns[0])

    # Plot stacked horizontal bar
    counts.plot(
        kind='barh',
        stacked=True,
        figsize=(10, max(4, 0.4 * len(counts))),
        color={"nuclear":"skyblue", "mito":"orange", "plastid":"green"},
        edgecolor="black"
    )

    plt.xlabel("Number of reads")
    plt.ylabel("Genus")
    plt.tight_layout()
    plt.savefig(out_pdf)
    plt.close()


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
        .dropna(subset=['taxon_long'])
    )

    # Extract genus and origin type
    df_annotated_reads[['genus', 'origin_type']] = df_annotated_reads['taxon_long'].apply(
        lambda x: pd.Series(extract_genus_and_type(x))
    )

    # Save annotated reads
    df_annotated_reads.to_csv(out_file, sep="\t", index=False)
    ctx.register("taxa_ssu_reads", out_file)

    # Generate genus abundance plot
    pdf_out = Path(ctx.require("cm_out")) / "genus_abundance.pdf"
    plot_genus_abundance(df_annotated_reads, pdf_out)
    ctx.log(f"Genus abundance plot written to {pdf_out}")
    ctx.register("genus_abundance_plot", pdf_out)