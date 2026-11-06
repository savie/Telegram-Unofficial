"""Pengaturan identitas aplikasi Tele-ß dan kredensial Telegram."""
import os
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def replace_once(path: Path, pattern: str, replacement: str, label: str, flags=0):
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Patch target changed or missing: {label}")
    path.write_text(updated, encoding="utf-8")

def configure_api():
    path = ROOT / "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java"
    app_id = os.environ["TELEGRAM_API_ID"]
    app_hash = os.environ["TELEGRAM_API_HASH"]
    if not app_id.isdigit():
        raise SystemExit("TELEGRAM_API_ID must be numeric.")
    source = path.read_text(encoding="utf-8")
    source, n1 = re.subn(r"public static int APP_ID = [0-9]+;", f"public static int APP_ID = {app_id};", source, count=1)
    source, n2 = re.subn(r'public static String APP_HASH = "[^"]*";', f'public static String APP_HASH = "{app_hash}";', source, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit("BuildVars.java layout changed; refusing to patch credentials.")
    path.write_text(source, encoding="utf-8")

def configure_branding():
    props = ROOT / "gradle.properties"
    replace_once(props, r"(?m)^APP_PACKAGE=.*$", "APP_PACKAGE=org.telebeta.messenger", "APP_PACKAGE")
    manifest = ROOT / "TMessagesProj/config/release/AndroidManifest_standalone.xml"
    replace_once(manifest, r'android:label="[^"]*"', 'android:label="Tele-ß"', "launcher label")

    module = ROOT / "TMessagesProj/build.gradle"
    module_text = module.read_text(encoding="utf-8")
    if not re.search(r"namespace ['\"]org\.telegram\.messenger['\"]", module_text):
        raise SystemExit("TMessagesProj namespace must remain org.telegram.messenger.")

def configure_standalone_suffix():
    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    app_text = standalone.read_text(encoding="utf-8")
    if "namespace 'org.telegram.messenger.web'" not in app_text and 'namespace "org.telegram.messenger.web"' not in app_text:
        raise SystemExit("Standalone namespace must remain org.telegram.messenger.web.")
    app_text, count = re.subn(r'(standalone\s*\{[\s\S]*?applicationIdSuffix\s+)["\']\.web["\']', r'\1""', app_text, count=1)
    if count != 1:
        raise SystemExit("Could not remove standalone .web applicationIdSuffix.")
    standalone.write_text(app_text, encoding="utf-8")
