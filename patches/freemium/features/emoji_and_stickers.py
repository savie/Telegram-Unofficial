"""Animated Emoji, Emoji Statuses, Infinite Reactions dan Premium Stickers."""
from ..integration.premium_feature_gates import patch_local_premium_checks
from .message_effects import patch_effect_emoji_picker, patch_effect_reaction_picker

TARGETS = (
    "messenger/MediaDataController.java",
    "ui/SelectAnimatedEmojiDialog.java",
    "ui/Components/ReactionsContainerLayout.java",
    "ui/Components/Reactions/CustomEmojiReactionsWindow.java",
    "ui/Components/StickersAlert.java",
    "ui/Adapters/StickersAdapter.java",
    "ui/Components/SuggestEmojiView.java",
    "ui/Cells/StickerCell.java",
    "ui/Cells/StickerEmojiCell.java",
    "ui/Cells/AvailableReactionCell.java",
    "ui/TopicCreateFragment.java",
    "ui/bots/SetupEmojiStatusSheet.java",
    "ui/Components/EmojiPacksAlert.java",
    "ui/ReactionsDoubleTapManageActivity.java",
    "ui/Components/StickerSetBulletinLayout.java",
)


def patch_media_data_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_select_animated_emoji_dialog(source: str) -> str:
    source = patch_effect_emoji_picker(source)
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 8),
    ))


def patch_reactions_container(source: str) -> str:
    source = patch_effect_reaction_picker(source)
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 7),
    ))


def patch_stickers_alert(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_sticker_cell(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(UserConfig.selectedAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)", 2),
    ))


def patch_sticker_emoji_cell(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_available_reaction_cell(source: str) -> str:
    anchor = "UserConfig.getInstance(currentAccount).isPremium()"
    replacement = "TeleBetaFreemium.hasAllAccess(currentAccount)"
    old_count = source.count(anchor)
    if old_count != 1:
        raise RuntimeError(
            "AvailableReactionCell Premium gate mismatch: "
            f"expected exactly 1 anchor, found {old_count}"
        )
    return patch_local_premium_checks(source, (
        (anchor, replacement, 1),
    ))


def patch_topic_create_fragment(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))



def patch_setup_emoji_status_sheet(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_emoji_packs_alert(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(UserConfig.selectedAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)", 3),
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 4),
    ))


def patch_reactions_double_tap_manage(source: str) -> str:
    replacements = (
        (
            "getUserConfig().isPremium()",
            "TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
        (
            "UserConfig.getInstance(currentAccount).isPremium()",
            "TeleBetaFreemium.hasAllAccess(currentAccount)",
            1,
        ),
    )
    for anchor, _, expected_count in replacements:
        old_count = source.count(anchor)
        if old_count != expected_count:
            raise RuntimeError(
                "ReactionsDoubleTapManageActivity Premium gate mismatch: "
                f"expected {expected_count} occurrence(s) of {anchor!r}, "
                f"found {old_count}"
            )
    return patch_local_premium_checks(source, replacements)



def patch_sticker_set_bulletin_layout(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!UserConfig.getInstance(UserConfig.selectedAccount).isPremium()", "!TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount)", 1),
        ("final boolean isPremium = UserConfig.getInstance(UserConfig.selectedAccount).isPremium();", "final boolean isPremium = TeleBetaFreemium.hasAllAccess(UserConfig.selectedAccount);", 1),
    ))



