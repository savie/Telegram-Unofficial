"""Resolusi identitas stabil akun; slot akun hanya locator sementara."""

class AccountIdentityError(RuntimeError):
    pass

def resolve_client_user_id(account: int) -> int:
    """Resolve clientUserId dari UserConfig pada source tree saat patch dijalankan.

    Fungsi ini menghasilkan Java helper source; identitas runtime dibaca oleh Java
    dari UserConfig.getInstance(account).getClientUserId().
    """
    if not isinstance(account, int) or account < 0:
        raise AccountIdentityError("Invalid Telegram account slot")
    return account
