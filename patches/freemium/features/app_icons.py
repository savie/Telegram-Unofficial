"""Premium App Icons: pertahankan controller upstream, gunakan entitlement akun aktif."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Cells/AppIconsSelectorCell.java",)
PROTECTED = True


def patch_app_icons_selector(source: str) -> str:
    source = patch_local_premium_checks(source, (
        (
            "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked())",
            "if (MessagesController.getInstance(currentAccount).premiumFeaturesBlocked() && !TeleBetaFreemium.hasAllAccess(currentAccount))",
            1,
        ),
    ))

    replacements = (
        (
            "if (icon.premium && !UserConfig.hasPremiumOnAccounts()) {\n                fragment.showDialog",
            "if (icon.premium && !TeleBetaFreemium.hasAllAccess(currentAccount)) {\n                fragment.showDialog",
        ),
        (
            "holderView.bind(icon);",
            "holderView.bind(icon, TeleBetaFreemium.hasAllAccess(currentAccount));",
        ),
        (
            "private void bind(LauncherIconController.LauncherIcon icon) {",
            "private void bind(LauncherIconController.LauncherIcon icon, boolean hasAllAccess) {",
        ),
        (
            "if (icon.premium && !UserConfig.hasPremiumOnAccounts()) {",
            "if (icon.premium && !hasAllAccess) {",
        ),
    )
    for old, new in replacements:
        count = source.count(old)
        if count != 1:
            raise RuntimeError(
                f"App icons gate anchor mismatch: expected one occurrence, found {count}: {old}"
            )
        source = source.replace(old, new, 1)
    return source
