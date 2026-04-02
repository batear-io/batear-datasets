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
    └── viz_spectrogram.py   # Automated spectrogram generation for PRs
