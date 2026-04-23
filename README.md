![System in Action](https://raw.githubusercontent.com/ra08697-glitch/Low-Cost-Velocity-Estimation-Using-IMU-Sensor-Fusion-and-Computer-Vision-for-Gymnastics-Applications/proof-of-concept/images/Estimated%20Pose.jpg)
*Real-time pose estimation and velocity calculation running on the Jetson Orin Nano.*

# Gymnast Velocity Tracking System
### Low-Cost, Real-Time Center of Mass (CoM) Estimation 



Traditional motion capture for gymnastics costs thousands of dollars and requires laboratory conditions. This project provides a **deployable, $500 alternative** using embedded AI to track vaulting and tumbling velocity in real-time.

---

## 🚀 The Tech Stack
* **Vision:** NVIDIA Jetson Orin Nano + YOLOv8-Pose (tracking hips as CoM proxy).
* **Inertial:** Arduino Nano 33 BLE Rev2 (Sternum-mounted for trunk acceleration).
* **Optics:** Arducam IMX477 (CSI connection for high-speed, 60fps+ capture).
* **OS:** NVIDIA JetPack 6.2.1 (Ubuntu 22.04).

## 📊 Intelligent Filtering
To solve "teleportation" errors and keypoint jitter, the system uses **Triple-Check Logic**:
1. **Confidence Filter:** Requires >0.6 hip detection confidence to calculate velocity.
2. **Physiological Clamp:** Discards any movement >12.0 m/s (based on human sprinting limits).
3. **Peak Validation:** Top speeds are only recorded during high-certainty (>0.75) detection windows.

## 📂 Repository Structure
* `/python`: Main CV tracking scripts and Jetson inference code.
* `/arduino`: Firmware for the Nano 33 BLE velocity logger.
* `/docs`: Detailed research and setup documentation.

## 🛠 Quick Start

### 1. Hardware Setup
Before running the code, ensure your Jetson is configured for the IMX477 camera and your Arduino is flashed.
* See [REPLICATION_GUIDE.md](./REPLICATION_GUIDE.md) for the full Jetson environment setup.
* See [TRIAL_PROTOCOL_AND_ENCLOSURES.md](./TRIAL_PROTOCOL_AND_ENCLOSURES.md) for mounting and trial instructions.

### 2. Software Install
```bash
# Clone the repository
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO.git](https://github.com/YOUR_USERNAME/YOUR_REPO.git)
cd YOUR_REPO

# Install core AI dependencies (See Replication Guide for custom OpenCV build)
pip3 install "numpy<2.0"
pip3 install ultralytics pyserial
```

### 3. Run Tracker
```bash
python3 python/gymnast_tracker_imx477.py
```

---

---

## ✍️ Authors & Research Team
* **Primary Researcher:** Reasun Understanding Allah-U-Akbar
  *Lead developer, system architect, and primary investigator.*
* **Faculty Advisor:** Dr. Junghun Choi, Ph.D.  
  *Project guidance and institutional support.*

## 🏛️ Research Context
This project was developed at **Georgia Southern University** for the 2026 Student Research Symposium. It represents an advancement in low-cost sports biomechanics, moving elite-level data out of the lab and into the gym.

## ⚖️ License
This project is licensed under the **MIT License**. This allows for free use and modification for academic and commercial purposes, provided that the original author is credited. See the [LICENSE](LICENSE) file for the full legal text.
