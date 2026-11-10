"""Static checks for account-keyed storage and prohibited slot-key persistence."""

def validate_account_storage_source(source: str) -> None:
    required = ("getClientUserId()", "getSharedPreferences(")
    missing = [token for token in required if token not in source]
    if missing:
        raise AssertionError("Account-local storage missing: " + ", ".join(missing))
    if "PREFIX + account" in source or "prefs_" + '" + account' in source:
        raise AssertionError("Account slot must not be used as persistent identity")
