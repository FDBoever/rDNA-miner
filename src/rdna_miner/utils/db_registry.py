from dataclasses import dataclass
from typing import List

@dataclass
class DatabaseSpec:
    name: str
    url: str
    files: List[str]
    compressed: bool = False


DATABASES = {
    "rfam": DatabaseSpec(
        name="rfam",
        url="https://ftp.ebi.ac.uk/pub/databases/Rfam/CURRENT/Rfam.cm.gz",
        files=["Rfam.cm", "Rfam.clanin"],
        compressed=True
    ),
    "silva": DatabaseSpec(
        name="silva",
        url="https://drive.google.com/file/d/1w3wdSCpSihntWkbP_zvXz7r3s-tNB8DV/view?usp=sharing",
        files=["SILVA_SSU_*.RData"],
        compressed=True
    ),
    "pr2": DatabaseSpec(
        name="pr2",
        url="https://github.com/pr2database/pr2database/releases/download/v5.1.0.0/pr2_version_5.1.0_SSU.decipher.trained.rds",
        files=["pr2_version_*.decipher.trained.rds"],
        compressed=False
    )
}