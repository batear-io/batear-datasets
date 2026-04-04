#!/usr/bin/env python3
"""Scan all audio files and regenerate metadata/samples.json.

Walks field-tests/ and synthetic/ directories, reads WAV headers, infers
category/subcategory/timestamp from the directory structure and filename,
and writes a complete samples.json registry.

Usage:
    python generate_metadata.py [--repo-root <path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import wave
from datetime import datetime, timezone
from pathlib import Path

AUDIO_EXTENSIONS = {".wav"}
SCAN_DIRS = ["field-tests", "synthetic"]

CATEGORY_MAP = {
    "DJI":              ("drone", None),
    "mavic":            ("drone", "mavic"),
    "esp32-s3-onboard": ("drone", "esp32-capture"),
    "ambient":          ("ambient", None),
    "urban":            ("ambient", "urban"),
    "rural":            ("ambient", "rural"),
    "bat-sites":        ("ambient", "bat-sites"),
    "sine-sweeps":      ("synthetic", "sine-sweep"),
}

TIMESTAMP_RE = re.compile(r"(\d{8})[_T](\d{6})")


def infer_category(rel_path: Path) -> tuple[str, str]:
    """Derive category and subcategory from the file's directory path."""
    parts = rel_path.parts
    category, subcategory = "unknown", "unknown"
    for part in reversed(parts):
        if part in CATEGORY_MAP:
            cat, sub = CATEGORY_MAP[part]
            category = cat
            if sub:
                subcategory = sub
            break
    if subcategory == "unknown":
        for part in parts:
            if part in CATEGORY_MAP:
                _, sub = CATEGORY_MAP[part]
                if sub:
                    subcategory = sub
    return category, subcategory


def infer_timestamp(filename: str) -> str | None:
    """Try to parse a UTC timestamp from the filename (YYYYMMDD_HHMMSS)."""
    m = TIMESTAMP_RE.search(filename)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def file_id(rel_path: Path) -> str:
    """Generate a stable, short ID from the relative path."""
    digest = hashlib.sha256(str(rel_path).encode()).hexdigest()[:8]
    stem = rel_path.stem.lower().replace(" ", "-")
    return f"{stem}-{digest}"


def is_lfs_pointer(path: Path) -> bool:
    """Return True if the file is a Git LFS pointer instead of real content."""
    try:
        with path.open("rb") as f:
            head = f.read(512)
        return head.startswith(b"version https://git-lfs.github.com/spec/v1")
    except Exception:
        return False


def read_wav_info(path: Path) -> dict | None:
    """Extract audio properties from a WAV file header.

    Returns None when the file cannot be read (e.g. LFS pointer).
    """
    if is_lfs_pointer(path):
        return None
    try:
        with wave.open(str(path), "rb") as w:
            sr = w.getframerate()
            ch = w.getnchannels()
            sw = w.getsampwidth() * 8
            frames = w.getnframes()
            duration = round(frames / sr, 3)
    except wave.Error:
        return None
    return {
        "sample_rate_hz": sr,
        "bit_depth": sw,
        "channels": ch,
        "duration_sec": duration,
    }


def scan(repo_root: Path) -> list[dict]:
    """Scan all audio files and return a list of sample metadata dicts."""
    samples = []
    for scan_dir in SCAN_DIRS:
        base = repo_root / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            rel = path.relative_to(repo_root)
            category, subcategory = infer_category(rel)
            timestamp = infer_timestamp(path.name)
            info = read_wav_info(path)
            if info is None:
                print(f"  SKIP (not a valid WAV / LFS pointer): {rel}")
                continue
            entry = {
                "id": file_id(rel),
                "filename": str(rel),
                "category": category,
                "subcategory": subcategory,
                **info,
                "timestamp_utc": timestamp,
            }
            samples.append(entry)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate metadata/samples.json from audio files.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of tools/).",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    samples = scan(repo_root)

    manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "Master registry for Batear acoustic datasets",
        "version": "0.1.0",
        "samples": samples,
    }

    out = repo_root / "metadata" / "samples.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Generated {out} with {len(samples)} sample(s).")


if __name__ == "__main__":
    main()
