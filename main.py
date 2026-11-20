#!/usr/bin/env python3
"""Copy the pre-rendered front page to the output directory.

Entry for make.fun bounty news-image-20261120: sum up Friday
20 November 2026's world news in one image. The image
(news-20-nov-2026.png, 1024x1024, under 1 MiB) is a newspaper front
page drawn at build time from the day's verified headlines; this
program just copies it to entry.png in the output directory, as the
kit's starter does. The seven stories on the page are: Russia's
overnight missile and drone barrage on Kyiv that killed eight and
damaged three Dnipro bridges; Russian missiles and a drone entering
Polish airspace; Cyclone Akvan making landfall in Odisha; Estonia
closing its border crossings with Russia from 1 December; Iraqi
forces deploying in the Jurf al-Sakhar militia stronghold; stocks
sliding worldwide as the AI sell-off deepens; and New York Mayor
Mamdani's plan to close Rikers Island by 2032.

Pure Python standard library, deterministic, no network: both runs
write the same bytes. Honours MAKEFUN_OUTPUT_DIR, defaulting to
/output; a blank value counts as unset. The source is checked to be
a whole PNG (magic bytes, IHDR dimensions and IEND trailer) and
under the 1 MiB limit before copying.
"""
import os
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "news-20-nov-2026.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576


def _output_dir():
    """Resolve the output directory from the environment.

    MAKEFUN_OUTPUT_DIR wins when set to a non-blank value; otherwise
    the default /output is used. Leading/trailing whitespace is
    ignored so a stray space cannot create a wrong directory.
    """
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR") or ""
    return Path(raw.strip() or "/output")


def _checked_source():
    """Return SOURCE after verifying it is a whole PNG under 1 MiB.

    Also checks the IHDR width and height, since the gate requires at
    most 1024 by 1024 pixels: a PNG that is valid but oversized must
    never reach the output directory.
    """
    if not SOURCE.is_file():
        raise FileNotFoundError(f"missing entry image: {SOURCE}")
    if SOURCE.stat().st_size > MAX_BYTES:
        raise ValueError(f"entry image over 1 MiB: {SOURCE}")
    with SOURCE.open("rb") as fh:
        head = fh.read(8 + 8 + 13)
        fh.seek(-12, os.SEEK_END)
        tail = fh.read(12)
    if head[:8] != PNG_MAGIC:
        raise ValueError(f"not a PNG file: {SOURCE}")
    if head[12:16] != b"IHDR":
        raise ValueError(f"not a PNG file (no IHDR): {SOURCE}")
    if tail[4:8] != b"IEND":
        raise ValueError(f"not a whole PNG file (no IEND): {SOURCE}")
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    if width > 1024 or height > 1024:
        raise ValueError(
            f"entry image too large: {width}x{height} (max 1024x1024)")
    return SOURCE


def main():
    out_dir = _output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_checked_source(), out_dir / "entry.png")


if __name__ == "__main__":
    main()
