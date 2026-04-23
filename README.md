# Gymnast Velocity Tracking System
### Low-Cost, Real-Time Center of Mass (CoM) Estimation 

This project implements a dual-method tracking system designed for gymnastic vaulting and tumbling. It leverages embedded AI to provide elite-level data at a fraction of the cost of traditional systems.

## 🚀 The Tech Stack
* **Vision:** NVIDIA Jetson Orin Nano + YOLOv8-Pose (tracking hips as CoM).
* **Inertial:** Arduino Nano 33 BLE Rev2 (Sternum-mounted acceleration).
* **Optics:** Arducam IMX477 (High-speed CSI connection).

## 📊 Intelligent Filtering
To solve the "teleportation" errors common in pose estimation, this system uses a **Triple-Check Logic**:
1. **Confidence Filter:** Requires >0.6 hip detection confidence.
2. **Physics Clamp:** Discards any movement >12 m/s (physically impossible for human sprinting).
3. **Peak Validation:** Only logs top speeds during high-certainty detection windows.

## 🛠 Setup
1. Clone the repo: `git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git`
2. Install dependencies: `pip install ultralytics opencv-python pyserial`
3. Run the tracker: `python3 python/gymnast_tracker_imx477.py`
