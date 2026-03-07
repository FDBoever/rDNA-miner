from Bio import SeqIO
from pathlib import Path

def load_fasta_or_convert(input_path: Path, output_dir: Path):
    """
    Ensure input is a FASTA file. If not, try to convert to FASTA.
    Returns the Path to the canonical FASTA.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() in [".fa", ".fasta", ".fna"]:
        return input_path

    # If input is some other format (e.g., FASTQ), convert to FASTA
    fasta_path = output_dir / f"{input_path.stem}.fasta"
    with open(fasta_path, "w") as out_f:
        for record in SeqIO.parse(str(input_path), "fastq"):  # or adjust parser
            SeqIO.write(record, out_f, "fasta")
    return fasta_path

def extract_rDNA_read_ids(gff_files):
    read_ids = set()
    for gff_file in gff_files:
        with open(gff_file) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                read_id = line.split("\t")[0]
                read_ids.add(read_id)
    return read_ids


def filter_fasta(input_fasta, output_fasta, read_ids):
    with open(output_fasta, "w") as out_f:
        for record in SeqIO.parse(input_fasta, "fasta"):
            if record.id in read_ids:
                SeqIO.write(record, out_f, "fasta")