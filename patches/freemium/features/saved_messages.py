"""Tags in Saved Messages: buka seluruh gate daftar dan interaksi tag lokal."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Components/SearchTagsList.java",)


def patch_search_tags(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()",
         "TeleBetaFreemium.hasAllAccess(currentAccount)", 4),
    ))
