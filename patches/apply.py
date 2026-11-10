#!/usr/bin/env python3
"""Orkestrasi patch build Tele-ß."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
UPSTREAM_ROOT = REPO_ROOT / "upstream"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from branding.patch import configure_api, configure_branding, configure_standalone_suffix
from build_cache.patch import configure_native_build_cache
from firebase.patch import configure_firebase, remove_library_google_services_plugin
from freemium.patch import apply_freemium
from freemium.quick_replies import apply_local_quick_replies
from freemium.download_manager import apply_local_download_manager
from signing.patch import configure_signing


def validate_workspace() -> None:
    required_paths = (
        UPSTREAM_ROOT / "gradlew",
        UPSTREAM_ROOT / "gradle.properties",
        UPSTREAM_ROOT / "TMessagesProj/build.gradle",
        UPSTREAM_ROOT / "TMessagesProj_AppStandalone/build.gradle",
    )
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_paths if not path.is_file()]
    if missing:
        raise SystemExit(
            "Vendored Telegram source is incomplete under upstream/: "
            + ", ".join(missing)
        )


def main() -> None:
    validate_workspace()
    configure_api()
    configure_signing()
    configure_branding()
    remove_library_google_services_plugin()
    configure_standalone_suffix()
    configure_firebase()
    configure_native_build_cache()
    apply_freemium()
    apply_local_quick_replies()
    apply_local_download_manager()
    print("All Tele-ß build patches applied.")


if __name__ == "__main__":
    main()
