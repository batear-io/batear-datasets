# Metadata

Dataset manifest and labeling information.

## Files

| File | Description |
|---|---|
| `samples.json` | Master registry of all audio samples with sample rate, bit depth, timestamps, and tags |

## Schema

Every entry in `samples.json` must include:

- `id` — unique identifier
- `filename` — relative path from repository root
- `category` — top-level class (`drone`, `bio`, `ambient`, `synthetic`)
- `sample_rate_hz` — original sample rate
- `bit_depth` — bits per sample
- `channels` — mono (1) or stereo (2)
- `duration_sec` — length in seconds
- `timestamp_utc` — ISO 8601 recording timestamp
