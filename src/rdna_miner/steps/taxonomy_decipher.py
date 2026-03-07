import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    ctx.log_step("Assign taxonomy with DECIPHER")
    out_dir = ctx.output_dir
    os.makedirs(out_dir, exist_ok=True)

    # Resolve databases via DatabaseManager
    pr2_db = ctx.db_manager.get_db("pr2")       # already returns Path to file
    silva_db = ctx.db_manager.get_db("silva")   # already returns Path to file

    decipher_script = os.path.join(os.path.dirname(__file__), "taxonomy_decipher/run-decipher.R")

    # Prepare CLI args for R script
    input_fasta = ctx.require("combined_SSU")
    threads = ctx.threads

    # You can pass both pr2 and silva paths, and let R script pick based on user option
    run_command(f"Rscript {decipher_script} {input_fasta} pr2 {pr2_db} {silva_db} {out_dir} --threads {threads}")