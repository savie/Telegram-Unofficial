#!/usr/bin/env python3
"""Entry point patch Freemium V2; detail implementasi berada di modul bertanggung jawab."""
from pathlib import Path

from .core.account_storage import stage_java_helper
from .validation.patch_preflight import require_files
from .validation.source_integrity import StagedFile, commit_staged


def apply_freemium() -> None:
    """Preflight, stage seluruh perubahan Freemium, lalu commit secara deterministik."""
    repo_root = Path(__file__).resolve().parents[2]
    upstream_root = repo_root / "upstream"
    java_root = upstream_root / "TMessagesProj/src/main/java"
    require_files(
        upstream_root,
        (
            "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java",
            "TMessagesProj/src/main/java/org/telegram/ui/PremiumPreviewFragment.java",
        ),
    )

    helper_path, helper_source = stage_java_helper(upstream_root)
    staged = []
    if helper_path.exists():
        original = helper_path.read_text(encoding="utf-8")
        if original != helper_source:
            staged.append(StagedFile(helper_path, original, helper_source))
    else:
        # A new file is staged with an empty expected original; commit_staged
        # handles creation only after every existing target has passed preflight.
        staged.append(StagedFile(helper_path, "", helper_source))

    for item in staged:
        if item.path.exists() and item.path.read_text(encoding="utf-8") != item.original:
            raise RuntimeError(f"Source changed after staging: {item.path}")
        if not item.path.exists() and item.original:
            raise RuntimeError(f"Staged source disappeared: {item.path}")
    for item in staged:
        item.path.parent.mkdir(parents=True, exist_ok=True)
        item.path.write_text(item.updated, encoding="utf-8")


if __name__ == "__main__":
    apply_freemium()
