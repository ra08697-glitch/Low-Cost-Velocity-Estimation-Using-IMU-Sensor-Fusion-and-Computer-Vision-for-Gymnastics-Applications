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

## A2. Equipment Checklist
Before each session, confirm:
- [ ] Jetson Orin Nano powered and booted (JetPack 6.2.1).
- [ ] Arducam IMX477 connected via CSI and confirmed (`ls /dev/video0`).
- [ ] Camera mount stable, leveled, and aimed at the 5m "action zone."
- [ ] `PIXELS_PER_METER` calibrated for the current camera-to-athlete distance.
- [ ] Arduino flashed with `imu_velocity_logger.ino`.
- [ ] Serial Monitor active at 115200 baud for data capture.
- [ ] Floor markings: 1m calibration reference and 5m validation tape lines.

---

## A3. Calibration (Run Before Every Session)

### CV Pixel Calibration
1. Place a 1-meter object (meter stick) at the exact depth where the gymnast will be performing.
2. Capture a frame and measure the pixel width of the 1m object.
3. Update `PIXELS_PER_METER` in your Python tracking script.
4. **Note:** If the camera moves even an inch, you must re-calibrate.

### IMU Auto-Calibration
1. Power on the Arduino and keep it perfectly still on a level surface.
2. The code includes a 2-second stillness window to zero out the BMI270 offsets.
3. Confirm the "Calibration complete" message in the Serial Monitor.

---

## A4. Validation Trials
**Purpose:** Establish system accuracy against a manual baseline ($v = d/t$).

| Trial | Speed Condition | Reps | Reference Measurement |
|---|---|---|---|
| 1 | Normal Walk | 5 | Stopwatch time over 5m |
| 2 | Jog | 5 | Stopwatch time over 5m |
| 3 | Sprint | 5 | Stopwatch time over 5m |

**Success Criteria:** CV and IMU readings should both fall within **±15%** of the stopwatch reference.

---

## A5. Gymnast-Specific Trials
### Skills to Record
- **Floor:** 14m diagonal run, round-off entry, back handspring series.
- **Vault:** Full approach run from start to board contact.
- **General:** Standing sprints, jumps, and cartwheels.

### Data Collection Routine
1. Send `s` in the Serial Monitor to start IMU logging.
2. Execute the skill.
3. Send `s` to stop logging.
4. Record the **Peak CV Speed** displayed on the Jetson HUD.

---

# PART B: ENCLOSURE & MOUNTING

## B1. Sourcing Existing Models
While custom CAD allows for specific research branding, most users will find it faster to source existing models from **GrabCAD**, **Thingiverse**, or **Printables**.

**Recommended Search Terms:**
- "Arducam IMX477 Case" or "Raspberry Pi High Quality Camera Enclosure"
- "Arduino Nano 33 BLE Case"
- "GoPro Tripod Mount Adapter" (to bridge enclosures to standard tripods)

---

## B2. Camera Enclosure Requirements (IMX477 CSI)
If downloading or designing a camera housing, it must meet these criteria:
1.  **Lens Support:** Must accommodate a C-mount lens (like the Computar 12mm) and have room for a **5mm C-to-CS adapter ring**.
2.  **CSI Cable Protection:** The 22-pin ribbon cable is fragile; the housing should have a slot that prevents the cable from being sharply bent or tugged.
3.  **Mounting:** Must have a **1/4"-20 tripod thread** or a GoPro-style "fingers" mount for angle adjustment.
4.  **Ventilation:** The IMX477 can get warm during long sessions; side vents are recommended.

---

## B3. IMU Enclosure Requirements (Nano 33 BLE)
The IMU housing is the most critical for data quality as it is worn by the athlete.
1.  **Secure Fixation:** The case must have slots for a **25mm elastic chest strap** or a high-tension clip. Any "jiggle" inside the case will appear as noise in the velocity data.
2.  **Orientation Markers:** There should be a physical arrow or text on the case indicating the **"UP"** direction (USB port down) to ensure data is consistent across trials.
3.  **Port Access:** The Micro-USB port must be accessible without opening the case for easy data offloading and charging.
4.  **Weight:** Target total weight (Arduino + Case) should be **<40g** to avoid impacting gymnast biomechanics.

---

## B4. Environmental Setup Tips
- **Lighting:** Avoid backlighting (e.g., windows behind the gymnast). Pose estimation works best when the athlete is brighter than the background.
- **Contrast:** Encourage athletes to wear colors that contrast with the gym mats (e.g., avoid blue leotards/shorts if the mats are blue).
- **Background:** A "busy" background with other moving athletes will confuse the tracker. Aim the camera at a clear "lane."
