"""Checklists: unlock editor checklist actions while preserving Telegram's native TODO model.

The TODO media model, serialization, send path and completion actions are upstream
implementations. This patch only redirects the client-side Premium editor gate to
the account-local Freemium entitlement; it does not synthesize TODO protocol data.
"""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/iv/RichEditor.java",
    "ui/iv/ChatAttachAlertRichLayout.java",
    "messenger/MessageObject.java",
    "messenger/SendMessagesHelper.java",
)


def patch_checklist_rich_editor(source: str) -> str:
    """Unlock checklist/list conversion and editor actions in the native RichEditor."""
    return patch_local_premium_checks(source, (
        (
            "UserConfig.getInstance(currentAccount).isPremium()",
            "TeleBetaFreemium.hasAllAccess(currentAccount)",
            4,
        ),
    ))


def patch_checklist_attach_layout(source: str) -> str:
    """Unlock checklist insertion from the existing chat attachment editor."""
    return patch_local_premium_checks(source, (
        (
            "UserConfig.getInstance(currentAccount).isPremium()",
            "TeleBetaFreemium.hasAllAccess(currentAccount)",
            5,
        ),
    ))
