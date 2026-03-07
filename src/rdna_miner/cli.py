import typer
from pathlib import Path

from rdna_miner.workflow.context import Context
from rdna_miner.pipeline import run_pipeline
from rdna_miner.utils.db import DatabaseManager

app = typer.Typer(help="rDNA-miner: extract, assemble, and classify rDNA from long reads")


@app.command()
def run(
    input_fasta: Path = typer.Option(..., "--input", "-i", exists=True, file_okay=True, dir_okay=False, help="Input FASTA file"),
    output_dir: Path = typer.Option(..., "--out-dir", "-o", file_okay=False, dir_okay=True, help="Directory to store output"),
    db_dir: Path = typer.Option(..., "--db-dir", "-d", file_okay=False, dir_okay=True, help="Default database directory"),
    rfam_db: Path = typer.Option(None, "--rfam-db", file_okay=False, dir_okay=True, help="Path to Rfam database (optional override)"),
    pr2_db: Path = typer.Option(None, "--pr2-db", file_okay=False, dir_okay=True, help="Path to PR2 database (optional override)"),
    silva_db: Path = typer.Option(None, "--silva-db", file_okay=False, dir_okay=True, help="Path to SILVA database (optional override)"),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    platform: str = typer.Option("auto", "--platform", "-p", help="Sequencing platform (e.g., pacbio, nanopore, auto)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing outputs"),
):
    """
    Run the full rDNA-miner pipeline.
    """
    # Initialize context
    ctx = Context(input_fasta, output_dir, force=force)

    # Attach runtime configuration
    ctx.threads = threads
    ctx.platform = platform

    # Setup DatabaseManager with defaults and optional per-db overrides
    ctx.db_manager = DatabaseManager(cli_db_dir=db_dir)
    if rfam_db:
        ctx.db_manager.override_db("rfam", rfam_db)
    if pr2_db:
        ctx.db_manager.override_db("pr2", pr2_db)
    if silva_db:
        ctx.db_manager.override_db("silva", silva_db)
    
    run_pipeline(ctx)


if __name__ == "__main__":
    app()