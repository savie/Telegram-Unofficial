"""AI Tools: buka gate client-side; layanan AI tetap mengikuti respons server."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Components/AIEditorAlert.java",)


def patch_ai_editor_alert(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))
