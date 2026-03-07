import os
from rdna_miner.utils.cmd import run_command

def run(ctx):
    ctx.log_step("Map reads to rDNA assembly")
    assembly_fasta = ctx.require("assembly")
    rdna_reads = ctx.require("rdna_reads")
    mapping_file = ctx.artifact("mapping", "mapping", ".tsv")
    if ctx.exists("mapping"):
        return

    platform = getattr(ctx, "platform", "ont")
    mm2_preset = "map-ont" if platform == "ont" else "map-pb"

    cmd = (
        f"minimap2 -t {ctx.threads} -ax {mm2_preset} --secondary=no {assembly_fasta} {rdna_reads} | "
        f"samtools view -@ {ctx.threads} -F 4 | "
        r"""awk 'BEGIN {OFS="\t"; print "QNAME","FLAG","RNAME","POS","MAPQ","CIGAR","RNEXT","PNEXT","TLEN","TAGS"}
                 { tags=""; if (NF>11) { for (i=12;i<=NF;i++){ if(tags==""){tags=$i}else{tags=tags";"$i}} }
                   print $1,$2,$3,$4,$5,$6,$7,$8,$9,tags }' """
        f"> {mapping_file}"
    )
    run_command(cmd)
    ctx.register("mapping", mapping_file)