# Batear Datasets

[![Storage: Git LFS](https://img.shields.io/badge/Storage-Git_LFS-blue)](https://git-lfs.github.com/)

A curated collection of acoustic datasets specifically designed for **drone detection**, **signal classification**, and **bio-acoustic interference analysis** on constrained embedded systems (e.g., ESP32-S3).

## 🎯 Project Goals

This repository serves as a standardized benchmark for validating Digital Signal Processing (DSP) algorithms. By providing real-world "dirty" audio samples, we aim to:
* **Optimize SNR Thresholds:** Improve Signal-to-Noise Ratio (SNR) detection for micro-Doppler and motor signatures.
* **Filter Validation:** Validate digital anti-aliasing and high-pass filter designs for low-sample-rate (16kHz) inference.
* **Feature Discrimination:** Differentiate between mechanical harmonics (drones) and natural high-frequency signals (e.g., bat echolocation).

---

## 🏗 Directory Structure

To maintain a scalable and machine-readable environment, the data is organized as follows:

```text
batear-datasets/
├── field-tests/             # Real-world recordings (Drone flights, outdoor ambient)
│   ├── DJI/
│   │   └── mavic/           # DJI Mavic Pro/Air motor noise profiles
│   ├── esp32-s3-onboard/    # Samples captured directly from Batear nodes
│   └── ambient/             # Negative samples — environment without drones
│       ├── urban/           # City traffic, HVAC, pedestrian noise
│       ├── rural/           # Wind, insects, birdsong
│       └── bat-sites/       # Bat echolocation & nocturnal wildlife
├── synthetic/               # Pure frequencies for DSP calibration & unit testing
│   └── sine-sweeps/         # 10Hz to 100kHz linear/logarithmic sweeps
├── metadata/                # Dataset manifest and labeling
│   └── samples.json         # Master registry (SR, Bit-depth, timestamps)
└── tools/                   # Automation and data engineering scripts
    ├── resample.py          # Batch downsampling to production target (16kHz)
    ├── viz_spectrogram.py   # Automated spectrogram generation for PRs
    ├── generate_metadata.py # Auto-generate samples.json from audio files
    └── requirements.txt     # Python dependencies
```

---

## 🚀 Getting Started

```bash
git clone git@github.com:batear-io/batear-datasets.git
cd batear-datasets
git lfs pull
```

Audio files are organized under `field-tests/` and `synthetic/`. Each sample is registered in `metadata/samples.json` with its sample rate, bit depth, duration, and tags.

---

## 🛠 Tools Usage

### Prerequisites

- Python 3.9+
- Install dependencies:

```bash
pip install -r tools/requirements.txt
```

### Resample Audio — `tools/resample.py`

Batch downsample audio files to the production target sample rate (16 kHz by default).

**When to use:**
- After adding new high-sample-rate recordings (e.g., 44.1/48 kHz) that need to match the ESP32-S3 inference rate (16 kHz).
- When testing how DSP filters and SNR thresholds behave at different sample rates.

```bash
# Resample all files in a directory to 16 kHz (default)
python tools/resample.py field-tests/ambient/rural/

# Custom output directory and sample rate
python tools/resample.py field-tests/DJI/mavic/ --output-dir output/mavic_8k --target-sr 8000
```

Output is saved to `<input_dir>_resampled/` with a `resample_manifest.json` summary.

### Generate Spectrograms — `tools/viz_spectrogram.py`

Create mel-spectrogram PNG images for visual inspection and PR reviews.

**When to use:**
- When submitting a PR with new audio files — attach spectrograms so reviewers can visually verify the data.
- When comparing drone vs. ambient recordings to spot frequency patterns (motor harmonics, bat chirps, etc.).
- When debugging filter designs — visualize before/after resampling to check for aliasing artifacts.

```bash
# Single file
python tools/viz_spectrogram.py field-tests/ambient/rural/20230701_054200.WAV

# Entire directory
python tools/viz_spectrogram.py field-tests/ambient/rural/

# Custom FFT parameters
python tools/viz_spectrogram.py field-tests/ambient/rural/ --output-dir spectrograms/ --n-fft 4096 --hop-length 256
```

Output is saved to `<input_dir>_spectrograms/`.

---

## 📝 Contributing

We welcome contributions of new recordings, synthetic signals, and tool improvements.

### Adding Audio Data

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b add/mavic-hover-samples
   ```
2. **Place files** in the correct subdirectory:
   - Drone recordings → `field-tests/DJI/<model>/` or `field-tests/esp32-s3-onboard/`
   - Ambient / negative samples → `field-tests/ambient/{urban,rural,bat-sites}/`
   - Calibration signals → `synthetic/sine-sweeps/`
3. **File requirements:**
   - Format: WAV (16-bit PCM preferred)
   - Minimum sample rate: 44.1 kHz
   - Filename convention: `YYYYMMDD_HHMMSS.WAV` (UTC timestamp)
4. **Optionally** generate spectrograms to include in your PR:
   ```bash
   python tools/viz_spectrogram.py <your-files-directory>
   ```
5. **Open a Pull Request** — `metadata/samples.json` will be updated automatically by CI after merging to `main`.

### Improving Tools

1. Install dev dependencies:
   ```bash
   pip install -r tools/requirements.txt
   ```
2. Make your changes in `tools/`.
3. Test locally against existing audio files before submitting.

### Guidelines

- Keep commits focused — separate data additions from tool changes.
- Use descriptive branch names: `add/<description>`, `fix/<description>`, `tool/<description>`.
- Large files (audio, images) are tracked by Git LFS automatically via `.gitattributes`.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
