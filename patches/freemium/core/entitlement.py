"""Model tier tunggal FREE/FREEMIUM; tidak menyimpan feature grants."""
from dataclasses import dataclass
from enum import Enum

class Tier(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"

@dataclass(frozen=True)
class AccountEntitlement:
    account_user_id: int
    tier: Tier
    activated_at: int = 0
    schema_version: int = 2
    updated_at: int = 0

def has_all_access(entitlement: AccountEntitlement | None) -> bool:
    return entitlement is not None and entitlement.tier is Tier.FREEMIUM
