"""Mapping kategori Premium ke source gate; key teknis bukan entitlement."""
PREMIUM_GATE_TARGETS = {
    "Stories": ("ui/Stories/StealthModeAlert.java", "ui/Stories/SelfStoryViewsPage.java"),
    "Voice-to-Text Conversion": ("ui/Components/TranscribeButton.java",),
    "Real-Time Translation": ("ui/Components/TranslateButton.java", "ui/Components/TranslateAlert3.java"),
    "Faster Download Speed": ("messenger/FileLoadOperation.java",),
    "Tags in Saved Messages": ("ui/Components/SearchTagsList.java",),
    "Formatting Tools": ("ui/iv/RichEditor.java", "ui/iv/ChatAttachAlertRichLayout.java"),
}
