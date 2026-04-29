#!/usr/bin/env python3
"""Compute per-AudioMoth-WAV distance to one or more drones.

Inputs:
  * AudioMoth SUMMARY.CSV (one row per WAV with Timestamp/Latitude/Longitude/Duration).
    The AudioMoth Configuration App produces this file; GPS values come from the
    GUANO `Loc Position` field embedded in each WAV (acoustic-chime source).
  * One DCIM directory per drone, containing JPGs with EXIF GPSInfo
    (GPSLatitude, GPSLongitude, GPSAltitude) and DateTimeOriginal.

Per WAV (60-second window starting at Timestamp + Duration), the script:
  1. Filters drone EXIF points whose UTC timestamp falls in that window.
  2. Computes horizontal distance (Haversine) and vertical offset
     (drone GPS altitude minus that drone's take-off GPS altitude minus the
     recorder height above take-off ground).
  3. Aggregates min/median/mean/max of the 3D distance, plus horizontal and
     vertical extrema.

Take-off GPS altitude is taken as the altitude of the chronologically first
JPG per drone -- this cancels out the per-receiver GPS-altitude bias so that
"height above recorder" stays meaningful even though absolute GPS altitudes
between two DJI drones can disagree by ~20 m.

Drone EXIF DateTimeOriginal is local time; pass --tz-offset to convert to UTC.

Usage:
    python drone_distance.py \
        --summary K:/.../SUMMARY.CSV \
        --drone mavic-pro=K:/.../mavic/DCIM \
        --drone mini-4-pro=K:/.../mini/DCIM \
        --tz-offset 2 \
        --rec-height 0 \
        --output metadata/audio_drone_distance_<DATE>.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

EARTH_RADIUS_M = 6_371_000.0


def dms_to_deg(dms, ref: str) -> float:
    """Convert EXIF (deg, min, sec) tuple + N/S/E/W ref to signed decimal degrees."""
    d, m, s = (float(x) for x in dms)
    val = d + m / 60 + s / 3600
    return -val if ref in ("S", "W") else val


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def parse_drone_jpg(path: Path, tz_offset_h: float) -> dict | None:
    """Return {t_utc, lat, lon, alt} from EXIF, or None if data missing."""
    img = Image.open(path)
    exif = img._getexif() or {}
    lat = lon = alt = ts_local = None
    for tag_id, val in exif.items():
        name = TAGS.get(tag_id, tag_id)
        if name == "GPSInfo":
            gps = {GPSTAGS.get(k, k): v for k, v in val.items()}
            if "GPSLatitude" in gps and "GPSLongitude" in gps:
                lat = dms_to_deg(gps["GPSLatitude"], gps.get("GPSLatitudeRef", "N"))
                lon = dms_to_deg(gps["GPSLongitude"], gps.get("GPSLongitudeRef", "E"))
                if "GPSAltitude" in gps:
                    alt = float(gps["GPSAltitude"])
        elif name == "DateTimeOriginal":
            ts_local = datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
    if ts_local is None or lat is None or alt is None:
        return None
    t_utc = ts_local - timedelta(hours=tz_offset_h)
    return {"t_utc": t_utc.replace(tzinfo=timezone.utc), "lat": lat, "lon": lon, "alt": alt}


def collect_drone_points(dcim_dir: Path, tz_offset_h: float) -> list[dict]:
    """Walk dcim_dir recursively and parse every JPG. Sorted by UTC time."""
    seen: set[Path] = set()
    points = []
    for jpg in dcim_dir.rglob("*"):
        if jpg.suffix.lower() != ".jpg" or jpg in seen:
            continue
        seen.add(jpg)
        p = parse_drone_jpg(jpg, tz_offset_h)
        if p:
            points.append(p)
    points.sort(key=lambda r: r["t_utc"])
    return points


def read_summary(path: Path) -> list[dict]:
    """Parse AudioMoth SUMMARY.CSV, skipping rows without a timestamp (stub files)."""
    wavs = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("Timestamp"):
                continue
            wavs.append(
                {
                    "fn": row["File Name"],
                    "t_start": datetime.fromisoformat(row["Timestamp"].replace("Z", "+00:00")),
                    "duration": float(row["Duration (s)"]),
                    "lat": float(row["Latitude"]),
                    "lon": float(row["Longitude"]),
                }
            )
    return wavs


def stats_block(samples_d3: list[float], samples_h: list[float], samples_v: list[float]) -> list:
    if not samples_d3:
        return [0, "", "", "", "", "", "", "", ""]
    return [
        len(samples_d3),
        f"{min(samples_d3):.1f}",
        f"{statistics.median(samples_d3):.1f}",
        f"{sum(samples_d3) / len(samples_d3):.1f}",
        f"{max(samples_d3):.1f}",
        f"{min(samples_h):.1f}",
        f"{max(samples_h):.1f}",
        f"{min(samples_v):.1f}",
        f"{max(samples_v):.1f}",
    ]


def header_for_drone(name: str) -> list[str]:
    return [
        f"{name}_n",
        f"{name}_d3d_min_m",
        f"{name}_d3d_median_m",
        f"{name}_d3d_mean_m",
        f"{name}_d3d_max_m",
        f"{name}_horiz_min_m",
        f"{name}_horiz_max_m",
        f"{name}_height_above_rec_min_m",
        f"{name}_height_above_rec_max_m",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--summary", type=Path, required=True, help="Path to AudioMoth SUMMARY.CSV.")
    parser.add_argument(
        "--drone",
        action="append",
        required=True,
        metavar="NAME=DCIM_DIR",
        help="Drone name and DCIM directory (repeat for multiple drones).",
    )
    parser.add_argument(
        "--tz-offset",
        type=float,
        default=0.0,
        help="Hours to subtract from drone EXIF DateTimeOriginal to get UTC (e.g. 2 for CEST).",
    )
    parser.add_argument(
        "--rec-height",
        type=float,
        default=0.0,
        help="Recorder height in meters above local take-off ground (default: 0).",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output CSV path.")
    args = parser.parse_args()

    drones: dict[str, list[dict]] = {}
    takeoff_alt: dict[str, float] = {}
    for spec in args.drone:
        if "=" not in spec:
            parser.error(f"--drone expects NAME=DCIM_DIR, got {spec!r}")
        name, dcim = spec.split("=", 1)
        pts = collect_drone_points(Path(dcim), args.tz_offset)
        if not pts:
            parser.error(f"no usable JPGs found under {dcim}")
        drones[name] = pts
        takeoff_alt[name] = pts[0]["alt"]
        print(
            f"{name}: {len(pts)} points  "
            f"{pts[0]['t_utc']:%Y-%m-%d %H:%M:%S} ... {pts[-1]['t_utc']:%H:%M:%S} UTC  "
            f"take-off ASL = {takeoff_alt[name]:.2f} m"
        )

    wavs = read_summary(args.summary)
    print(f"\nSUMMARY.CSV: {len(wavs)} WAV rows with timestamps")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        header = ["wav_file", "t_start_utc", "duration_s", "rec_lat", "rec_lon"]
        for name in drones:
            header.extend(header_for_drone(name))
        header.append("active_drone")
        w.writerow(header)

        for wav in wavs:
            t0 = wav["t_start"]
            t1 = t0 + timedelta(seconds=wav["duration"])
            rl, rn = wav["lat"], wav["lon"]
            row = [wav["fn"], t0.isoformat().replace("+00:00", "Z"), wav["duration"], f"{rl:.6f}", f"{rn:.6f}"]
            active = []
            for name, pts in drones.items():
                d3, hh, vv = [], [], []
                for p in pts:
                    if t0 <= p["t_utc"] <= t1:
                        h = haversine_m(rl, rn, p["lat"], p["lon"])
                        v = (p["alt"] - takeoff_alt[name]) - args.rec_height
                        d3.append(math.sqrt(h * h + v * v))
                        hh.append(h)
                        vv.append(v)
                row.extend(stats_block(d3, hh, vv))
                if d3:
                    active.append(name)
            row.append("+".join(active) if active else "none")
            w.writerow(row)

    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
