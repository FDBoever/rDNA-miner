import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    ctx.log_step("Assign taxonomy with DECIPHER")

    taxonomy_file = ctx.artifact("taxonomy", "taxonomy", ".tsv")
     # Skip if artifact already exists
    if ctx.artifact_exists_or_skip("taxonomy"):
        return   

    out_dir = ctx.output_dir
    os.makedirs(out_dir, exist_ok=True)

    # Resolve databases via DatabaseManager
    pr2_db = ctx.db_manager.get_db("pr2")
    silva_db = ctx.db_manager.get_db("silva")

    decipher_script = os.path.join(os.path.dirname(__file__), "taxonomy_decipher/run-decipher.R")

    # Prepare CLI args for R script
    input_fasta = ctx.require("combined_SSU")
    threads = ctx.threads

    # You can pass both pr2 and silva paths, and let R script pick based on user option
    run_command(f"Rscript {decipher_script} {input_fasta} pr2 {pr2_db} {silva_db} {out_dir} --threads {threads}")
    ctx.register("taxonomy", taxonomy_file)