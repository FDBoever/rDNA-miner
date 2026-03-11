import typer
from pathlib import Path

from rdna_miner.workflow.context import Context
from rdna_miner.utils.db import DatabaseManager
from rdna_miner.utils.logging_utils import section, info, warn
import platform
import datetime

from rdna_miner.pipeline import build_long_read_pipeline
from rdna_miner.pipeline import build_assembly_pipeline
from rdna_miner.pipeline import run_pipeline

def print_header(start_time):
    from importlib.metadata import version
    width = 70
    v = version("rdna-miner")

    print()
    print("=" * width)
    print("rDNA-miner".center(width))
    print(f"version {v}".center(width))
    print("Extract, assemble, and classify rDNA from long reads".center(width))
    print("=" * width)
    print(f"Run started: {start_time.isoformat(timespec='seconds')}")
    print(f"Python: {platform.python_version()}")
    print("=" * width)

def format_timedelta(td: "datetime.timedelta") -> str:
    total_seconds = td.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds:03d}"

app = typer.Typer(help="rDNA-miner: extract, assemble, and classify rDNA from long reads", 
                  add_completion=False,
                  invoke_without_command=True)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    rDNA-miner: extract, assemble, and classify rDNA from long reads
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command("long-read")
def run(
    input_fasta: Path = typer.Option(..., "--input", "-i", exists=True, file_okay=True, dir_okay=False, help="Input FASTA file"),
    output_dir: Path = typer.Option(..., "--out-dir", "-o", file_okay=False, dir_okay=True, help="Directory to store output"),
    db_dir: Path = typer.Option(None, "--db-dir", "-d", file_okay=False, dir_okay=True, help="Default database directory"),
    rfam_db: Path = typer.Option(None, "--rfam-db", file_okay=False, dir_okay=True, help="Path to Rfam database (optional override)"),
    pr2_db: Path = typer.Option(None, "--pr2-db", file_okay=False, dir_okay=True, help="Path to PR2 database (optional override)"),
    silva_db: Path = typer.Option(None, "--silva-db", file_okay=False, dir_okay=True, help="Path to SILVA database (optional override)"),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    platform: str = typer.Option("auto", "--platform", "-p", help="Sequencing platform (e.g., pacbio, nanopore, auto)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing outputs"),
):
    """
    Run the full rDNA-miner pipeline.

    Extracts rDNA reads, assembles them, and performs taxonomic classification.
    """
    start_time = datetime.datetime.now()
    print_header(start_time)

    info("loading packages")

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
    
    pipeline = build_long_read_pipeline()
    run_pipeline(ctx, pipeline)
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print("-" * 70)
    print(f"Finished: {end_time.isoformat(timespec='seconds')}")
    print(f"Total runtime: {format_timedelta(duration)}")
    print("-" * 70)

#---------------------------------#

@app.command()
def assembly(
    assembly_fasta: Path = typer.Option(..., "--input", "-i", exists=True, help="Input assembly FASTA"),
    output_dir: Path = typer.Option(..., "--out-dir", "-o", help="Directory to store output"),
    db_dir: Path = typer.Option(None, "--db-dir", "-d"),
    rfam_db: Path = typer.Option(None, "--rfam-db"),
    pr2_db: Path = typer.Option(None, "--pr2-db"),
    silva_db: Path = typer.Option(None, "--silva-db"),
    threads: int = typer.Option(4, "--threads", "-t"),
    force: bool = typer.Option(False, "--force", "-f"),
):
    """
    Run rDNA-miner starting from an assembly.
    """

    start_time = datetime.datetime.now()
    print_header(start_time)

    ctx = Context(assembly_fasta, output_dir, force=force)
    ctx.threads = threads
    ctx.register("assembly", assembly_fasta)

    ctx.db_manager = DatabaseManager(cli_db_dir=db_dir)

    if rfam_db:
        ctx.db_manager.override_db("rfam", rfam_db)
    if pr2_db:
        ctx.db_manager.override_db("pr2", pr2_db)
    if silva_db:
        ctx.db_manager.override_db("silva", silva_db)

    
    # build assembly pipeline
    pipeline = build_assembly_pipeline()
    run_pipeline(ctx, pipeline)

    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print("-" * 70)
    print(f"Finished: {end_time.isoformat(timespec='seconds')}")
    print(f"Total runtime: {format_timedelta(duration)}")
    print("-" * 70)

#-----------------------------------
# manage databses
#-----------------------------------

db_app = typer.Typer(help="manage rDNA-miner databases")
app.add_typer(db_app, name="db")

@db_app.command("install")
def db_install(
    db: str = typer.Argument(..., help="Database to install (rfam, silva, pr2, all)"),
    db_dir: Path = typer.Option(None, "--db-dir", "-d", help="Database directory override"),
    force: bool = typer.Option(False, "--force", help="Force re-download")):

    start_time = datetime.datetime.now()
    print_header(start_time)

    manager = DatabaseManager(cli_db_dir=db_dir)
    section("Database installation")

    if db == "all":
        for name in manager.list_registered_dbs():
            section(f"Installing {name}")
            manager.install(name, force=force)
    else:
        section(f"Installing {db}")
        manager.install(db, force=force)
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print("-" * 70)
    print(f"Finished: {end_time.isoformat(timespec='seconds')}")
    print(f"Total runtime: {format_timedelta(duration)}")
    print("-" * 70)


@db_app.command("status")
def db_status(
    db_dir: Path = typer.Option(None, "--db-dir", "-d", help="Database directory override")):

    manager = DatabaseManager(cli_db_dir=db_dir)
    section("Database status")
    status = manager.status()

    for db, installed in status.items():
        if installed:
            info(f"{db:10} . installed")
        else:
            warn(f"{db:10} x missing")


if __name__ == "__main__":
    app()