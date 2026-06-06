#!/usr/bin/env python3
"""
Post-Webflow-export fixup for speaker detail pages.

Ensures speaker.html (the JS-rendered detail template) and
js/speakers.js exist. The actual rendering is client-side from
data/speakers.json — no static speakers/*.html files needed.

Also cleans up any legacy speakers/*.html files that may have been
left over from the old static generation approach.

Usage:
    cd /path/to/capetown-2027
    python3 scripts/generate_speakers.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEAKERS_JSON = REPO_ROOT / "data" / "speakers.json"
SPEAKER_HTML = REPO_ROOT / "speaker.html"
SPEAKERS_JS = REPO_ROOT / "js" / "speakers.js"
SPEAKERS_DIR = REPO_ROOT / "speakers"


def main():
    # Verify required files exist
    errors = []

    if not SPEAKERS_JSON.exists():
        errors.append(f"data/speakers.json not found")

    if not SPEAKER_HTML.exists():
        errors.append(f"speaker.html not found (JS-rendered detail template)")

    if not SPEAKERS_JS.exists():
        errors.append(f"js/speakers.js not found")

    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print("\nRun 'git checkout main -- speaker.html js/speakers.js' to restore.")
        return

    speakers = json.loads(SPEAKERS_JSON.read_text())
    print(f"  ✓ data/speakers.json — {len(speakers)} speakers")
    print(f"  ✓ speaker.html — JS-rendered detail template present")
    print(f"  ✓ js/speakers.js — client-side renderer present")

    # Clean up legacy static speaker pages (if any remain)
    if SPEAKERS_DIR.exists():
        legacy = list(SPEAKERS_DIR.glob("*.html"))
        if legacy:
            for f in legacy:
                f.unlink()
                print(f"  ✗ removed legacy: speakers/{f.name}")
            print(f"\n  Removed {len(legacy)} legacy static speaker pages.")
            print(f"  Speaker detail is now served by speaker.html?slug=...")
        else:
            print(f"  ✓ speakers/ directory clean (no legacy static files)")
    else:
        print(f"  ✓ no speakers/ directory (clean)")

    print(f"\nDone. Speaker URLs: speaker.html?slug=<slug>")


if __name__ == "__main__":
    main()
