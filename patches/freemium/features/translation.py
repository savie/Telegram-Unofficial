"""Real-Time Translation: alihkan gate lokal tanpa mengubah request/response server."""
from ..integration.gate_patch import patch_local_premium_checks

TARGETS = ("ui/Components/TranslateButton.java",)


def patch_translate_button(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 3),
    ))
