"""Validasi statis namespace entitlement account-local."""
def validate_account_storage_source(source: str) -> None:
    required = (
        "getClientUserId()",
        "getSharedPreferences(",
        "PREFIX + userId",
        'getBoolean("active", false)',
        'getLong("activated_at"',
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise AssertionError("Account-local storage missing: " + ", ".join(missing))
    prohibited = ("PREFIX + account", "PREFIX + currentAccount", "prefs_" + '" + account')
    found = [token for token in prohibited if token in source]
    if found:
        raise AssertionError("Account slot used as persistent identity: " + ", ".join(found))
