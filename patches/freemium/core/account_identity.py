"""Identitas stabil Freemium; currentAccount hanya locator slot Telegram."""

def resolve_client_user_id_expression(account_expression: str = "account") -> str:
    """Bangun ekspresi Java yang membaca clientUserId, bukan nomor slot."""
    if not account_expression or not account_expression.replace("_", "").isalnum():
        raise ValueError("Invalid Java account expression")
    return "UserConfig.getInstance(" + account_expression + ").getClientUserId()"
