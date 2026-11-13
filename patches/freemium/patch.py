#!/usr/bin/env python3
"""Orkestrasi patch Freemium V2; seluruh source di-stage sebelum ditulis."""
from pathlib import Path

from .activation.activation_flow import patch_purchase_flow, patch_settings_business_entry
from .core.account_storage import stage_java_helper
from .features.ai_tools import patch_ai_editor_alert
from .features.app_icons import patch_app_icons_selector
from .features.business import TARGETS as BUSINESS_SOURCE_FILES, patch_business_activity_gate, patch_chat_greetings_view, patch_quick_replies_layout
from .integration.premium_feature_gates import PREMIUM_GATE_TARGETS
from .features.chat_management import patch_archive_settings, patch_chat_activity_saved_message_tags, patch_dialog_cell_tags, patch_dialogs_activity, patch_filter_chatlist, patch_filter_create, patch_filter_tabs_view, patch_filters_setup, patch_saved_messages_controller, patch_users_select_activity
from .features.downloads import patch_file_load_operation
from .features.emoji_and_stickers import patch_stickers_adapter, patch_suggest_emoji_view, patch_content_preview_viewer, patch_custom_emoji_reactions_window, patch_mentions_adapter, patch_available_reaction_cell, patch_emoji_packs_alert, patch_media_data_controller, patch_reactions_container, patch_reactions_double_tap_manage, patch_select_animated_emoji_dialog, patch_setup_emoji_status_sheet, patch_sticker_cell, patch_sticker_set_bulletin_layout, patch_sticker_emoji_cell, patch_stickers_alert, patch_topic_create_fragment
from .features.last_seen import patch_message_private_seen_view
from .features.limits_and_storage import patch_chat_rights_edit_activity, patch_caption_photo_viewer, patch_document_layout, patch_file_loader_upload_limit, patch_file_upload_operation, patch_photo_viewer_caption, patch_select_chat_user_sheet
from .features.no_ads import patch_dialogs_search_adapter, patch_search_view_pager, patch_video_ads
from .features.formatting_tools import patch_attach_rich_layout, patch_chat_activity_enter_view, patch_rich_editor
from .features.privacy_and_sharing import patch_privacy_controls, patch_privacy_settings_activity
from .features.profile_and_colors import patch_peer_color_activity, patch_profile_activity, patch_user_object_profile_style, patch_avatar_drawable_profile_style, patch_chat_message_cell_profile_style, patch_message_topic_button_color_id, patch_reply_message_line_color_id, patch_giveaway_results_message_cell_color_id, patch_giveaway_message_cell_color_id, stage_local_profile_style
from .features.saved_messages import patch_search_tags
from .features.stories import patch_caption_container_view, patch_caption_story, patch_expired_story_views, patch_stealth_mode, patch_stories_controller
from .features.translation import patch_language_select_activity, patch_translate_alert, patch_translate_button
from .features.voice_to_text import patch_transcribe_button
from .features.wallpapers import patch_theme, patch_theme_preview_activity, patch_chat_theme_bottom_sheet
from .validation.account_isolation import validate_account_storage_source
from .validation.feature_regression import assert_no_standalone_theme_ui_modules, validate_catalog_mapping
from .validation.patch_preflight import require_files, require_upstream_revision
from .validation.source_integrity import StagedFile, commit_staged


