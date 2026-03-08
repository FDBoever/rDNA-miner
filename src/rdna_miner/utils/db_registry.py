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
        url="https://example.org/silva/SILVA_SSU_latest.RData.gz",
        files=["SILVA_SSU_*.RData"],
        compressed=True
    ),
    "pr2": DatabaseSpec(
        name="pr2",
        url="https://example.org/pr2/pr2_version_latest.decipher.trained.rds",
        files=["pr2_version_*.decipher.trained.rds"],
        compressed=False
    )
}