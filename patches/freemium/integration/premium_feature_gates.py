"""Pemetaan audit 26 kategori Premium ke source upstream; bukan grant per fitur."""
IMPORT_ANCHOR = "import org.telegram.messenger.UserConfig;"
FREEMIUM_IMPORT = "import org.telegram.messenger.TeleBetaFreemium;"

PREMIUM_GATE_TARGETS = {
    "Stories": (
        "ui/Stories/StealthModeAlert.java",
        "ui/Stories/SelfStoryViewsPage.java",
        "ui/DialogsActivity.java",
    ),
    "Unlimited Cloud Storage": (
        "messenger/FileLoader.java",
        "messenger/MessagesController.java",
    ),
    "Doubled Limits": (
        "messenger/MessagesController.java",
        "ui/DialogsActivity.java",
        "ui/Components/ChatActivityEnterView.java",
        "messenger/SavedMessagesController.java",
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
    ),
    "Animated Emoji": (
        "ui/SelectAnimatedEmojiDialog.java",
        "messenger/MediaDataController.java",
    ),
    "Emoji Statuses": (
        "ui/SelectAnimatedEmojiDialog.java",
        "ui/PeerColorActivity.java",
    ),
    "Tags in Saved Messages": ("ui/Components/SearchTagsList.java",),
    "Name and Profile Colors": (
        "ui/PeerColorActivity.java",
        "ui/ProfileActivity.java",
    ),
    "Wallpaper for Both Sides": ("ui/ChatEditActivity.java",),
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
        "messenger/SavedMessagesController.java",
    ),
    "No Ads": (
        "ui/DialogsActivity.java",
        "messenger/MessagesController.java",
        "ui/SponsoredMessageInfoView.java",
        "messenger/video/VideoAds.java",
    ),
    "Premium App Icons": (
        "ui/Cells/AppIconsSelectorCell.java",
        "ui/Components/Premium/PremiumAppIconsPreviewView.java",
    ),
    "Infinite Reactions": ("ui/Components/ReactionsContainerLayout.java",),
    "Animated Profile Pictures": (
        "ui/ProfileActivity.java",
        "ui/ProfileActivity2.java",
    ),
    "Premium Stickers": (
        "ui/Components/StickersAlert.java",
        "messenger/MediaDataController.java",
    ),
    "Message Effects": (
        "ui/Components/ReactionsContainerLayout.java",
        "ui/SelectAnimatedEmojiDialog.java",
        "ui/Components/ChatActivityEnterView.java",
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
    if FREEMIUM_IMPORT not in source:
        if "package org.telegram.messenger;" not in source:
            if source.count(IMPORT_ANCHOR) != 1:
                raise RuntimeError("UserConfig import anchor must exist exactly once")
            source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + FREEMIUM_IMPORT, 1)

    for old, new, expected_count in replacements:
        old_count = source.count(old)
        new_count = source.count(new)
        if old_count == expected_count:
            source = source.replace(old, new)
        elif old_count == 0 and new_count == expected_count:
            continue
        else:
            raise RuntimeError(
                f"Premium gate anchor mismatch: expected {expected_count} occurrences, "
                f"found old={old_count}, new={new_count}"
            )
    return source
