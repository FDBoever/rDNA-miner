import os
from pathlib import Path
import pandas as pd
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

def read_cmscan(filename):
    lines = []
    with open(filename, 'r') as fh:
        for line in fh:
            if line.strip() and not line.startswith("#"):
                lines.append(line.strip())
    data = []
    for line in lines:
        cols = line.split()
        if len(cols) > 26:
            cols[26] = ' '.join(cols[26:])
            cols = cols[:27]
        data.append(cols)
    columns = ['idx','target_name','accession','query_name','query_accession','clan_name',
               'mdl','mdl_from','mdl_to','seq_from','seq_to','strand','trunc','pass','gc',
               'bias','score','E_value','inc','olp','anyidx','afrct1','afrct2','winidx',
               'wfrct1','wfrct2','description']
    return pd.DataFrame(data, columns=columns)

def detect_overlap(df):
    df['overlap_group'] = -1
    current_group = 1
    prev_query_name = None
    position_set = set()
    for idx, row in df.iterrows():
        query_name = row['query_name']
        seq_from, seq_to = int(row['seq_from']), int(row['seq_to'])
        start, end = min(seq_from, seq_to), max(seq_from, seq_to)
        if query_name != prev_query_name:
            position_set = set()
            current_group = 1
            prev_query_name = query_name
        if any(pos in position_set for pos in range(start, end+1)):
            df.at[idx, 'overlap_group'] = current_group
        else:
            current_group += 1
            df.at[idx, 'overlap_group'] = current_group
            position_set.update(range(start, end+1))
    return df

def top_hit(df):
    sorted_df = df.sort_values(['query_name','overlap_group','E_value','score'], ascending=[True,True,True,False])
    grouped = sorted_df.groupby(['query_name','overlap_group'])
    top_hits = pd.DataFrame()
    for name, group in grouped:
        top_hits = pd.concat([top_hits, group.head(1)])
    return top_hits

def extract_top_hits(df, fasta_file, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    seqs = SeqIO.to_dict(SeqIO.parse(fasta_file, "fasta"))
    for target_name, group in df.groupby('target_name'):
        records = []
        for _, row in group.iterrows():
            seq = seqs.get(row['query_name'])
            if seq:
                start, end = min(int(row['seq_from']), int(row['seq_to'])), max(int(row['seq_from']), int(row['seq_to']))
                frag = seq.seq[start-1:end]
                if row['strand'] == '-':
                    frag = frag.reverse_complement()
                rec = SeqRecord(frag, id=f"{row['query_name']}_{row['target_name']}", description=f"TopHit_{start}_{end}")
                records.append(rec)
        SeqIO.write(records, output_dir / f"extracted_sequences_{target_name}.fasta", "fasta")

def run(ctx):
    ctx.log_step("Analyse cmscan output and extract top hits")

    tblout = ctx.require("cmscan_tblout")
    assembly_fasta = ctx.require("assembly")
    cm_out = ctx.require("cm_out")

    df = read_cmscan(tblout)
    overlaps = detect_overlap(df)
    top_hits_df = top_hit(overlaps)

    extract_top_hits(top_hits_df, assembly_fasta, cm_out)

    # register top hits
    ctx.register("cm_top_hits", top_hits_df)