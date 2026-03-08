from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow
from Bio import SeqIO
import hashlib
import matplotlib.patches as mpatches

# Optional categorical palette for main feature types
FEATURE_PALETTE = {
    "SSU": "#1f77b4",   # blue
    "LSU": "#ff7f0e",   # orange
    "tRNA": "#2ca02c",  # green
    "Intron": "#d62728" # red
}

def _feature_color(feature: str):
    """
    Deterministically generate a color from a feature name.
    Prioritizes categorical palette for main types.
    """
    for key, color in FEATURE_PALETTE.items():
        if key.lower() in feature.lower():
            return color

    # fallback: hash-based
    h = hashlib.md5(feature.encode()).hexdigest()
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return (r, g, b)

def plot_contigs(tsv_file, fasta_file, out_pdf):
    """
    Plot genomic features along contigs in a gene-style layout.
    """

    df = pd.read_csv(tsv_file, sep="\t")

    # Contig lengths
    contig_lengths = {rec.id: len(rec.seq) for rec in SeqIO.parse(fasta_file, "fasta")}
    contigs = sorted(contig_lengths.keys())

    # Figure setup
    fig_height = max(3, len(contigs) * 1.2)
    fig, ax = plt.subplots(figsize=(16, fig_height), dpi=300)

    y_positions = {}
    overlap_offsets = {}  # track feature stacking for each contig

    # draw contig baselines
    for i, contig in enumerate(contigs):
        y = len(contigs) - i
        y_positions[contig] = y
        overlap_offsets[contig] = []
        length = contig_lengths[contig]

        ax.plot([0, length], [y, y], linewidth=3, color="black")
        ax.text(-length * 0.01, y, contig, ha="right", va="center", fontsize=9)

    # draw features
    for _, row in df.iterrows():
        contig = row["query_name"]
        if contig not in y_positions:
            continue

        base_y = y_positions[contig]

        start = int(min(row["seq_from"], row["seq_to"]))
        end = int(max(row["seq_from"], row["seq_to"]))
        strand = row.get("strand", "+")
        feature = str(row["target_name"])

        width = end - start
        color = _feature_color(feature)

        # Determine vertical stacking to avoid overlap
        offsets = overlap_offsets[contig]
        y_offset = 0
        for o_start, o_end in offsets:
            if not (end < o_start or start > o_end):
                y_offset += 0.4
        offsets.append((start, end))

        y = base_y + y_offset if strand == "+" else base_y - y_offset

        # Draw gene-style arrow
        arrow = FancyArrow(
            start if strand == "+" else end,
            y,
            width if strand == "+" else -width,
            0,
            width=0.15,
            head_width=0.15,     # same as line width
            head_length=min(abs(width)*0.1, 50),  # small arrowhead
            length_includes_head=True,
            color=color,
            alpha=0.85
        )
        ax.add_patch(arrow)

        # Label above arrow
        label_pos = (start + end) / 2
        label_y = y + 0.35 if strand == "+" else y - 0.35
        ax.text(label_pos, label_y, feature, fontsize=7, ha="center", rotation=45)

    # Legend
    legend_patches = [mpatches.Patch(color=color, label=feat) for feat, color in FEATURE_PALETTE.items()]
    ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)

    # Formatting
    ax.set_xlabel("Position (bp)")
    ax.set_yticks([])
    ax.set_title("rDNA Miner: Contig Feature Map")
    max_len = max(contig_lengths.values())
    ax.set_xlim(-max_len * 0.02, max_len * 1.02)
    ax.grid(axis='x', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_pdf)
    plt.close()

def run(ctx):
    ctx.log_step("Plot contig feature map")

    cm_hits = ctx.require("cm_top_hits")
    assembly = ctx.require("assembly")

    out_dir = Path(ctx.require("cm_out"))
    out_dir.mkdir(parents=True, exist_ok=True)

    tsv_path = out_dir / "cm_filtered.tsv"
    cm_hits.to_csv(tsv_path, sep="\t", index=False)

    pdf_out = out_dir / "contig_map.pdf"

    plot_contigs(tsv_path, assembly, pdf_out)

    ctx.log(f"Contig map written to {pdf_out}")
    ctx.register("contig_map", pdf_out)