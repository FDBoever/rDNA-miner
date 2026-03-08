from rdna_miner.steps import (barrnap_scan,
                              filter_rdna_reads,
                              assemble_rdna,
                              annotate_rfam,
                              taxonomy_decipher,
                              map_reads,
                              compile_taxonomy,)


def build_pipeline():
    """
    Each step exposes run(ctx) and internally
    handles its own dependencies using ctx.require().
    """

    return [
        barrnap_scan.run,
        filter_rdna_reads.run,
        assemble_rdna.run,
        annotate_rfam.run,
        taxonomy_decipher.run,
        map_reads.run,
        compile_taxonomy.run,
    ]


def run_pipeline(ctx):
    pipeline = build_pipeline()

    for step in pipeline:
        if ctx.exists("pipeline_terminated_early"):
            return
        step(ctx)
    
    ctx.report_artifacts()