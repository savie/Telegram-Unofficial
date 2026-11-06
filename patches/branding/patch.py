"""Pengaturan identitas aplikasi Tele-ß dan kredensial Telegram."""
import os
import re
from pathlib import Path

ROOT = Path("upstream/Telegram-Android")

def replace_once(path: Path, pattern: str, replacement: str, label: str, flags=0):
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Patch target berubah atau tidak ditemukan: {label}")
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
    replace_once(manifest, r'android:label="[^"]*"', 'android:label="Tele-ß"', "label aplikasi")

    library = ROOT / "TMessagesProj/build.gradle"
    library_text = library.read_text(encoding="utf-8")
    if not re.search(r"""namespace ['"]org\.telegram\.messenger['"]""", library_text):
        raise SystemExit("Namespace library harus tetap org.telegram.messenger.")

    standalone = ROOT / "TMessagesProj_AppStandalone/build.gradle"
    app_text = standalone.read_text(encoding="utf-8")
    if "namespace 'org.telegram.messenger.web'" not in app_text and 'namespace "org.telegram.messenger.web"' not in app_text:
        raise SystemExit("Namespace standalone harus tetap org.telegram.messenger.web.")
    start = app_text.find("        standalone {")
    if start < 0:
        raise SystemExit("Blok buildTypes.standalone tidak ditemukan.")
    end = app_text.find("\n        }", start)
    if end < 0:
        raise SystemExit("Penutup blok buildTypes.standalone tidak ditemukan.")
    block = app_text[start:end]
    suffix = 'applicationIdSuffix ".web"'
    if block.count(suffix) != 1:
        raise SystemExit("applicationIdSuffix .web pada standalone tidak ditemukan secara unik.")
    block = block.replace(suffix, 'applicationIdSuffix ""', 1)
    standalone.write_text(app_text[:start] + block + app_text[end:], encoding="utf-8")
    if "APP_PACKAGE=org.telebeta.messenger" not in props.read_text(encoding="utf-8"):
        raise SystemExit("Validasi identitas APP_PACKAGE gagal.")
