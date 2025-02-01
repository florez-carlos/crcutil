from dataclasses import dataclass
from pathlib import Path


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class BootstrapPathsDTO:
    log_dir: Path
