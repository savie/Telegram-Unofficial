"""Pengaturan Firebase untuk aplikasi standalone Tele-ß."""
import json
import os
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def configure_firebase():
    plugin = "apply plugin: 'com.google.gms.google-services'"
    if module_text.count(plugin) != 1:
        raise SystemExit("Unexpected Google Services plugin declaration in TMessagesProj.")
    module.write_text(module_text.replace(plugin, "", 1), encoding="utf-8")

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
    app_firebase = ROOT / "TMessagesProj_AppStandalone/google-services.json"
    app_firebase.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    if plugin not in standalone.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must remain enabled in standalone app.")
    if plugin in module.read_text(encoding="utf-8"):
        raise SystemExit("Google Services plugin must not be enabled in library module.")
    final_props = props.read_text(encoding="utf-8")
    if "APP_PACKAGE=org.telebeta.messenger" not in final_props:
        raise SystemExit("APP_PACKAGE identity validation failed.")
