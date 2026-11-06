#!/usr/bin/env python3
"""Orkestrasi patch build Tele-ß."""
from branding.patch import configure_api, configure_branding
from firebase.patch import configure_firebase
from freemium.patch import apply_freemium
from signing.patch import configure_signing


def main() -> None:
    # Explicit order: credentials -> signing -> app identity -> Firebase -> Freemium.
    configure_api()
    configure_signing()
    configure_branding()
    configure_firebase()
    apply_freemium()
    print("All Tele-ß build patches applied.")


if __name__ == "__main__":
    main()
