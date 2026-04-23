# Trial Protocol & Enclosure Requirements
## Gymnast Velocity Tracking — Research Documentation

---

# PART A: TRIAL PROTOCOL

## A1. Overview
**Goal:** Validate both tracking systems (CV + IMU) against a known reference, then collect gymnast-specific velocity data across multiple apparatus.

**Systems running simultaneously:**
- **Computer Vision:** Jetson Orin Nano + YOLOv8-pose (Whole-body CoM velocity).
- **IMU:** Arduino Nano 33 BLE Rev2 on sternum (Trunk acceleration proxy).

---

## A2. Equipment & Safety Checklist
### Hardware
- [ ] Jetson Orin Nano powered and booted (JetPack 6.2.1).
- [ ] Arducam IMX477 connected via CSI and confirmed (`ls /dev/video0`).
- [ ] Camera mount stable, leveled, and aimed at the "action zone."
- [ ] Arduino flashed with `imu_velocity_logger.ino` and secured in enclosure.
- [ ] Serial Monitor active at 115200 baud for data capture.

### Safety & Environment
- [ ] **Trip Hazards:** Ensure all power/CSI cables are taped down or routed away from the gymnast's path.
- [ ] **Lighting:** Subject should be front-lit; avoid bright windows in the background.
- [ ] **Calibration:** 1m reference and 5m tape lines clearly visible on floor.

---

## A3. Calibration & Synchronization

### CV Pixel Calibration
1. Place a 1-meter reference at the exact depth where the gymnast will move.
2. Capture frame, measure pixel width, and update `PIXELS_PER_METER` in code.
3. **Note:** Re-calibrate if the camera or the athlete's plane of motion shifts.

### System Synchronization (The "Sync-Jump")
To align the IMU data (CSV) with the Computer Vision data (Video/Logs):
1. With both systems recording, have the athlete perform a **small vertical hop** in view of the camera.
2. The impact spike in the IMU's `Az` (Z-axis) data will match the frame where the athlete's hips reach the lowest point of the landing.

---

## A4. Data Collection Protocol

### 1. Validation Phase (Accuracy Check)
Perform 3 reps of walking and 3 reps of sprinting over the 5m marked distance.
* **Manual Ref:** Time with a stopwatch ($v = 5 / t$).
* **Goal:** Verify CV and IMU are within ±15% of the manual reference.

### 2. Experimental Phase (Gymnastics Skills)
For every skill (Vault approach, Tumbling, etc.):
1. **Name the Trial:** Use convention `Date_AthleteID_Skill_Trial01`.
2. **Start Logging:** Send `s` in Serial Monitor.
3. **The Sync:** Perform the Sync-Jump.
4. **The Skill:** Execute the gymnastics movement.
5. **Stop Logging:** Send `s` again.
6. **Note HUD:** Record the "Peak Velocity" shown on the Jetson screen.

---

## A5. Data Recording Sheet

| Trial ID | Skill Name | Manual Ref | CV Peak | IMU Peak | Notes (Occlusion? Drift?) |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

---

# PART B: ENCLOSURE & MOUNTING

## B1. Sourcing Existing Models
Rather than designing from scratch, researchers can use verified models from **GrabCAD** or **Printables**.

**Search Terms:**
- *Arducam IMX477 Case* (Ensure it supports C-Mount lenses).
- *Arduino Nano 33 BLE Chest Mount*.
- *GoPro to 1/4"-20 Adapter* (Useful for mounting cases to tripods).

---

## B2. Enclosure Requirements

### Camera (IMX477 CSI)
- **Adapter Space:** Must have clearance for a **5mm C-to-CS adapter ring**.
- **Strain Relief:** The 22-pin CSI cable must be clamped or slotted to prevent disconnection during vibration.
- **Heat Management:** Must have ventilation slots; the Jetson-linked cameras run hot during inference.

### IMU (Nano 33 BLE Rev2)
- **Rigid Coupling:** The Arduino must not move inside the case. Use a friction fit or M2 screws.
- **Chest Interface:** Case back must be flat or contoured for the sternum, with slots for a **25mm elastic strap**.
- **Orientation:** A physical "UP" arrow must be marked on the outside to ensure the Y-axis consistently represents vertical acceleration.

---

## B3. Research Limitations to Note
- **2D Perspective:** Velocity is only accurate when the movement is perpendicular to the camera.
- **Occlusion:** If a gymnast tucks (e.g., a somersault), the hip keypoints may be lost, causing a velocity drop.
- **IMU Drift:** The IMU calculates velocity via integration; it is only accurate for short bursts (<10 seconds) before "Stillness Reset" is required.
