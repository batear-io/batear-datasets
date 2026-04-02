#!/usr/bin/env python3
"""Automated spectrogram generation for audio datasets.

Generates mel-spectrogram PNG images suitable for embedding in PRs and
documentation.

Usage:
    python viz_spectrogram.py <input> [--output-dir <dir>] [--n-fft <int>]

Examples:
    python viz_spectrogram.py ../field-tests/mavic-series/hover_10s.wav
    python viz_spectrogram.py ../synthetic/sine-sweeps/ --output-dir ./spectrograms
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import librosa
    import librosa.display
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    sys.exit(
        "Missing dependencies. Install them with:\n"
        "  pip install librosa matplotlib numpy\n"
    )

AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg"}


def generate_spectrogram(
    audio_path: Path,
    output_path: Path,
    *,
    n_fft: int = 2048,
    hop_length: int = 512,
    figsize: tuple[int, int] = (12, 4),
) -> None:
    """Create a mel-spectrogram image from an audio file."""
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)
    S_dB = librosa.power_to_db(S, ref=np.max)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    img = librosa.display.specshow(
        S_dB, sr=sr, hop_length=hop_length,
        x_axis="time", y_axis="mel", ax=ax, cmap="magma",
    )
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title(f"{audio_path.name}  (SR={sr} Hz)", fontsize=10)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)


def discover_audio_files(path: Path) -> list[Path]:
    """Return audio files — works with both a single file and a directory."""
    if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
        return [path]
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.suffix.lower() in AUDIO_EXTENSIONS)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mel-spectrogram images.")
    parser.add_argument("input", type=Path, help="Audio file or directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output PNGs (default: <input>_spectrograms).",
    )
    parser.add_argument("--n-fft", type=int, default=2048, help="FFT window size.")
    parser.add_argument("--hop-length", type=int, default=512, help="Hop length for STFT.")
    args = parser.parse_args()

    input_path: Path = args.input.resolve()
    files = discover_audio_files(input_path)
    if not files:
        sys.exit(f"No audio files found at {input_path}")

    base = input_path if input_path.is_dir() else input_path.parent
    output_dir = (args.output_dir or base.parent / f"{base.name}_spectrograms").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating spectrograms for {len(files)} file(s) …")

    for i, src in enumerate(files, 1):
        rel = src.relative_to(base) if src != input_path else Path(src.name)
        dst = output_dir / rel.with_suffix(".png")
        print(f"  [{i}/{len(files)}] {rel}")
        generate_spectrogram(src, dst, n_fft=args.n_fft, hop_length=args.hop_length)

    print(f"\nDone. Spectrograms saved to {output_dir}")


if __name__ == "__main__":
    main()
