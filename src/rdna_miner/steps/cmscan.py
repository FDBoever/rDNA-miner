# src/rdna_miner/steps/cmscan.py
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from Bio import SeqIO
from rdna_miner.utils.cmd import run_command

def _cmscan_cmd(input_file, tblout, clanin, cm):
    return (
        f'cmscan --cpu 1 -Z 5.874406 --cut_ga --rfam --nohmmonly '
        f'--tblout "{tblout}" --fmt 2 --clanin "{clanin}" "{cm}" "{input_file}"'
    )

def _split_fasta(in_fa, out_dir, n_parts):
    records = list(SeqIO.parse(in_fa, "fasta"))
    if len(records) <= 1 or n_parts <= 1:
        return [in_fa]
    n_parts = min(n_parts, len(records))
    buckets = [[] for _ in range(n_parts)]
    for i, rec in enumerate(records):
        buckets[i % n_parts].append(rec)
    shards = []
    for idx, bucket in enumerate(buckets, 1):
        if not bucket:
            continue
        shard_path = os.path.join(out_dir, f"shard_{idx}.fasta")
        with open(shard_path, "w") as h:
            SeqIO.write(bucket, h, "fasta")
        shards.append(shard_path)
    return shards

def run(ctx, rfam_cm: Path, rfam_clanin: Path):
    """
    Run cmscan on the rDNA assembly.
    Requires explicit paths to Rfam database files.
    """
    assembly_fasta = ctx.require("assembly")
    cm_out = ctx.artifact("cm_out", "cm", "")
    final_tblout = ctx.artifact("cmscan_tblout", "cm", ".tblout")

    if ctx.artifact_exists_or_skip("cmscan_tblout"):
        return

    os.makedirs(cm_out, exist_ok=True)
    threads = ctx.threads

    if threads > 1:
        with tempfile.TemporaryDirectory(dir=cm_out) as tmpd:
            shards = _split_fasta(assembly_fasta, tmpd, threads)
            if len(shards) == 1:
                run_command(
                    f'cmscan --cpu {threads} -Z 5.874406 --cut_ga --rfam --nohmmonly '
                    f'--tblout "{final_tblout}" --fmt 2 --clanin "{rfam_clanin}" "{rfam_cm}" "{assembly_fasta}"'
                )
            else:
                tblouts = [os.path.join(tmpd, f"{Path(s).stem}.tblout") for s in shards]
                cmds = [_cmscan_cmd(s, t, rfam_clanin, rfam_cm) for s, t in zip(shards, tblouts)]
                with ThreadPoolExecutor(max_workers=min(threads, len(cmds))) as ex:
                    futures = [ex.submit(run_command, c) for c in cmds]
                    for f in futures:
                        f.result()
                # merge tblouts
                with open(final_tblout, "w") as out:
                    for i, tf in enumerate(tblouts):
                        with open(tf) as fh:
                            for line in fh:
                                # skip header lines for all but the first shard
                                if line.startswith("#") and i > 0:
                                    continue
                                out.write(line)
    else:
        run_command(
            f'cmscan --cpu 1 -Z 5.874406 --cut_ga --rfam --nohmmonly '
            f'--tblout "{final_tblout}" --fmt 2 --clanin "{rfam_clanin}" "{rfam_cm}" "{assembly_fasta}"'
        )

    ctx.register("cm_out", cm_out)