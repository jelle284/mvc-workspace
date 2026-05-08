import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

# ================================================================= #
# ------------------------  Error classes -------------------------- #
class MVCError(Exception):
    def __init__(self, message):
        super().__init__(message)

# ================================================================= #
# ---------------------------- Functions -------------------------- #

def get_submit_path(submit_id: int) -> str:
    return Path("temp") / f"sub{submit_id}"

def get_stable_path() -> str:
    return Path("versions") / "latest"

def get_release_path(release_id: int) -> str:
    return Path("versions") / f"ver{release_id}"

def list_files_dir(dir: str):
    return [f for f in os.listdir(dir) if f not in (".mvc", "changelog.md")]

# ================================================================= #
# ------------------------  Data classes -------------------------- #
@dataclass
class FileID:
    major: int
    minor: int
    dev: int
    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.dev}"
    @property
    def sub_path(self):
        if self.dev > 0:
            subpath = get_submit_path(self.dev)
        elif self.minor > 0:
            subpath = get_stable_path()
        elif self.major > 0:
            subpath = get_release_path(self.major)
        else:
            subpath = get_stable_path()
        return subpath
    @classmethod
    def copy(cls, other):
        return cls(**other.__dict__)
    
# ================================================================= #
# ------------------ Persistent Data classes ---------------------- #

class JSONBase:
    """Base class providing JSON persistence for dataclasses."""

    def save(self, filepath: str):
        data = asdict(self)
        filepath = Path(filepath) / ".mvc"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, filepath: str):
        def object_hook(d: dict):
            if all(field in d for field in FileID.__annotations__):
                return FileID(**d)
            return d
        filepath = Path(filepath) / ".mvc"
        with open(filepath, 'r') as f:
            data = json.load(f, object_hook=object_hook)
        return cls(**data)

@dataclass
class Project(JSONBase):
    name: str
    id: FileID
    claims: dict[str, str]

@dataclass
class Workspace(JSONBase):
    project: str

@dataclass
class Version(JSONBase):
    description: list[str]
    include: dict[str, FileID]
