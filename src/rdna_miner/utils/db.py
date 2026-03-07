# src/rdna_miner/utils/db.py

import os
from pathlib import Path
from glob import glob

class DatabaseManager:
    """
    Resolve and verify required bioinformatic databases.
    Supports multiple database types, e.g., rfam, silva, pr2.
    """

    DEFAULT_BASE = Path.home() / ".rdna-miner" / "db"

    # Register expected files for each database type
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

        # Keep resolved db paths per type
        self.db_paths = {}

        # Store per-db overrides
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

        # return the resolved files, not just the dir
        return resolved_files if len(resolved_files) > 1 else resolved_files[0]

    def list_registered_dbs(self):
        """Return database types known to the system."""
        return list(self.DATABASE_FILES.keys())