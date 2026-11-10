"""Premium App Icons: pertahankan controller upstream, gunakan entitlement akun aktif."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Cells/AppIconsSelectorCell.java",)
PROTECTED = True


def patch_app_icons_selector(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("!UserConfig.hasPremiumOnAccounts()", "!TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
        (
            "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked())",
            "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(currentAccount))",
            1,
        ),
    ))
