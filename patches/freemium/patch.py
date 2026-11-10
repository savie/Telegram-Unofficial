#!/usr/bin/env python3
"""Orkestrasi patch Freemium V2; seluruh source di-stage sebelum ditulis."""
from pathlib import Path

from .activation.activation_flow import patch_purchase_flow
from .core.account_storage import stage_java_helper
from .features.ai_tools import patch_ai_editor_alert
from .features.app_icons import patch_app_icons_selector
from .features.business import TARGETS as BUSINESS_SOURCE_FILES
from .features.chat_management import patch_archive_settings, patch_dialog_cell_tags, patch_dialogs_activity, patch_filter_chatlist, patch_filter_create, patch_filter_tabs_view, patch_filters_setup, patch_saved_messages_controller, patch_users_select_activity
from .features.downloads import patch_file_load_operation, patch_file_loader
from .features.emoji_and_stickers import patch_available_reaction_cell, patch_media_data_controller, patch_reactions_container, patch_select_animated_emoji_dialog, patch_sticker_cell, patch_sticker_emoji_cell, patch_stickers_alert, patch_topic_create_fragment
from .features.last_seen import patch_message_private_seen_view
from .features.limits_and_storage import patch_chat_rights_edit_activity, patch_document_layout, patch_photo_viewer_caption, patch_select_chat_user_sheet
from .features.no_ads import patch_dialogs_search_adapter, patch_video_ads
from .features.formatting_tools import patch_attach_rich_layout, patch_chat_activity_enter_view, patch_rich_editor
from .features.privacy_and_sharing import patch_privacy_controls
from .features.profile_and_colors import patch_peer_color_activity, patch_profile_activity
from .features.saved_messages import patch_search_tags
from .features.stories import patch_caption_container_view, patch_expired_story_views, patch_stealth_mode, patch_stories_controller
from .features.translation import patch_translate_alert, patch_translate_button
from .features.voice_to_text import patch_transcribe_button
from .features.wallpapers import patch_theme_preview_activity
from .validation.account_isolation import validate_account_storage_source
from .validation.feature_regression import assert_no_standalone_theme_ui_modules, validate_catalog_mapping
from .validation.patch_preflight import require_files, require_upstream_revision
from .validation.source_integrity import StagedFile, commit_staged


FEATURE_PATCHES = (
    ("ui/Components/TranscribeButton.java", patch_transcribe_button),
    ("ui/Components/TranslateButton.java", patch_translate_button),
    ("ui/Components/TranslateAlert3.java", patch_translate_alert),
    ("ui/Stories/StealthModeAlert.java", patch_stealth_mode),
    ("ui/Stories/SelfStoryViewsPage.java", patch_expired_story_views),
    ("ui/Stories/StoriesController.java", patch_stories_controller),
    ("ui/Components/SearchTagsList.java", patch_search_tags),
    ("ui/iv/RichEditor.java", patch_rich_editor),
    ("ui/iv/ChatAttachAlertRichLayout.java", patch_attach_rich_layout),
    ("ui/PeerColorActivity.java", patch_peer_color_activity),
    ("ui/ProfileActivity.java", patch_profile_activity),
    ("messenger/FileLoader.java", patch_file_loader),
    ("messenger/FileLoadOperation.java", patch_file_load_operation),
    ("messenger/MediaDataController.java", patch_media_data_controller),
    ("ui/Components/ReactionsContainerLayout.java", patch_reactions_container),
    ("ui/Components/StickersAlert.java", patch_stickers_alert),
    ("ui/Components/AIEditorAlert.java", patch_ai_editor_alert),
    ("ui/PrivacyControlActivity.java", patch_privacy_controls),
    ("ui/SelectAnimatedEmojiDialog.java", patch_select_animated_emoji_dialog),
    ("ui/Components/ChatActivityEnterView.java", patch_chat_activity_enter_view),
    ("messenger/SavedMessagesController.java", patch_saved_messages_controller),
    ("ui/DialogsActivity.java", patch_dialogs_activity),
    ("ui/ArchiveSettingsActivity.java", patch_archive_settings),
    ("ui/FiltersSetupActivity.java", patch_filters_setup),
    ("ui/FilterCreateActivity.java", patch_filter_create),
    ("ui/FilterChatlistActivity.java", patch_filter_chatlist),
    ("ui/Components/DialogCellTags.java", patch_dialog_cell_tags),
    ("ui/Components/FilterTabsView.java", patch_filter_tabs_view),
    ("ui/UsersSelectActivity.java", patch_users_select_activity),
    ("ui/ChatRightsEditActivity.java", patch_chat_rights_edit_activity),
    ("ui/SelectChatUserSheet.java", patch_select_chat_user_sheet),
    ("ui/Components/ChatAttachAlertDocumentLayout.java", patch_document_layout),
    ("ui/Components/PhotoViewerCaptionEnterView.java", patch_photo_viewer_caption),
    ("ui/Stories/recorder/CaptionContainerView.java", patch_caption_container_view),
    ("messenger/video/VideoAds.java", patch_video_ads),
    ("ui/Adapters/DialogsSearchAdapter.java", patch_dialogs_search_adapter),
    ("ui/ThemePreviewActivity.java", patch_theme_preview_activity),
    ("ui/Cells/AppIconsSelectorCell.java", patch_app_icons_selector),
    ("ui/Cells/StickerCell.java", patch_sticker_cell),
    ("ui/Cells/StickerEmojiCell.java", patch_sticker_emoji_cell),
    ("ui/Cells/AvailableReactionCell.java", patch_available_reaction_cell),
    ("ui/TopicCreateFragment.java", patch_topic_create_fragment),
    ("ui/Components/MessagePrivateSeenView.java", patch_message_private_seen_view),
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
    required.extend(
        "TMessagesProj/src/main/java/org/telegram/" + relative_path
        for relative_path in BUSINESS_SOURCE_FILES
    )
    require_files(upstream_root, tuple(required))

    validate_catalog_mapping()
    helper_path, helper_source = stage_java_helper(upstream_root)
    validate_account_storage_source(helper_source)
    assert_no_standalone_theme_ui_modules([relative for relative, _ in FEATURE_PATCHES])
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
        "Reactions, Advanced Chat Management, No Ads, AI Tools, Paid Messages, "
        "Disable Sharing, and Formatting Tools. "
        f"Upstream revision: {upstream_revision}."
    )


if __name__ == "__main__":
    apply_freemium()
