"""Staging perubahan teks agar validasi selesai sebelum source ditulis."""
from pathlib import Path

class StagedFile:
    def __init__(self, path: Path, original: str, updated: str):
        self.path, self.original, self.updated = path, original, updated

def stage_text(path: Path, transform) -> StagedFile:
    original = path.read_text(encoding="utf-8")
    updated = transform(original)
    if not isinstance(updated, str) or not updated:
        raise ValueError(f"Invalid staged source for {path}")
    return StagedFile(path, original, updated)

def commit_staged(staged: list[StagedFile]) -> None:
    for item in staged:
        if item.path.read_text(encoding="utf-8") != item.original:
            raise RuntimeError(f"Source changed after staging: {item.path}")
    for item in staged:
        item.path.write_text(item.updated, encoding="utf-8")
