"""Konfigurasi Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def configure_firebase():
    (ROOT / "TMessagesProj/google-services.json").unlink(missing_ok=True)
    firebase_text = os.environ.get("FIREBASE_GOOGLE_SERVICES_JSON", "").strip()
    if not firebase_text:
        raise SystemExit("FIREBASE_GOOGLE_SERVICES_JSON wajib diatur.")
    try:
        config = json.loads(firebase_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FIREBASE_GOOGLE_SERVICES_JSON bukan JSON valid: {exc}") from exc
    clients = config.get("client", [])
    package_name = "org.telebeta.messenger"
    if not any(c.get("client_info", {}).get("android_client_info", {}).get("package_name") == package_name for c in clients):
        raise SystemExit(f"Konfigurasi Firebase tidak memiliki client Android {package_name}.")
    app_firebase = ROOT / "TMessagesProj_AppStandalone/google-services.json"
    app_firebase.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    plugin = "apply plugin: 'com.google.gms.google-services'"
    module = (ROOT / "TMessagesProj/build.gradle").read_text(encoding="utf-8")
    standalone = (ROOT / "TMessagesProj_AppStandalone/build.gradle").read_text(encoding="utf-8")
    if plugin not in standalone or plugin in module:
        raise SystemExit("Google Services plugin harus aktif hanya pada modul standalone.")
