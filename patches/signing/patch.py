"""Penyiapan keystore dan properti signing Tele-ß."""
import base64
import os
from pathlib import Path
import re

ROOT = Path(".")

def configure_signing():
    names = ("TELEBETA_KEYSTORE_BASE64", "TELEBETA_KEYSTORE_PASSWORD", "TELEBETA_KEY_ALIAS", "TELEBETA_KEY_PASSWORD")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing repository secrets: " + ", ".join(missing))
    alias = os.environ["TELEBETA_KEY_ALIAS"]
    if alias != "telebeta-release":
        raise SystemExit("TELEBETA_KEY_ALIAS must be telebeta-release.")
    try:
        raw = base64.b64decode("".join(os.environ["TELEBETA_KEYSTORE_BASE64"].split()), validate=True)
    except Exception as exc:
        raise SystemExit("TELEBETA_KEYSTORE_BASE64 is not valid Base64.") from exc
    if len(raw) < 1024:
        raise SystemExit("Decoded keystore is unexpectedly small.")
    keystore = ROOT / "TMessagesProj/config/release.keystore"
    keystore.parent.mkdir(parents=True, exist_ok=True)
    keystore.write_bytes(raw)
    props = ROOT / "gradle.properties"
    data = props.read_text(encoding="utf-8")
    values = {
        "RELEASE_STORE_PASSWORD": os.environ["TELEBETA_KEYSTORE_PASSWORD"],
        "RELEASE_KEY_ALIAS": alias,
        "RELEASE_KEY_PASSWORD": os.environ["TELEBETA_KEY_PASSWORD"],
    }
    for key, value in values.items():
        data, count = re.subn(rf"(?m)^{key}=.*$", lambda _: f"{key}={value}", data, count=1)
        if count != 1:
            raise SystemExit(f"Could not configure {key}.")
    props.write_text(data, encoding="utf-8")
