"""Pemetaan audit 26 kategori Premium ke source upstream; bukan grant per fitur."""
FREEMIUM_IMPORT = "import org.telegram.messenger.TeleBetaFreemium;"

PREMIUM_GATE_TARGETS = {
    "Stories": (
        "ui/Stories/StealthModeAlert.java",
        "ui/Stories/SelfStoryViewsPage.java",
        "ui/Stories/StoriesController.java",
        "ui/Stories/recorder/CaptionContainerView.java",
        "ui/DialogsActivity.java",
    ),
    "Unlimited Cloud Storage": (
        "messenger/FileLoader.java",
        "messenger/MessagesController.java",
        "ui/Components/ChatAttachAlertDocumentLayout.java",
    ),
    "Doubled Limits": (
        "messenger/MessagesController.java",
        "ui/DialogsActivity.java",
        "ui/ChatRightsEditActivity.java",
        "ui/SelectChatUserSheet.java",
        "ui/Components/ChatActivityEnterView.java",
        "messenger/SavedMessagesController.java",
        "ui/Components/PhotoViewerCaptionEnterView.java",
    ),
    "Telegram Business": ("ui/PremiumPreviewFragment.java",),
    "Last Seen Times": (
        "ui/PrivacyControlActivity.java",
        "ui/ProfileActivity.java",
        "messenger/ContactsController.java",
        "ui/Components/MessagePrivateSeenView.java",
    ),
    "Voice-to-Text Conversion": ("ui/Components/TranscribeButton.java",),
    "Faster Download Speed": (
        "messenger/FileLoader.java",
        "messenger/FileLoadOperation.java",
        "ui/DialogsActivity.java",
    ),
    "Real-Time Translation": (
        "ui/Components/TranslateButton.java",
        "ui/Components/TranslateAlert3.java",
        "ui/LanguageSelectActivity.java",
    ),
    "Animated Emoji": (
        "ui/SelectAnimatedEmojiDialog.java",
        "ui/Cells/StickerCell.java",
        "ui/Cells/StickerEmojiCell.java",
        "ui/Cells/AvailableReactionCell.java",
        "ui/TopicCreateFragment.java",
        "ui/bots/SetupEmojiStatusSheet.java",
        "ui/Components/EmojiPacksAlert.java",
        "ui/ReactionsDoubleTapManageActivity.java",
        "messenger/MediaDataController.java",
    ),
    "Emoji Statuses": (
        "ui/SelectAnimatedEmojiDialog.java",
        "ui/PeerColorActivity.java",
        "ui/bots/SetupEmojiStatusSheet.java",
    ),
    "Tags in Saved Messages": ("ui/Components/SearchTagsList.java",),
    "Name and Profile Colors": (
        "ui/PeerColorActivity.java",
        "ui/ProfileActivity.java",
    ),
    "Wallpaper for Both Sides": ("ui/ThemePreviewActivity.java",
        "messenger/ChatThemeController.java",),
    "Profile Badge": (
        "ui/ProfileActivity.java",
        "ui/ProfileActivity2.java",
    ),
    "Paid Messages": ("ui/PrivacyControlActivity.java",),
    "Disable Sharing": (
        "ui/PrivacyControlActivity.java",
        "ui/ProfileActivity.java",
    ),
    "Advanced Chat Management": (
        "ui/DialogsActivity.java",
        "ui/ArchiveSettingsActivity.java",
        "ui/FiltersSetupActivity.java",
        "ui/FilterCreateActivity.java",
        "ui/FilterChatlistActivity.java",
        "ui/Components/DialogCellTags.java",
        "ui/Components/FilterTabsView.java",
        "ui/UsersSelectActivity.java",
        "messenger/SavedMessagesController.java",
    ),
    "No Ads": (
        "ui/DialogsActivity.java",
        "messenger/MessagesController.java",
        "ui/SponsoredMessageInfoView.java",
        "messenger/video/VideoAds.java",
        "ui/Adapters/DialogsSearchAdapter.java",
    ),
    "Premium App Icons": (
        "ui/Cells/AppIconsSelectorCell.java",
        "ui/Components/Premium/PremiumAppIconsPreviewView.java",
    ),
    "Infinite Reactions": ("ui/Components/ReactionsContainerLayout.java",
        "ui/Cells/AvailableReactionCell.java",),
    "Animated Profile Pictures": (
        "ui/ProfileActivity.java",
        "ui/ProfileActivity2.java",
    ),
    "Premium Stickers": (
        "ui/Components/StickersAlert.java",
        "ui/Components/StickerSetBulletinLayout.java",
        "ui/Cells/StickerCell.java",
        "ui/Cells/StickerEmojiCell.java",
        "messenger/MediaDataController.java",
    ),
    "Message Effects": (
        "ui/Components/ReactionsContainerLayout.java",
        "ui/SelectAnimatedEmojiDialog.java",
        "ui/Components/ChatActivityEnterView.java",
        "ui/ReactionsDoubleTapManageActivity.java",
        "messenger/SendMessagesHelper.java",
    ),
    "AI Tools": ("ui/Components/AIEditorAlert.java",),
    "Formatting Tools": (
        "ui/iv/RichEditor.java",
        "ui/iv/ChatAttachAlertRichLayout.java",
        "ui/Components/ChatActivityEnterView.java",
    ),
    "Checklists": (
        "ui/iv/RichEditor.java",
        "ui/iv/ChatAttachAlertRichLayout.java",
        "messenger/MessageObject.java",
        "messenger/SendMessagesHelper.java",
    ),
}


def patch_local_premium_checks(source: str, replacements: tuple[tuple[str, str, int], ...]) -> str:
    """Alihkan gate Premium lokal; kelas messenger satu package tidak butuh import."""
    if FREEMIUM_IMPORT not in source and "package org.telegram.messenger;" not in source:
        package_start = source.find("package ")
        package_end = source.find(";", package_start)
        if package_start < 0 or package_end < 0:
            raise RuntimeError("Java package declaration is required for Freemium import")
        source = source[:package_end + 1] + "\n\n" + FREEMIUM_IMPORT + source[package_end + 1:]

    for old, new, expected_count in replacements:
        old_count = source.count(old)
        new_count = source.count(new)
        if old_count == expected_count:
            source = source.replace(old, new)
        elif old_count == 0 and new_count > 0:
            continue
        else:
            raise RuntimeError(
                f"Premium gate anchor mismatch: expected {expected_count} occurrences, "
                f"found old={old_count}, new={new_count}"
            )
    return source
