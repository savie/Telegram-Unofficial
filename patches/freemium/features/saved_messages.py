"""Tags in Saved Messages: buka seluruh gate daftar dan interaksi tag lokal."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = ("ui/Components/SearchTagsList.java",)


def patch_search_tags(source: str) -> str:
    anchor = "UserConfig.getInstance(currentAccount).isPremium()"
    replacement = "TeleBetaFreemium.hasAllAccess(currentAccount)"
    expected_count = 4

    old_count = source.count(anchor)
    new_count = source.count(replacement)

    if old_count == 0 and new_count == expected_count:
        return source

    if old_count != expected_count:
        raise RuntimeError(
            "SearchTagsList Premium gate mismatch: "
            f"expected exactly {expected_count} original anchors, "
            f"found {old_count}; replacement count={new_count}"
        )

    return patch_local_premium_checks(source, (
        (anchor, replacement, expected_count),
    ))
