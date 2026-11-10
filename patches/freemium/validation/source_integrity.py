"""Staging multi-file dengan validasi awal dan rollback jika commit gagal."""
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


def _write_temp(target: Path, content: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    path = Path(name)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def commit_staged(staged: list[StagedFile]) -> None:
    seen: set[Path] = set()
    for item in staged:
        if item.path in seen:
            raise RuntimeError(f"Duplicate staged target: {item.path}")
        seen.add(item.path)
        if item.original is None:
            if item.path.exists():
                raise RuntimeError(f"New staged source already exists: {item.path}")
        elif not item.path.is_file() or item.path.read_text(encoding="utf-8") != item.original:
            raise RuntimeError(f"Source changed after staging: {item.path}")

    temporary_files: list[tuple[Path, Path]] = []
    replaced: list[StagedFile] = []
    try:
        for item in staged:
            temporary_files.append((_write_temp(item.path, item.updated), item.path))
        for temporary_path, target_path in temporary_files:
            os.replace(temporary_path, target_path)
            replaced.append(next(item for item in staged if item.path == target_path))
    except Exception:
        for item in reversed(replaced):
            if item.original is None:
                item.path.unlink(missing_ok=True)
            else:
                rollback_path = _write_temp(item.path, item.original)
                os.replace(rollback_path, item.path)
        raise
    finally:
        for temporary_path, _ in temporary_files:
            if temporary_path.exists():
                temporary_path.unlink()