FEATURE_PATCHES = (
    ("ui/Business/LocationActivity.java", patch_business_activity_gate),
    ("ui/Business/OpeningHoursActivity.java", patch_business_activity_gate),
    ("ui/Business/OpeningHoursDayActivity.java", patch_business_activity_gate),
    ("ui/Business/QuickRepliesActivity.java", patch_business_activity_gate),
    ("ui/Business/GreetMessagesActivity.java", patch_business_activity_gate),
    ("ui/Business/AwayMessagesActivity.java", patch_business_activity_gate),
    ("ui/Business/BusinessLinksActivity.java", patch_business_activity_gate),
    ("ui/Business/BusinessIntroActivity.java", patch_business_activity_gate),
    ("ui/Business/ChatbotsActivity.java", patch_business_activity_gate),
    ("ui/SettingsActivity.java", patch_settings_business_entry),
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
    ("messenger/UserObject.java", patch_user_object_profile_style),
    ("ui/Components/AvatarDrawable.java", patch_avatar_drawable_profile_style),
    ("ui/Cells/ChatMessageCell.java", patch_chat_message_cell_profile_style),
    ("ui/Components/Forum/MessageTopicButton.java", patch_message_topic_button_color_id),
    ("ui/Components/ReplyMessageLine.java", patch_reply_message_line_color_id),
    ("ui/Components/Premium/boosts/cells/msg/GiveawayResultsMessageCell.java", patch_giveaway_results_message_cell_color_id),
    ("ui/Components/Premium/boosts/cells/msg/GiveawayMessageCell.java", patch_giveaway_message_cell_color_id),
    ("messenger/FileLoader.java", patch_file_loader_upload_limit),
    ("messenger/FileLoadOperation.java", patch_file_load_operation),
    ("messenger/MediaDataController.java", patch_media_data_controller),
    ("ui/Components/ReactionsContainerLayout.java", patch_reactions_container),
    ("ui/Components/Reactions/CustomEmojiReactionsWindow.java", patch_custom_emoji_reactions_window),
    ("ui/Adapters/MentionsAdapter.java", patch_mentions_adapter),
    ("ui/ContentPreviewViewer.java", patch_content_preview_viewer),
    ("ui/Components/SearchViewPager.java", patch_search_view_pager),
    ("ui/Adapters/StickersAdapter.java", patch_stickers_adapter),
    ("ui/Components/SuggestEmojiView.java", patch_suggest_emoji_view),
    ("ui/Components/StickersAlert.java", patch_stickers_alert),
    ("ui/Components/AIEditorAlert.java", patch_ai_editor_alert),
    ("ui/PrivacyControlActivity.java", patch_privacy_controls),
    ("ui/PrivacySettingsActivity.java", patch_privacy_settings_activity),
    ("ui/Components/ChatGreetingsView.java", patch_chat_greetings_view),
    ("ui/Business/ChatAttachAlertQuickRepliesLayout.java", patch_quick_replies_layout),
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
    ("ui/ChatActivity.java", patch_chat_activity_saved_message_tags),
    ("ui/ChatRightsEditActivity.java", patch_chat_rights_edit_activity),
    ("ui/SelectChatUserSheet.java", patch_select_chat_user_sheet),
    ("ui/Components/ChatAttachAlertDocumentLayout.java", patch_document_layout),
    ("ui/Components/PhotoViewerCaptionEnterView.java", patch_photo_viewer_caption),
    ("ui/Components/CaptionPhotoViewer.java", patch_caption_photo_viewer),
    ("messenger/FileUploadOperation.java", patch_file_upload_operation),
    ("ui/Stories/recorder/CaptionContainerView.java", patch_caption_container_view),
    ("ui/Stories/recorder/CaptionStory.java", patch_caption_story),
    ("messenger/video/VideoAds.java", patch_video_ads),
    ("ui/Adapters/DialogsSearchAdapter.java", patch_dialogs_search_adapter),
    ("ui/ActionBar/Theme.java", patch_theme),
    ("ui/ThemePreviewActivity.java", patch_theme_preview_activity),
    ("ui/Components/ChatThemeBottomSheet.java", patch_chat_theme_bottom_sheet),
    ("ui/Cells/AppIconsSelectorCell.java", patch_app_icons_selector),
    ("ui/Cells/StickerCell.java", patch_sticker_cell),
    ("ui/Cells/StickerEmojiCell.java", patch_sticker_emoji_cell),
    ("ui/Cells/AvailableReactionCell.java", patch_available_reaction_cell),
    ("ui/TopicCreateFragment.java", patch_topic_create_fragment),
    ("ui/bots/SetupEmojiStatusSheet.java", patch_setup_emoji_status_sheet),
    ("ui/Components/EmojiPacksAlert.java", patch_emoji_packs_alert),
    ("ui/ReactionsDoubleTapManageActivity.java", patch_reactions_double_tap_manage),
    ("ui/Components/StickerSetBulletinLayout.java", patch_sticker_set_bulletin_layout),
    ("ui/LanguageSelectActivity.java", patch_language_select_activity),
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
    premium_source_files = tuple(dict.fromkeys(
        relative_path
        for paths in PREMIUM_GATE_TARGETS.values()
        for relative_path in paths
    ))
    required.extend(
        "TMessagesProj/src/main/java/org/telegram/" + relative_path
        for relative_path in premium_source_files
    )
    require_files(upstream_root, tuple(required))

    validate_catalog_mapping()
    helper_path, helper_source = stage_java_helper(upstream_root)
    validate_account_storage_source(helper_source)
    local_profile_style_path, local_profile_style_source = stage_local_profile_style(upstream_root)
    freemium_modules = [
        str(path.relative_to(repo_root))
        for path in (repo_root / "patches/freemium").rglob("*.py")
    ]
    assert_no_standalone_theme_ui_modules(freemium_modules)
    preview_path = java_root / "org/telegram/ui/PremiumPreviewFragment.java"

    staged: list[StagedFile] = []
    helper_original = helper_path.read_text(encoding="utf-8") if helper_path.exists() else None
    if helper_original != helper_source:
        staged.append(StagedFile(helper_path, helper_original, helper_source))
    local_profile_style_original = local_profile_style_path.read_text(encoding="utf-8") if local_profile_style_path.exists() else None
    if local_profile_style_original != local_profile_style_source:
        staged.append(StagedFile(local_profile_style_path, local_profile_style_original, local_profile_style_source))

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
        "Freemium V2 applied: account-local activation and audited Premium/Business "
        "entry, gate, and client action-path integrations. Server-dependent operations "
        "remain subject to Telegram server acceptance. "
        f"Upstream revision: {upstream_revision}."
    )


if __name__ == "__main__":
    apply_freemium()
