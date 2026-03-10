# src/rdna_miner/utils/db.py
import os
from pathlib import Path
from glob import glob

import urllib.request
import gzip
import shutil
import gdown
import subprocess

from rdna_miner.utils.db_registry import DATABASES
from rdna_miner.utils.logging_utils import section, info, warn

class DatabaseManager:
    """
    Resolve and verify required bioinformatic databases.
    Supports multiple database types, e.g., rfam, silva, pr2.
    """

    DEFAULT_BASE = Path.home() / ".rdna-miner" / "db"

    # register expected files for each database type
    DATABASE_FILES = {
        "rfam": ["Rfam.cm", "Rfam.clanin"],
        "silva": ["SILVA_SSU_*.RData"],
        "pr2": ["pr2_version_*.decipher.trained.rds"]
    }

    def __init__(self, cli_db_dir: str = None):
        """
        Resolve base db directory according to priority:
        1. CLI override
        2. ENV variable RDNA_MINER_DB
        3. Default install location (~/.rdna-miner/db)
        """
        self.base_dir = Path(cli_db_dir) if cli_db_dir else None
        if not self.base_dir:
            env = os.environ.get("RDNA_MINER_DB")
            if env:
                self.base_dir = Path(env)
            else:
                self.base_dir = self.DEFAULT_BASE

        self.db_paths = {}
        self._overrides = {}        
    
    def override_db(self, db_type: str, path: str):
        """
        Set a user-specified override for a database type.
        """
        path = Path(path)
        if not path.exists():
            raise RuntimeError(f"Override path for database '{db_type}' does not exist: {path}")
        self._overrides[db_type] = path


    def get_db(self, db_type: str) -> Path:
        """
        Returns the directory for the database, resolves files by pattern.
        Raises RuntimeError if database is missing.
        """
        if db_type not in self.DATABASE_FILES:
            raise ValueError(f"Unknown database type: {db_type}")

        db_path = self._overrides.get(db_type, self.base_dir / db_type)
        self.db_paths[db_type] = db_path

        missing_files = []
        resolved_files = []

        for pattern in self.DATABASE_FILES[db_type]:
            matches = list(db_path.glob(pattern))
            if not matches:
                missing_files.append(pattern)
            else:
                if len(matches) > 1:
                    # pick the latest file alphabetically (reasonable for versions)
                    matches.sort()
                resolved_files.append(matches[-1])  # last = latest
        if missing_files:
            raise RuntimeError(
                f"Database '{db_type}' missing required files: {missing_files}\n"
                f"Searched in: {db_path}\n"
                "Please either:\n"
                " 1. Run `rdna-miner download-db`\n"
                f" 2. Point to an existing database using --{db_type}-db"
            )

        return resolved_files if len(resolved_files) > 1 else resolved_files[0]


    def list_registered_dbs(self):
        """Return database types known to the system."""
        return list(self.DATABASE_FILES.keys())
    

    def install(self, db_type: str, force: bool = False):
        if db_type not in DATABASES:
            raise ValueError(f"Unknown database: {db_type}")

        spec = DATABASES[db_type]

        target_dir = self.base_dir / db_type
        target_dir.mkdir(parents=True, exist_ok=True)

        for download in spec.downloads:
            download_path = target_dir / download.filename

            if download_path.exists() and not force:
                info(f"{download.filename} already exists")
                continue

            info(f"Downloading {download.filename}")
            if download.source == "http":
                urllib.request.urlretrieve(download.url, download_path)
            elif download.source == "gdrive":
                gdown.download(id=download.url, output=str(download_path), quiet=False)
            else:
                raise RuntimeError(f"Unknown download source: {download.source}")

            if download.compressed:
                info(f"Decompressing {download.filename}")
                out_file = target_dir / download.filename.replace(".gz", "")

                with gzip.open(download_path, "rb") as f_in:
                    with open(out_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                download_path.unlink()
        
        if db_type == "rfam":
            self._index_rfam(target_dir, force=force)        


    def status(self):
        results = {}

        for db_type in DATABASES:
            db_dir = self.base_dir / db_type
            installed = True

            if not db_dir.exists():
                installed = False
            else:
                for pattern in DATABASES[db_type].files:
                    if not list(db_dir.glob(pattern)):
                        installed = False
                        break

            results[db_type] = installed
        return results


    def _index_rfam(self, rfam_dir: Path, force: bool = False):
        """
        Run Infernal cmpress on Rfam.cm.
        Removes old indices if necessary.
        """
        cm_file = rfam_dir / "Rfam.cm"

        if not cm_file.exists():
            raise RuntimeError(f"Rfam.cm not found in {rfam_dir}")

        index_files = list(rfam_dir.glob("Rfam.cm.i*"))

        # If indices exist
        if index_files:
            if not force:
                info("RFAM already indexed")
                return

            info("Removing existing RFAM indices")
            for f in index_files:
                f.unlink()

        info("Indexing Rfam.cm with cmpress")
        try:
            subprocess.run(["cmpress", str(cm_file)], check=True)

        except FileNotFoundError:
            raise RuntimeError(
                "cmpress not found in PATH. Install Infernal.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"cmpress failed while indexing Rfam.cm\n{e}")

        info("RFAM indexing complete")