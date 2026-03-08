import os
from Bio import SeqIO
from rdna_miner.steps import cmscan, cm_analyse
from rdna_miner.steps import plot_contigs

import glob

def build_combined_ssu(cm_out, assembly_fasta, combined_file):
    # 1) Try FASTA outputs
    candidates = []
    for pat in ("*SSU*", "*ssu*"):
        candidates.extend(glob.glob(os.path.join(cm_out, pat)))
    fasta_like = [f for f in candidates if os.path.isfile(f) and f.lower().endswith((".fa", ".fasta", ".fna"))]

    if fasta_like:
        with open(combined_file, "w") as out:
            for f in sorted(fasta_like):
                with open(f) as fh:
                    out.write(fh.read())
        return sum(1 for line in open(combined_file) if line.startswith(">"))

    # 2) Fallback: parse tblout
    tblout = os.path.join(cm_out, "assembly.cmscan.tblout")
    if not os.path.exists(tblout):
        return 0

    seq_index = SeqIO.to_dict(SeqIO.parse(assembly_fasta, "fasta"))
    n_written = 0
    with open(combined_file, "w") as out, open(tblout) as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split()
            if len(parts) < 12:
                continue
            target = parts[1]
            if "SSU" not in target.lower():
                continue
            qname = parts[3]
            try:
                seq_from = int(parts[9])
                seq_to = int(parts[10])
            except ValueError:
                continue
            strand = parts[11]
            if qname not in seq_index:
                continue
            frag = seq_index[qname].seq[min(seq_from, seq_to)-1:max(seq_from, seq_to)]
            if strand == "-":
                frag = frag.reverse_complement()
            header = f"{qname}:{seq_from}-{seq_to}({strand})|{target}"
            out.write(f">{header}\n{frag}\n")
            n_written += 1
    return n_written


def run(ctx):
    # Get resolved Rfam database files via DatabaseManager
    rfam_files = ctx.db_manager.get_db("rfam")
    # get_db now returns a list of resolved files (CM and CLANIN)
    if isinstance(rfam_files, list):
        # pick CM and CLANIN based on suffix
        rfam_cm = next(f for f in rfam_files if f.suffix == ".cm")
        rfam_clanin = next(f for f in rfam_files if "clanin" in f.name.lower())
    else:
        # fallback if single file returned (shouldn't happen for Rfam)
        raise RuntimeError(f"Unexpected single file returned for Rfam database: {rfam_files}")

    assembly_fasta = ctx.require("assembly")
    cm_out = ctx.artifact("cm_out", "cm", "")
    combined_file = ctx.artifact("combined_SSU", "cm", ".fasta")

    if ctx.artifact_exists_or_skip("combined_SSU"):
        return

    os.makedirs(cm_out, exist_ok=True)

    #cmscan
    cmscan_done_flag = ctx.artifact_exists_or_skip("cmscan_done")
    if not cmscan_done_flag:
        cmscan.run(ctx, rfam_cm=rfam_cm, rfam_clanin=rfam_clanin)
        ctx.register("cmscan_done", True)

    #cmanalyse
    cm_analyse_done_flag = ctx.artifact_exists_or_skip("cm_top_hits")
    if not cm_analyse_done_flag:
        cm_analyse.run(ctx)
        ctx.register("cm_top_hits_done", True)

    # contig plots
    plots_done_flag = ctx.artifact_exists_or_skip("contig_plots")
    if not plots_done_flag:
        plot_contigs.run(ctx)
        ctx.register("contig_plots_done", True)

    #combined SSU
    combined_done_flag = ctx.artifact_exists_or_skip("combined_SSU")
    if not combined_done_flag:
        n_ssu = build_combined_ssu(cm_out, assembly_fasta, combined_file)
        if n_ssu == 0:
            ctx.log("WARN: No SSU sequences found, downstream DECIPHER output may be empty.")