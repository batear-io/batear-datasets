#!/usr/bin/env python3
"""Batch downsampling of audio files to production target sample rate (16 kHz).

Usage:
    python resample.py <input_dir> [--output-dir <dir>] [--target-sr <hz>]

Examples:
    python resample.py ../field-tests/mavic-series/
    python resample.py ../synthetic/sine-sweeps/ --target-sr 8000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import librosa
    import soundfile as sf
except ImportError:
    sys.exit(
        "Missing dependencies. Install them with:\n"
        "  pip install librosa soundfile\n"
    )

AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg"}
DEFAULT_TARGET_SR = 16_000


def resample_file(
    src: Path,
    dst: Path,
    target_sr: int = DEFAULT_TARGET_SR,
) -> dict:
    """Resample a single audio file and return metadata."""
    y, orig_sr = librosa.load(str(src), sr=None, mono=False)
    if y.ndim == 1:
        channels = 1
    else:
        channels = y.shape[0]

    if orig_sr != target_sr:
        y_resampled = librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr)
    else:
        y_resampled = y

    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), y_resampled.T if y_resampled.ndim > 1 else y_resampled, target_sr)

    return {
        "source": str(src),
        "destination": str(dst),
        "original_sr": orig_sr,
        "target_sr": target_sr,
        "channels": channels,
        "duration_sec": round(len(y_resampled.T if y_resampled.ndim > 1 else y_resampled) / target_sr, 3),
    }


def discover_audio_files(directory: Path) -> list[Path]:
    """Recursively find all audio files under *directory*."""
    return sorted(
        p for p in directory.rglob("*") if p.suffix.lower() in AUDIO_EXTENSIONS
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch resample audio to target SR.")
    parser.add_argument("input_dir", type=Path, help="Directory with source audio files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: <input_dir>_resampled).",
    )
    parser.add_argument(
        "--target-sr",
        type=int,
        default=DEFAULT_TARGET_SR,
        help=f"Target sample rate in Hz (default: {DEFAULT_TARGET_SR}).",
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir.resolve()
    if not input_dir.is_dir():
        sys.exit(f"Error: {input_dir} is not a directory.")

    output_dir: Path = (args.output_dir or input_dir.parent / f"{input_dir.name}_resampled").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = discover_audio_files(input_dir)
    if not files:
        print(f"No audio files found in {input_dir}")
        return

    print(f"Found {len(files)} audio file(s). Resampling to {args.target_sr} Hz …")

    manifest: list[dict] = []
    for i, src in enumerate(files, 1):
        rel = src.relative_to(input_dir)
        dst = output_dir / rel.with_suffix(".wav")
        print(f"  [{i}/{len(files)}] {rel}")
        info = resample_file(src, dst, target_sr=args.target_sr)
        manifest.append(info)

    manifest_path = output_dir / "resample_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. Output in {output_dir}")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
