"""Utilitas patch gate lokal dengan anchor dan jumlah penggantian yang eksplisit."""
IMPORT_ANCHOR = "import org.telegram.messenger.UserConfig;"
FREEMIUM_IMPORT = "import org.telegram.messenger.TeleBetaFreemium;"


def patch_local_premium_checks(source: str, replacements: tuple[tuple[str, str, int], ...]) -> str:
    """Alihkan hanya pemeriksaan Premium client-side yang diaudit."""
    already_imported = FREEMIUM_IMPORT in source
    if not already_imported:
        if source.count(IMPORT_ANCHOR) != 1:
            raise RuntimeError("UserConfig import anchor must exist exactly once")
        source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + FREEMIUM_IMPORT, 1)

    for old, new, expected_count in replacements:
        old_count = source.count(old)
        new_count = source.count(new)
        if old_count == expected_count:
            source = source.replace(old, new)
        elif old_count == 0 and new_count == expected_count:
            continue
        else:
            raise RuntimeError(
                f"Premium gate anchor mismatch: expected {expected_count} occurrences, "
                f"found old={old_count}, new={new_count}"
            )
    return source
