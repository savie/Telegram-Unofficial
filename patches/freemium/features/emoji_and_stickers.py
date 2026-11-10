"""Animated Emoji, Emoji Statuses, Infinite Reactions dan Premium Stickers."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "messenger/MediaDataController.java",
    "ui/SelectAnimatedEmojiDialog.java",
    "ui/Components/ReactionsContainerLayout.java",
    "ui/Components/StickersAlert.java",
    "ui/Cells/StickerEmojiCell.java",
    "ui/Cells/AvailableReactionCell.java",
    "ui/TopicCreateFragment.java",
)


def patch_media_data_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_select_animated_emoji_dialog(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 8),
    ))


def patch_reactions_container(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 7),
    ))


def patch_stickers_alert(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_sticker_emoji_cell(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_available_reaction_cell(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_topic_create_fragment(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("getUserConfig().isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
