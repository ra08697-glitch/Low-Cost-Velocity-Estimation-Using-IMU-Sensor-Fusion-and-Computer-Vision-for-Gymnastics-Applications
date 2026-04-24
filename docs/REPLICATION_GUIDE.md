![Experimental Setup](../images/setup.HEIC)

# Gymnast Velocity Tracking System — Replication Guide

**Project:** Low-Cost Gymnast Velocity Tracking via Computer Vision and IMU  
**Hardware:** NVIDIA Jetson Orin Nano + Arducam IMX477 (CSI) + Arduino Nano 33 BLE Rev2  
**OS:** Ubuntu 22.04 (JetPack 6.2.1)  
**OpenCV:** 4.10.0 (built from source with GStreamer + CUDA)

---

## 1. Hardware Requirements

### Core System
| Component | Specification | Purpose |
|---|---|---|
| **NVIDIA Jetson Orin Nano** | 8GB Developer Kit | CV inference host & data processing |
| **Arduino Nano 33 BLE Rev2** | BMI270 IMU | Wearable trunk-velocity tracker |
| **Arducam IMX477** | CSI Interface (22-pin) | 60fps high-speed capture (Required for gymnastics) |
| **Computar 12mm Lens** | f/1.4 C-Mount | Primary lens for vault/bars (4-8m range) |

### Lens Setup (IMX477)
* **Adapter:** The Computar 12mm requires a **5mm C-to-CS adapter ring** to be installed between the lens and the camera body.
* **Aperture:** Use **f/4** for trials to provide a forgiving depth of field; use f/1.4 only in extremely low-light conditions.

---

## 2. Critical Environment Setup (The "Jetson Fixes")

The Jetson Orin Nano uses an ARM64 architecture. To avoid the **"Illegal Instruction"** error and library conflicts, follow these steps exactly.

### 2.1 Set Environment Variables
Add this to your `~/.bashrc` to ensure the OpenBLAS library maps correctly to the ARMv8 architecture. This prevents the `Illegal Instruction (core dumped)` error.

```bash
echo "export OPENBLAS_CORETYPE=ARMV8" >> ~/.bashrc
source ~/.bashrc
```

### 2.2 Install System Dependencies
```bash
sudo apt update && sudo apt install -y \
  v4l-utils python3-pip python3-dev ffmpeg libopenblas-dev \
  libgstreamer1.0-dev gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  build-essential cmake git pkg-config
```

### 2.3 cuSPARSELt Installation
Required for PyTorch 2.5+ GPU acceleration on JetPack 6:
```bash
wget [https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-aarch64/libcusparse_lt-linux-aarch64-0.6.3.2-archive.tar.xz](https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-aarch64/libcusparse_lt-linux-aarch64-0.6.3.2-archive.tar.xz)
tar -xf libcusparse_lt-linux-aarch64-0.6.3.2-archive.tar.xz
sudo cp libcusparse_lt-linux-aarch64-0.6.3.2-archive/lib/libcusparseLt.so.0 /usr/local/cuda-12.6/targets/aarch64-linux/lib/
sudo ldconfig
```

---

## 3. Camera & OpenCV Configuration

### 3.1 CSI Camera Enablement
Run the Jetson configuration tool to enable the IMX477 overlay:
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```
*Navigate to "Configure Jetson 24pin CSI Connector" → select "Camera IMX477-A" → Save & Reboot.*

### 3.2 Build OpenCV 4.10.0 (with GStreamer)
Standard `opencv-python` does not support the Jetson CSI pipeline. You must build from source. Version 4.10.0 is required for compatibility with CUDA 12.x.

**Key CMake Flags:**
* `-D WITH_GSTREAMER=ON`
* `-D WITH_CUDA=ON`
* `-D CUDA_ARCH_BIN=8.7`

---

## 4. Python AI Stack & Filtering

### 4.1 Version-Locked Dependencies
To prevent the **NumPy 2.0 conflict** which breaks PyTorch on Jetson, lock your version:
```bash
pip3 install "numpy>=1.26,<2.0"
pip3 install ultralytics --no-deps
pip3 install pyserial
```

### 4.2 Three-Level Velocity Filter
The tracking scripts implement a robust logic to eliminate "teleportation" artifacts:
* **Confidence Threshold:** Hips (Keypoints 11/12) must have >0.6 confidence for CoM calculation.
* **Physiological Clamp:** Instantaneous velocity >12.0 m/s is discarded.
* **Peak Validation:** Peak session speed only updates when confidence >0.75.

---

## 5. Arduino IMU Setup

### 5.1 Firmware & Reset Logic
Upload `imu_velocity_logger.ino` to the Nano 33 BLE.
* **Stillness Reset:** To eliminate sensor drift, the code automatically zeros velocity if acceleration remains below 2.0 m/s² for 200ms.
* **Filter:** A high-pass filter (`HP_ALPHA = 0.95`) removes the gravity component from the raw acceleration signal.

---

## 6. Calibration & Validation

### 6.1 Session Calibration
1. Place a 1-meter reference (meter stick) at the athlete's plane of motion.
2. Measure the pixel width of the reference in the camera feed.
3. Update `PIXELS_PER_METER` in the `python/` scripts.

### 6.2 Research Validation
Perform a 5-meter sprint test marked with tape.
Compare CV and IMU data against a stopwatch reference ($v = d/t$).
Target Accuracy: ± 15% deviation from manual timing.

---

## 7. Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| **Illegal Instruction** | OpenBLAS architecture mismatch | `export OPENBLAS_CORETYPE=ARMV8` |
| **NumPy Version Error** | Auto-update to NumPy 2.0 | `pip3 install "numpy<2.0"` |
| **CSI Camera Blurry** | Focus lock or missing adapter | Install 5mm C-to-CS adapter ring |
| **IMU Drift** | No stillness reset | Confirm `STILL_THRESHOLD` is tuned to noise |
