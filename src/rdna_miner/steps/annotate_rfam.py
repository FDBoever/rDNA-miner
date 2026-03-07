import os
from Bio import SeqIO
from rdna_miner.steps import cmscan, cm_analyse

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
    ctx.log_step("Annotate rDNA operons with Rfam/CMSCAN")

    assembly_fasta = ctx.require("assembly")
    cm_out = ctx.artifact("cm_out", "cm", "")
    os.makedirs(cm_out, exist_ok=True)

    # Run cmscan (Rfam annotation)
    cmscan.run(ctx)

    # Analyse CMSCAN output and extract top hits
    cm_analyse.run(ctx)

    # Build combined SSU FASTA for downstream steps
    combined_file = ctx.artifact("combined_SSU", "cm", ".fasta")
    n_ssu = build_combined_ssu(cm_out, assembly_fasta, combined_file)
    if n_ssu == 0:
        print(f"[WARN] No SSU sequences found, downstream DECIPHER output may be empty.")

    ctx.register("combined_SSU", combined_file)