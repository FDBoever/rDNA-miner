# src/rdna_miner/utils/db_registry.py
from dataclasses import dataclass
from typing import List

@dataclass
class DownloadSpec:
    url: str
    filename: str
    compressed: bool = False
    source: str = "http"  # http | gdrive

@dataclass
class DatabaseSpec:
    name: str
    downloads: List[DownloadSpec]
    files: List[str]

DATABASES = {

    "rfam": DatabaseSpec(
        name="rfam",
        downloads=[
            DownloadSpec(
                url="https://ftp.ebi.ac.uk/pub/databases/Rfam/CURRENT/Rfam.cm.gz",
                filename="Rfam.cm.gz",
                compressed=True),
            DownloadSpec(
                url="https://ftp.ebi.ac.uk/pub/databases/Rfam/CURRENT/Rfam.clanin",
                filename="Rfam.clanin")
        ],
        files=["Rfam.cm", "Rfam.clanin"]
    ),

    "silva": DatabaseSpec(
        name="silva",
        downloads=[
            DownloadSpec(
                url="1w3wdSCpSihntWkbP_zvXz7r3s-tNB8DV",  # Google Drive ID
                filename="SILVA_SSU_r138.2_v2.RData",
                compressed=False,
                source="gdrive")
        ],
        files=["SILVA_SSU_*.RData"]
    ),

    "pr2": DatabaseSpec(
        name="pr2",
        downloads=[
            DownloadSpec(
                url="https://github.com/pr2database/pr2database/releases/download/v5.1.0.0/pr2_version_5.1.0_SSU.decipher.trained.rds",
                filename="pr2_version_5.1.0_SSU.decipher.trained.rds")
        ],
        files=["pr2_version_*.decipher.trained.rds"]
    )
}


## Explore the inclusion of EUKRAYOME
## https://eukaryome.org/