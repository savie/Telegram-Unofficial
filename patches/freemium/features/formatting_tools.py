"""Formatting Tools dan Checklists: toolbar, draft, lock state, serta send path."""
from ..integration.premium_feature_gates import patch_local_premium_checks
from .checklists import patch_checklist_attach_layout, patch_checklist_rich_editor

TARGETS = (
    "ui/iv/RichEditor.java",
    "ui/iv/ChatAttachAlertRichLayout.java",
    "ui/Components/ChatActivityEnterView.java",
)


def patch_rich_editor(source: str) -> str:
    source = patch_checklist_rich_editor(source)
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 4),
    ))


def patch_attach_rich_layout(source: str) -> str:
    source = patch_checklist_attach_layout(source)
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))


def patch_chat_activity_enter_view(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 5),
    ))
