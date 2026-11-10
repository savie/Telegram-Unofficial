#!/usr/bin/env python3
"""Orkestrasi patch Freemium V2; seluruh source di-stage sebelum ditulis."""
from pathlib import Path

from .activation.activation_flow import patch_purchase_flow
from .core.account_storage import stage_java_helper
from .features.ai_tools import patch_ai_editor_alert
from .features.downloads import patch_file_load_operation, patch_file_loader
from .features.emoji_and_stickers import patch_media_data_controller, patch_reactions_container, patch_stickers_alert
from .features.formatting_tools import patch_attach_rich_layout, patch_rich_editor
from .features.privacy_and_sharing import patch_privacy_controls
from .features.profile_and_colors import patch_peer_color_activity
from .features.saved_messages import patch_search_tags
from .features.stories import patch_expired_story_views, patch_stealth_mode
from .features.translation import patch_translate_alert, patch_translate_button
from .features.voice_to_text import patch_transcribe_button
from .validation.patch_preflight import require_files, require_upstream_revision
from .validation.source_integrity import StagedFile, commit_staged


FEATURE_PATCHES = (
    ("ui/Components/TranscribeButton.java", patch_transcribe_button),
    ("ui/Components/TranslateButton.java", patch_translate_button),
    ("ui/Components/TranslateAlert3.java", patch_translate_alert),
    ("ui/Stories/StealthModeAlert.java", patch_stealth_mode),
    ("ui/Stories/SelfStoryViewsPage.java", patch_expired_story_views),
    ("ui/Components/SearchTagsList.java", patch_search_tags),
    ("ui/iv/RichEditor.java", patch_rich_editor),
    ("ui/iv/ChatAttachAlertRichLayout.java", patch_attach_rich_layout),
    ("ui/PeerColorActivity.java", patch_peer_color_activity),
    ("messenger/FileLoader.java", patch_file_loader),
    ("messenger/FileLoadOperation.java", patch_file_load_operation),
    ("messenger/MediaDataController.java", patch_media_data_controller),
    ("ui/Components/ReactionsContainerLayout.java", patch_reactions_container),
    ("ui/Components/StickersAlert.java", patch_stickers_alert),
    ("ui/Components/AIEditorAlert.java", patch_ai_editor_alert),
    ("ui/PrivacyControlActivity.java", patch_privacy_controls),
)


def apply_freemium() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    upstream_root = repo_root / "upstream"
    upstream_revision = require_upstream_revision(repo_root)
    java_root = upstream_root / "TMessagesProj/src/main/java"

    required = [
        "TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java",
        "TMessagesProj/src/main/java/org/telegram/ui/PremiumPreviewFragment.java",
    ]
    required.extend(
        "TMessagesProj/src/main/java/org/telegram/" + relative_path
        for relative_path, _ in FEATURE_PATCHES
    )
    require_files(upstream_root, tuple(required))

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

    for relative_path, transform in FEATURE_PATCHES:
        target = java_root / "org/telegram" / relative_path
        original = target.read_text(encoding="utf-8")
        updated = transform(original)
        if updated != original:
            staged.append(StagedFile(target, original, updated))

    if not staged:
        print("Freemium V2 already applied; no source changes required.")
        return

    commit_staged(staged)
    print(
        "Freemium V2 applied: account-local activation and client-side gates "
        "for Stories, Voice-to-Text, Real-Time Translation, Saved Message Tags, "
        "Name and Profile Colors, Faster Download Speed, Emoji and Stickers, "
        "Reactions, AI Tools, Paid Messages, Disable Sharing, and Formatting Tools. "
        f"Upstream revision: {upstream_revision}."
    )


if __name__ == "__main__":
    apply_freemium()
