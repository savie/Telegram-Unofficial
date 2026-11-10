"""Integrasi gate Premium: pemetaan source dan transformasi pemeriksaan lokal."""
IMPORT_ANCHOR = "import org.telegram.messenger.UserConfig;"
FREEMIUM_IMPORT = "import org.telegram.messenger.TeleBetaFreemium;"

PREMIUM_GATE_TARGETS = {
    "Stories": ("ui/Stories/StealthModeAlert.java", "ui/Stories/SelfStoryViewsPage.java"),
    "Voice-to-Text Conversion": ("ui/Components/TranscribeButton.java",),
    "Real-Time Translation": ("ui/Components/TranslateButton.java", "ui/Components/TranslateAlert3.java"),
    "Faster Download Speed": ("messenger/FileLoader.java", "messenger/FileLoadOperation.java"),
    "Animated Emoji": ("messenger/MediaDataController.java",),
    "Emoji Statuses": ("messenger/MediaDataController.java",),
    "Infinite Reactions": ("ui/Components/ReactionsContainerLayout.java",),
    "Premium Stickers": ("ui/Components/StickersAlert.java",),
    "Tags in Saved Messages": ("ui/Components/SearchTagsList.java",),
    "Name and Profile Colors": ("ui/PeerColorActivity.java",),
    "Paid Messages": ("ui/PrivacyControlActivity.java",),
    "Disable Sharing": ("ui/PrivacyControlActivity.java",),
    "AI Tools": ("ui/Components/AIEditorAlert.java",),
    "Formatting Tools": ("ui/iv/RichEditor.java", "ui/iv/ChatAttachAlertRichLayout.java"),
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
