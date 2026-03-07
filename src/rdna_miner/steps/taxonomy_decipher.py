import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    ctx.log_step("Assign taxonomy with DECIPHER")

    combined_fasta = ctx.require("combined_SSU")
    out_dir = ctx.output_dir
    os.makedirs(out_dir, exist_ok=True)

    pr2_db = ctx.pr2_db or os.path.join(ctx.db_dir, "pr2_version_5.0.0_SSU.decipher.trained.rds")
    silva_db = ctx.silva_db or os.path.join(ctx.db_dir, "SILVA_SSU_r138_2019.RData")

    decipher_script = os.path.join(os.path.dirname(__file__), "run_decipher.R")

    cmd = f"Rscript {decipher_script} {combined_fasta} pr2 {pr2_db} {silva_db} {out_dir}"
    run_command(cmd)

    # register the output TSV
    out_file = os.path.join(out_dir, "decipher_pr2.tsv")
    ctx.register("taxonomy", out_file)