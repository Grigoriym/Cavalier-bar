#!/usr/bin/env python3
"""
Sets the Cavalier bar's foreground gradient from the current desktop wallpaper.

Reads the active wallpaper via gsettings (works with any tool that updates
org.cinnamon.desktop.background picture-uri, including time-of-day wallpaper
extensions), extracts two representative colors from it, and writes them into
a dedicated "Wallpaper Accent" color profile in Cavalier's config.json. If the
bar is currently running, it's restarted so the new colors take effect
immediately (Cavalier only reads config.json at startup).

Intended to run periodically (see cavalier-wallpaper-accent.timer), not
continuously - it's a poll, not a watcher.
"""
import colorsys
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

CONFIG_PATH = Path.home() / ".config" / "Nickvision Cavalier" / "config.json"
PROFILE_NAME = "Wallpaper Accent"
CAVALIER_BIN = Path(__file__).resolve().parents[2] / "NickvisionCavalier.GNOME" / "bin" / "Debug" / "net10.0" / "NickvisionCavalier.GNOME"


def get_wallpaper_path() -> Path:
    out = subprocess.run(
        ["gsettings", "get", "org.cinnamon.desktop.background", "picture-uri"],
        check=True, capture_output=True, text=True,
    ).stdout.strip().strip("'")
    return Path(unquote(urlparse(out).path))


# The bar is drawn directly over the wallpaper, so reusing a color literally
# sampled from it (typically desaturated/mid-brightness, like any photo) makes
# it blend in and vanish. We only borrow the *hue* from the wallpaper - the
# saturation/brightness are fixed high so the bar always pops against the
# (usually much less saturated) photo behind it.
ACCENT_SATURATION = 0.85
ACCENT_VALUE = 0.95


def extract_gradient_colors(image_path: Path) -> tuple[str, str]:
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((200, 200))
    counts = img.getcolors(maxcolors=img.width * img.height) or []

    candidates = []
    for count, (r, g, b) in counts:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s >= 0.2 and 0.1 <= v <= 0.95:
            candidates.append((count, h))
    if not candidates:
        # Wallpaper is very flat/washed out - fall back to a safe blue gradient.
        return "#ff1e3a8a", "#ff38bdf8"

    candidates.sort(key=lambda c: c[0], reverse=True)
    top = candidates[:12]
    primary_hue = top[0][1]

    def hue_distance(a, b):
        d = abs(a - b)
        return min(d, 1 - d)

    secondary_hue = max(
        (h for _, h in top[1:]), key=lambda h: hue_distance(primary_hue, h), default=primary_hue
    )
    # Keep the two stops visually distinct even if the wallpaper is near-monochrome.
    if hue_distance(primary_hue, secondary_hue) < 0.08:
        secondary_hue = (primary_hue + 0.12) % 1.0

    def to_hex(hue):
        r, g, b = colorsys.hsv_to_rgb(hue, ACCENT_SATURATION, ACCENT_VALUE)
        return "#ff{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))

    return to_hex(primary_hue), to_hex(secondary_hue)


def update_config(fg_colors: tuple[str, str]) -> int:
    config = json.loads(CONFIG_PATH.read_text())
    profiles = config["ColorProfiles"]

    existing = next((i for i, p in enumerate(profiles) if p["Name"] == PROFILE_NAME), None)
    active = profiles[config["ActiveProfile"]]
    profile = {
        "Name": PROFILE_NAME,
        "FgColors": list(fg_colors),
        "BgColors": list(active["BgColors"]),
        "Theme": active["Theme"],
    }

    if existing is not None:
        profiles[existing] = profile
        index = existing
    else:
        profiles.append(profile)
        index = len(profiles) - 1

    config["ActiveProfile"] = index
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    return index


def restart_if_running() -> None:
    running = subprocess.run(
        ["pgrep", "-f", str(CAVALIER_BIN)], capture_output=True
    ).returncode == 0
    if not running:
        return
    subprocess.run(["pkill", "-9", "-f", str(CAVALIER_BIN)])
    subprocess.run(["pkill", "-9", "-f", "^cava "])
    subprocess.Popen(
        [str(CAVALIER_BIN)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL, start_new_session=True,
    )


def main() -> int:
    try:
        wallpaper = get_wallpaper_path()
        if not wallpaper.is_file():
            print(f"wallpaper_accent: wallpaper path does not exist: {wallpaper}", file=sys.stderr)
            return 1
        colors = extract_gradient_colors(wallpaper)
        update_config(colors)
        restart_if_running()
        print(f"wallpaper_accent: set {colors} from {wallpaper.name}")
        return 0
    except Exception as e:
        print(f"wallpaper_accent: failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