def patch_mentions_adapter(source: str) -> str:
    """Buka penyisipan Premium Stickers dan Animated Emoji pada mention picker."""
    return patch_local_premium_checks(source, (
        ("!UserConfig.getInstance(currentAccount).isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
        ("SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()", "SharedConfig.suggestAnimatedEmoji && TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_content_preview_viewer(source: str) -> str:
    """Buka preview sticker Premium memakai entitlement account-local."""
    return patch_local_premium_checks(source, (
        ("!AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))

def patch_custom_emoji_reactions_window(source: str) -> str:
    """Buka gate pemilihan Premium Reaction untuk entitlement lokal Tele-ß."""
    anchor = (
        "!UserConfig.getInstance("
        "baseFragment.getCurrentAccount()).isPremium()"
    )
    replacement = (
        "!TeleBetaFreemium.hasAllAccess("
        "baseFragment.getCurrentAccount())"
    )

    method_start = source.find("protected void onEmojiSelected(")
    method_end = source.find(
        "\n    private void showUnlockPremiumAlert()",
        method_start,
    )
    if method_start < 0 or method_end < 0:
        raise RuntimeError(
            "CustomEmojiReactionsWindow.onEmojiSelected anchor not found"
        )

    method_source = source[method_start:method_end]
    old_count = method_source.count(anchor)
    if old_count != 1:
        raise RuntimeError(
            "Expected exactly one Premium gate in onEmojiSelected, "
            f"found {old_count}"
        )

    return patch_local_premium_checks(
        source,
        ((anchor, replacement, 1),),
    )



def _replace_exact_local(source: str, old: str, new: str, expected: int, label: str) -> str:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == expected:
        return source.replace(old, new, expected)
    if old_count == 0 and new_count == expected:
        return source
    raise RuntimeError(
        f"{label}: expected {expected} anchor(s), found old={old_count}, patched={new_count}"
    )


def _ensure_freemium_import(source: str, label: str) -> str:
    import_line = "import org.telegram.messenger.TeleBetaFreemium;\n"
    if import_line in source:
        return source
    anchor = "import org.telegram.messenger.UserConfig;\n"
    if source.count(anchor) != 1:
        raise RuntimeError(f"{label}: UserConfig import anchor must occur exactly once")
    return source.replace(anchor, anchor + import_line, 1)


def patch_stickers_adapter(source: str) -> str:
    source = _ensure_freemium_import(source, "StickersAdapter")
    return _replace_exact_local(
        source,
        "SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()",
        "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.isActive(currentAccount))",
        1,
        "StickersAdapter animated emoji suggestion gate",
    )


def patch_suggest_emoji_view(source: str) -> str:
    source = _ensure_freemium_import(source, "SuggestEmojiView")
    return _replace_exact_local(
        source,
        "SharedConfig.suggestAnimatedEmoji && UserConfig.getInstance(currentAccount).isPremium()",
        "SharedConfig.suggestAnimatedEmoji && (UserConfig.getInstance(currentAccount).isPremium() || TeleBetaFreemium.isActive(currentAccount))",
        2,
        "SuggestEmojiView animated emoji suggestion gates",
    )


def patch_stickers_alert(source: str) -> str:
    source = _ensure_freemium_import(source, "StickersAlert")
    source = _replace_exact_local(
        source,
        """    private void checkPremiumStickers() {
        if (stickerSet != null) {
            stickerSet = MessagesController.getInstance(currentAccount).filterPremiumStickers(stickerSet);""",
        """    private void checkPremiumStickers() {
        if (stickerSet != null && !TeleBetaFreemium.isActive(currentAccount)) {
            stickerSet = MessagesController.getInstance(currentAccount).filterPremiumStickers(stickerSet);""",
        1,
        "StickersAlert filterPremiumStickers gate",
    )
    source = _replace_exact_local(
        source,
        "if (!UserConfig.getInstance(currentAccount).isPremium() && MessageObject.isPremiumEmojiPack(stickerSet))",
        "if (!UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.isActive(currentAccount) && MessageObject.isPremiumEmojiPack(stickerSet))",
        1,
        "StickersAlert pack description gate",
    )
    source = _replace_exact_local(
        source,
        "stickerSet.set.emojis && !UserConfig.getInstance(currentAccount).isPremium() && customButtonDelegate == null",
        "stickerSet.set.emojis && !UserConfig.getInstance(currentAccount).isPremium() && !TeleBetaFreemium.isActive(currentAccount) && customButtonDelegate == null",
        1,
        "StickersAlert pack_gate",
    )
    return source
