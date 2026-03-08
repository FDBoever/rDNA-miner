import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    rdna_reads = ctx.require("rdna_reads")
    
    outdir = ctx.output_dir / "flye"
    assembly_fasta = outdir / "assembly.fasta"
    ctx.register("assembly", assembly_fasta)

    if ctx.artifact_exists_or_skip("assembly"):
        return
    
    outdir = ctx.output_dir / "flye"
    outdir.mkdir(parents=True, exist_ok=True)

    # platform-aware
    platform = getattr(ctx, "platform", "ont")
    flye_mode = "--nano-raw" if platform == "ont" else "--pacbio-raw"

    run_command(f"flye --meta {flye_mode} {rdna_reads} --out-dir {outdir} -t {ctx.threads}")
    
    if not assembly_fasta.exists():
        raise RuntimeError("Flye assembly failed: assembly.fasta not produced")
