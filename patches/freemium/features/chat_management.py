"""Advanced Chat Management: batas pinned dialogs di Saved Messages."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("messenger/SavedMessagesController.java",)


def patch_saved_messages_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
