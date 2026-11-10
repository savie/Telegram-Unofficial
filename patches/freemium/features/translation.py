"""Real-Time Translation: alihkan gate lokal tanpa mengubah request/response server."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/Components/TranslateButton.java",
    "ui/Components/TranslateAlert3.java",
)


def patch_translate_button(source: str) -> str:
    # The button owns both the translation-menu and language-action gates.
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 3),
    ))


def patch_translate_alert(source: str) -> str:
    # Translate-all action has a separate Premium bottom-sheet gate.
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
