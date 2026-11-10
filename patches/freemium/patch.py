#!/usr/bin/env python3
"""Orkestrasi patch Freemium V2; seluruh source di-stage sebelum ditulis."""
from pathlib import Path

from .activation.activation_flow import patch_purchase_flow
from .core.account_storage import stage_java_helper
from .validation.patch_preflight import require_files
from .validation.source_integrity import StagedFile, commit_staged


def apply_freemium() -> None:
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
    preview_path = java_root / "org/telegram/ui/PremiumPreviewFragment.java"

    staged: list[StagedFile] = []

    helper_original = helper_path.read_text(encoding="utf-8") if helper_path.exists() else None
    if helper_original != helper_source:
        staged.append(StagedFile(helper_path, helper_original, helper_source))

    preview_original = preview_path.read_text(encoding="utf-8")
    preview_updated = patch_purchase_flow(preview_original)
    if preview_updated != preview_original:
        staged.append(StagedFile(preview_path, preview_original, preview_updated))

    if not staged:
        print("Freemium V2 already applied; no source changes required.")
        return

    commit_staged(staged)
    print(
        "Freemium V2 applied: account-local entitlement helper and "
        "Telegram Premium purchase-flow redirection."
    )


if __name__ == "__main__":
    apply_freemium()
