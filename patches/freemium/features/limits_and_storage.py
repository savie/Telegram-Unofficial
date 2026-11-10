"""Doubled Limits dan limit cloud/client workflows yang tetap memakai request upstream."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/ChatRightsEditActivity.java",
    "ui/SelectChatUserSheet.java",
)


def patch_chat_rights_edit_activity(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_select_chat_user_sheet(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!AccountInstance.getInstance(currentAccount).getUserConfig().isPremium()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
