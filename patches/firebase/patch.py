"""Pengaturan Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")
GOOGLE_SERVICES_PLUGIN = "apply plugin: 'com.google.gms.google-services'"

def configure_firebase():
    module = ROOT / "TMessagesProj/build.gradle"
    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    module_text = module.read_text(encoding="utf-8")
    app_text = standalone.read_text(encoding="utf-8")
    if module_text.count(GOOGLE_SERVICES_PLUGIN) != 1:
        raise SystemExit("Unexpected Google Services plugin declaration in TMessagesProj.")
    module.write_text(module_text.replace(GOOGLE_SERVICES_PLUGIN, "", 1), encoding="utf-8")
    if GOOGLE_SERVICES_PLUGIN not in app_text:
        raise SystemExit("Google Services plugin must remain enabled in standalone app.")

    (ROOT / "TMessagesProj/google-services.json").unlink(missing_ok=True)
    firebase_text = os.environ.get("FIREBASE_GOOGLE_SERVICES_JSON", "").strip()
    if not firebase_text:
        raise SystemExit("FIREBASE_GOOGLE_SERVICES_JSON is required.")
    try:
        config = json.loads(firebase_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FIREBASE_GOOGLE_SERVICES_JSON is invalid JSON: {exc}") from exc
    clients = config.get("client", [])
    if not any(c.get("client_info", {}).get("android_client_info", {}).get("package_name") == "org.telebeta.messenger" for c in clients):
        raise SystemExit("Firebase config has no Android client for org.telebeta.messenger.")
    (ROOT / "TMessagesProj_AppStandalone/google-services.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    if GOOGLE_SERVICES_PLUGIN in module.read_text(encoding="utf-8") or GOOGLE_SERVICES_PLUGIN not in standalone.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin scope validation failed.")
