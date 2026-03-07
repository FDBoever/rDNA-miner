import os
from pathlib import Path
from rdna_miner.workflow.context import Context
from rdna_miner.utils.cmd import run_command

def gff_has_records(gff_file: Path) -> bool:
    """Return True if GFF has any non-comment lines besides the header."""
    with open(gff_file) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            return True
    return False

def run(ctx):
    ctx.log_step("Run Barrnap")

    bac_gff = ctx.artifact("barrnap_bac", "barrnap", ".gff")
    euk_gff = ctx.artifact("barrnap_euk", "barrnap", ".gff")
    combined_gff = ctx.artifact("barrnap_combined", "barrnap", ".gff")

    if ctx.artifact_exists_or_skip("barrnap_combined"):
        return
    
    ctx.log(f"Running Barrnap for bacteria: {ctx.fasta} -> {bac_gff}")
    run_command(f"barrnap --kingdom bac --threads {ctx.threads} {ctx.fasta} --reject 0.2 > {bac_gff}")

    ctx.log(f"Running Barrnap for eukaryotes: {ctx.fasta} -> {euk_gff}")
    run_command(f"barrnap --kingdom euk --threads {ctx.threads} {ctx.fasta} --reject 0.2 > {euk_gff}")

    ctx.log(f"Combining GFFs -> {combined_gff}")
    run_command(f"cat {bac_gff} {euk_gff} > {combined_gff}")

    if not gff_has_records(combined_gff):
        ctx.terminate_pipeline("No rDNA hits found in the input FASTA")
        return