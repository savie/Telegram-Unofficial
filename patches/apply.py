#!/usr/bin/env python3
"""Orkestrasi patch build Tele-ß."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from branding.patch import configure_api, configure_branding, configure_standalone_suffix
from build_cache.patch import configure_native_build_cache
from firebase.patch import configure_firebase, remove_library_google_services_plugin
from freemium.patch import apply_freemium
from freemium.quick_replies import apply_local_quick_replies
from freemium.download_manager import apply_local_download_manager
from signing.patch import configure_signing


def main() -> None:
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
