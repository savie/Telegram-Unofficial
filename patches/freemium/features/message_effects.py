"""Message Effects: native effect picker, lock state and send-button entitlement routing.

Telegram's effect catalog and effect_id send payload remain upstream-owned. These
patches only replace client-side Premium checks with the local all-access resolver.
"""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/Components/ReactionsContainerLayout.java",
    "ui/SelectAnimatedEmojiDialog.java",
    "ui/Components/ChatActivityEnterView.java",
)


def patch_effect_reaction_picker(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 7),
    ))


def patch_effect_emoji_picker(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 8),
    ))


def patch_effect_send_gate(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))
