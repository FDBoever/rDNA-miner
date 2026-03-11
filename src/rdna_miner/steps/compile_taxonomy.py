import os
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


ORGANELLE_SUFFIXES = {
    "nucl": "nucleomorph",
    "plas": "plastid",
    "apic": "apicoplast",
    "chrom": "chromatophore",
    "mito": "mitochondrion",
}

ORIGIN_COLORS = {
    "cellular": "grey",
    "nuclear": "skyblue",
    "mito": "orange",
    "plas": "green",
    "nucl": "purple",
    "apic": "red",
    "chrom": "brown",
}

def extract_genus_and_type(taxon_long: str):
    """
    Extract genus and origin type from PR2 taxonomy string.

    Example:
    Root;Eukaryota:mito;...;Ophiostoma:mito;Ophiostoma_longirostellatum:mito
    -> genus='Ophiostoma', origin_type='mito'
    """

    parts = taxon_long.split(";")
    if len(parts) < 2:
        return ("Unknown", "nuclear")

    genus_part = parts[-2]

    if ":" in genus_part:
        genus, suffix = genus_part.split(":", 1)

        # validate suffix
        if suffix in ORGANELLE_SUFFIXES:
            origin_type = suffix
        else:
            origin_type = "nuclear"

    else:
        genus = genus_part
        origin_type = "nuclear"

    return genus, origin_type


def plot_genus_abundance(df: pd.DataFrame, out_pdf: Path, top_n=20):
    """
    Plot total read abundances per genus, stacked by origin_type.
    Facet by domain (Bacteria / Eukaryota).
    """

    domains = ["Bacteria", "Eukaryota"]

    fig, axes = plt.subplots(
        nrows=len(domains),
        ncols=1,
        figsize=(10, 6),
        sharex=True)

    if len(domains) == 1:
        axes = [axes]

    for ax, domain in zip(axes, domains):

        df_dom = df[df["domain"].str.replace(r":.*", "", regex=True) == domain]

        if df_dom.empty:
            ax.set_title(domain)
            ax.axis("off")
            continue

        counts = (
            df_dom.groupby(["genus", "origin_type"])
            .size()
            .unstack(fill_value=0))

        total_counts = counts.sum(axis=1)

        if len(total_counts) > top_n:
            top_genera = total_counts.nlargest(top_n).index
            counts_top = counts.loc[top_genera]
            counts_other = counts.drop(top_genera).sum()
            counts_top.loc["Other"] = counts_other
            counts = counts_top

        counts = counts.loc[counts.sum(axis=1).sort_values().index]

        counts.plot(
            kind="barh",
            stacked=True,
            ax=ax,
            color=ORIGIN_COLORS,
            edgecolor="black")

        ax.set_title(domain)
        ax.set_ylabel("Genus")

    axes[-1].set_xlabel("Number of reads")

    plt.tight_layout()
    plt.savefig(out_pdf)
    plt.close()

def plot_taxon_abundance(df, rank, out_pdf, top_n=20):

    domains = ["Bacteria", "Eukaryota"]

    fig, axes = plt.subplots(
        nrows=len(domains),
        ncols=1,
        figsize=(10, 6),
        sharex=True
    )

    if len(domains) == 1:
        axes = [axes]

    for ax, domain in zip(axes, domains):

        df_dom = df[df["domain_clean"] == domain]

        if df_dom.empty:
            ax.axis("off")
            continue

        counts = (
            df_dom.groupby([rank, "origin_type"])
            .size()
            .unstack(fill_value=0)
        )

        totals = counts.sum(axis=1)

        if len(totals) > top_n:
            top = totals.nlargest(top_n).index
            counts_top = counts.loc[top]
            counts_other = counts.drop(top).sum()
            counts_top.loc["Other"] = counts_other
            counts = counts_top

        counts = counts.loc[counts.sum(axis=1).sort_values().index]

        counts.plot(
            kind="barh",
            stacked=True,
            ax=ax,
            color=ORIGIN_COLORS,
            edgecolor="black"
        )

        ax.set_title(domain)
        ax.set_ylabel(rank.capitalize())

    axes[-1].set_xlabel("Number of reads")

    plt.tight_layout()
    plt.savefig(out_pdf)
    plt.close()

def run(ctx):
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

    # extract genus and origin type
    df_annotated_reads[['genus', 'origin_type']] = df_annotated_reads['taxon_long'].apply(
        lambda x: pd.Series(extract_genus_and_type(x))
    )

    df_annotated_reads["domain_clean"] = df_annotated_reads["domain"].str.replace(r":.*", "", regex=True)

    df_annotated_reads.loc[
        df_annotated_reads["domain_clean"] != "Eukaryota",
        "origin_type"
    ] = "cellular" 


    df_annotated_reads.to_csv(out_file, sep="\t", index=False)
    ctx.register("taxa_ssu_reads", out_file)

    # generate abundance plot
    pdf_out = Path(ctx.require("cm_out")) / "genus_abundance.pdf"
    plot_genus_abundance(df_annotated_reads, pdf_out)
    ctx.log(f"Genus abundance plot written to {pdf_out}")
    ctx.register("genus_abundance_plot", pdf_out)

    tax_ranks = ["class", "order", "family", "genus"]

    plot_dir = Path(ctx.require("cm_out"))

    for rank in tax_ranks:

        pdf_out = plot_dir / f"{rank}_abundance.pdf"

        plot_taxon_abundance(
            df_annotated_reads,
            rank=rank,
            out_pdf=pdf_out
        )

    ctx.log(f"{rank} abundance plot written to {pdf_out}")