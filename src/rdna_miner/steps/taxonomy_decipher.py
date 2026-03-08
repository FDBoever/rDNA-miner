import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    taxonomy_file = ctx.artifact("taxonomy", "taxonomy", ".tsv")

    if ctx.artifact_exists_or_skip("taxonomy"):
        return   

    out_dir = ctx.output_dir
    os.makedirs(out_dir, exist_ok=True)

    pr2_db = ctx.db_manager.get_db("pr2")
    silva_db = ctx.db_manager.get_db("silva")

    decipher_script = os.path.join(os.path.dirname(__file__), "taxonomy_decipher/run-decipher.R")

    input_fasta = ctx.require("combined_SSU")
    threads = ctx.threads

    run_command(f"Rscript {decipher_script} {input_fasta} pr2 {pr2_db} {silva_db} {out_dir} --threads {threads}")
    ctx.register("taxonomy", taxonomy_file)