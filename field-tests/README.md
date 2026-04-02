# Field Tests

Real-world acoustic recordings captured in various environments.

## Subdirectories

| Directory | Description |
|---|---|
| `DJI/mavic/` | DJI Mavic Pro/Air motor noise profiles at various distances and flight modes |
| `esp32-s3-onboard/` | Samples captured directly from Batear ESP32-S3 sensor nodes |
| `ambient/urban/` | Negative samples — city traffic, HVAC, pedestrian noise (no drones) |
| `ambient/rural/` | Negative samples — wind, insects, birdsong (no drones) |
| `ambient/bat-sites/` | Negative samples — bat echolocation and nocturnal wildlife (no drones) |

## Recording Guidelines

- Format: WAV (16-bit PCM preferred)
- Minimum sample rate: 44.1 kHz (will be downsampled to 16 kHz for inference)
- Include metadata entry in `../metadata/samples.json` for every new file
