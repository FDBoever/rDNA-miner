from rdna_miner.steps import (barrnap_scan,
                              filter_rdna_reads,
                              assemble_rdna,
                              annotate_rfam,
                              taxonomy_decipher,
                              map_reads,
                              compile_taxonomy,)
from rdna_miner.utils.logging_utils import section, info, warn


def build_long_read_pipeline():
    """
    Each step exposes run(ctx) and internally
    handles its own dependencies using ctx.require().
    """

    return [
        (barrnap_scan.run, "Run Barrnap"),
        (filter_rdna_reads.run, "Filter putative rDNA reads"),
        (assemble_rdna.run, "Assemble rDNA reads with Flye"),
        (annotate_rfam.run, "Annotate rDNA operons with Rfam/cmscan"),
        (taxonomy_decipher.run, "Assign taxonomy with DECIPHER"),
        (map_reads.run, "Map reads to rDNA assembly"),
        (compile_taxonomy.run, "Complete read-level taxonomy assignment" ),
    ]

def build_assembly_pipeline():
    """Pipeline provided an assembly."""

    return [
        (annotate_rfam.run, "Annotate rDNA operons with Rfam/cmscan"),
        (taxonomy_decipher.run, "Assign taxonomy with DECIPHER"),
    ]

def run_pipeline(ctx, pipeline):
    total_steps = len(pipeline)

    for i, (step_func, step_name) in enumerate(pipeline, start=1):
        if ctx.exists("pipeline_terminated_early"):
            return

        section(f"[{i}/{total_steps}] {step_name}")
        step_func(ctx)

    ctx.report_artifacts()