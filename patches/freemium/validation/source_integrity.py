"""Staging dan commit perubahan source setelah semua anchor lolos preflight."""
from pathlib import Path
import os
import tempfile


class StagedFile:
    def __init__(self, path: Path, original: str | None, updated: str):
        self.path = path
        self.original = original
        self.updated = updated


def stage_text(path: Path, transform) -> StagedFile:
    original = path.read_text(encoding="utf-8")
    updated = transform(original)
    if not isinstance(updated, str) or not updated:
        raise ValueError(f"Invalid staged source for {path}")
    return StagedFile(path, original, updated)


def commit_staged(staged: list[StagedFile]) -> None:
    # Validate every target before creating or replacing any source file.
    for item in staged:
        if item.original is None:
            if item.path.exists():
                raise RuntimeError(f"New staged source already exists: {item.path}")
        elif not item.path.is_file() or item.path.read_text(encoding="utf-8") != item.original:
            raise RuntimeError(f"Source changed after staging: {item.path}")

    temporary_files: list[tuple[Path, Path]] = []
    try:
        for item in staged:
            item.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(
                prefix=item.path.name + ".",
                suffix=".tmp",
                dir=str(item.path.parent),
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(item.updated)
                stream.flush()
                os.fsync(stream.fileno())
            temporary_files.append((temporary_path, item.path))

        # os.replace keeps each individual file replacement atomic.
        for temporary_path, target_path in temporary_files:
            os.replace(temporary_path, target_path)
    finally:
        for temporary_path, _ in temporary_files:
            if temporary_path.exists():
                temporary_path.unlink()
