import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    ctx.log_step("Assemble rDNA reads with Flye")
    assembly_fasta = ctx.artifact("assembly", "flye", ".fasta")
    if ctx.exists("assembly"):
        return

    rdna_reads = ctx.require("rdna_reads")
    outdir = ctx.output_dir / "flye"
    outdir.mkdir(parents=True, exist_ok=True)

    # platform-aware
    platform = getattr(ctx, "platform", "ont")
    flye_mode = "--nano-raw" if platform == "ont" else "--pacbio-raw"

    run_command(f"flye --meta {flye_mode} {rdna_reads} --out-dir {outdir} -t {ctx.threads}")

    assembly_path = os.path.join(outdir, "assembly.fasta")
    ctx.register("assembly", assembly_path)