"""Formatting Tools: buka gate editor, toolbar, dan jalur kirim di UI upstream."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/iv/RichEditor.java",
    "ui/iv/ChatAttachAlertRichLayout.java",
)


def patch_rich_editor(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 4),
    ))


def patch_attach_rich_layout(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))
