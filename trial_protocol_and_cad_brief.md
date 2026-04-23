# Trial Protocol & CAD Design Briefs
## Gymnast Velocity Tracking — Research Documentation

---

# PART A: TRIAL PROTOCOL

## A1. Overview

**Goal:** Validate both tracking systems (CV + IMU) against a known reference, then collect gymnast-specific velocity data across multiple apparatus.

**Systems running simultaneously:**
- Computer Vision: Jetson Orin Nano + YOLOv8-pose (whole-body CoM velocity)
- IMU: Arduino Nano 33 BLE Rev2 on sternum (whole-body approximation via trunk acceleration)

---

## A2. Equipment Checklist

Before each session confirm:

- [ ] Jetson Orin Nano powered and booted
- [ ] USB-C hub connected to Jetson
- [ ] Camera plugged into hub, `/dev/video0` confirmed with `ls /dev/video*`
- [ ] Camera mount stable, aimed at movement area, level
- [ ] `gymnast_tracker.py` PIXELS_PER_METER calibrated for current camera position
- [ ] Arduino charged or powered via USB
- [ ] Arduino flashed with `imu_velocity_logger.ino`
- [ ] Laptop with Arduino IDE Serial Monitor ready at 115200 baud
- [ ] Floor markings: 1m calibration reference, 5m validation distance marked with tape

---

## A3. Calibration (Run Before Every Session)

### CV Pixel Calibration
1. Place a 1-meter object (tape measure, meter stick) flat on the floor in the camera's field of view at the same depth as where the gymnast will be
2. Capture a frame and measure pixel width of the 1m object
3. Update `PIXELS_PER_METER` in `gymnast_tracker.py`
4. Record the value and camera position in your lab notebook — repeat if camera moves

### IMU Calibration
1. Power on Arduino, open Serial Monitor
2. Hold Arduino flat and still on a level surface for 2 seconds during auto-calibration
3. Confirm "Calibration complete" message before proceeding

---

## A4. Validation Trials (Run First)

**Purpose:** Establish accuracy of both systems before gymnast-specific trials.

**Setup:** 5m straight-line distance marked on floor with tape. Camera positioned perpendicular to movement direction.

**Protocol per condition:**

| Trial | Speed Condition | Expected Speed | Reps |
|---|---|---|---|
| 1 | Slow walk | ~1.2 m/s | 5 |
| 2 | Normal walk | ~1.5 m/s | 5 |
| 3 | Jog | ~2.5-3.5 m/s | 5 |
| 4 | Sprint | ~5-8 m/s | 5 |

**Reference measurement:** Time each pass with a stopwatch over the 5m distance. Reference speed = 5 / elapsed_time (m/s).

**Data to record per pass:**
- Reference speed (stopwatch)
- CV peak speed reading
- IMU peak speed reading
- Start `s` command in Serial Monitor before each pass, stop after

**Success criteria:** Both systems within ±15% of reference at all speed conditions.

---

## A5. Gymnast-Specific Trials

### Session Structure
- Warm-up: 10 minutes standard gymnastics warm-up
- Trials: 3-5 repetitions per skill, rest between sets
- Rest between apparatus: minimum 5 minutes

### Skills to Record by Apparatus

**Floor Exercise**
- Straight-line run (full floor diagonal, ~14m)
- Back handspring series
- Round-off entry into tumbling

**Vault (if available)**
- Approach run
- Board contact through post-flight

**General**
- Standing start sprint
- Cartwheel
- Jump series

### Data Collection Per Trial
1. Call out skill name before each rep (will timestamp in Serial log)
2. Send `s` to start IMU logging
3. Execute skill
4. Send `s` to stop IMU logging
5. Note peak CV speed from display
6. Record in data sheet (see A6)

---

## A6. Data Recording Sheet

Print and use in the gym. One row per trial.

```
Date: ___________  Athlete: ___________  Session #: ___________
Camera height: ___ m   PIXELS_PER_METER: ___   Camera distance from action: ___ m

| # | Apparatus | Skill        | Ref (m/s) | CV (m/s) | IMU (m/s) | Notes |
|---|-----------|--------------|-----------|----------|-----------|-------|
| 1 |           |              |           |          |           |       |
| 2 |           |              |           |          |           |       |
| 3 |           |              |           |          |           |       |
...
```

---

## A7. Environmental Setup Recommendations

**Camera placement:**
- Height: 1.0-1.2m (hip level) for whole-body CoM tracking
- Distance from action: 4-6m for full-body in frame at 1080p
- Angle: Perpendicular to primary movement direction
- Background: Plain, high-contrast wall preferred (avoid busy gym backgrounds)
- Lighting: Avoid backlighting; ensure athlete is well-lit from front/sides

**IMU placement:**
- Location: Sternum, centered on chest
- Attachment: Elastic band or sports tape; must not shift during movement
- Orientation: Consistent per session (USB connector pointing down preferred)
- Clothing: Under outer layer if possible to minimize flapping

**Both systems:**
- Run a 30-second pre-trial recording with athlete standing still to confirm baselines
- Verify CV is detecting the gymnast (green skeleton visible) before starting each set

---

# PART B: CAD DESIGN BRIEFS

## B1. Camera Enclosure (Sony IMX577 USB)

### Purpose
Protect the bare PCB, provide a stable 1/4"-20 tripod mount, and enable repeatable camera angle for research reproducibility.

### Required Measurements (fill in before modeling)

```
PCB length:          ___ mm
PCB width:           ___ mm  
PCB thickness:       ___ mm
Lens center from left edge:   ___ mm
Lens center from top edge:    ___ mm
Lens outer diameter:          ___ mm
USB connector edge:           Top / Bottom / Left / Right (circle one)
USB connector width:          ___ mm
USB connector height:         ___ mm
Mounting holes present:       Yes / No
  If yes — hole diameter: ___ mm
  Hole positions (from corner): ___ mm, ___ mm
```

### Design Specifications

**Body — Camera Pocket**
- PCB pocket depth = PCB thickness + 0.5mm
- PCB pocket XY = PCB dimensions + 0.3mm clearance each side
- Retention: M2 screws through existing PCB holes (if present) OR friction-fit lid
- Wall thickness minimum: 3mm sides, 4mm front face

**Lens Aperture**
- Circular hole: lens OD + 1mm clearance
- Shallow chamfer on exterior face (45°, 1mm depth) for clean appearance
- Center precisely on lens position from measurements above

**USB Exit Channel**
- Rear face slot: USB connector width + 1mm, USB connector height + 1mm
- Stress relief clamp (zip-tie post) 20mm from connector exit
- Gentle radius entry (R3mm minimum) to prevent cable kinking

**Ventilation**
- 4x slots (2mm × 10mm) on each side face
- Orient away from lens axis

**Mounting Interface — Bottom Face**
- 1/4"-20 brass heat-set insert (standard tripod thread)
- 3/8"-16 brass heat-set insert (heavy tripod/light stand)
- Two M4 slots (4.5mm × 10mm) for rail mounting, 25mm apart

**Tilt Adjustment Neck**
- Arc of ±20° forward/backward
- M4 bolt + knob lock
- Degree markings engraved at 5° increments
- Record camera angle in lab notes each session

**Branding (front face, embossed 0.5mm)**
- Institution name
- Project name
- Small 10mm rule bar adjacent to lens

**Print Settings**
- Material: PETG
- Layer height: 0.15mm
- Infill: 40% gyroid
- Walls: 4 perimeters
- Supports: Only if lens aperture requires

**Hardware to order before printing:**
- M2 × 4mm heat-set inserts (×4, for PCB retention)
- 1/4"-20 heat-set insert (×2)
- 3/8"-16 heat-set insert (×1)
- M4 × 20mm bolt + knurled knob (×1, for tilt lock)

---

## B2. Arduino Enclosure (Nano 33 BLE Rev2)

### Purpose
Protect the Arduino during athletic trials, provide secure body attachment (sternum mount), and allow USB access for programming without full disassembly.

### Arduino Nano 33 BLE Rev2 Dimensions (standard)

```
PCB length:    45mm
PCB width:     18mm
PCB thickness: 1.6mm
USB connector: Micro-B, short end of board
Pin headers:   Both long sides, 2.54mm pitch
Component height (top): ~4mm (components above PCB)
Component height (bottom): ~1mm (minimal)
```

**Verify these with calipers before modeling.**

### Design Specifications

**Body — Arduino Pocket**
- PCB pocket: 45.6mm × 18.6mm × 2.5mm deep (PCB + 0.3mm clearance + component relief)
- Component relief cavity above PCB: full length × full width × 5mm
- Total internal height: ~8mm
- Retention: snap-fit lid OR M2 screws at corners

**USB Access Port**
- Micro-B cutout on short end: 12mm × 8mm (generous clearance for cable insertion)
- Do NOT fully seal this end — cable must be insertable without disassembly

**LED Window**
- Small 3mm hole or 2mm × 8mm slot on top face aligned with Arduino's onboard RGB LED
- Allows visual confirmation of sketch running during trials

**Body Attachment System**
- Design for sternum mounting on gymnast
- Two options (design both, athlete chooses):

  *Option A — Elastic Band Channel:*
  - Two 25mm × 4mm slots on back face, top and bottom
  - Routes a 25mm wide elastic band around the torso
  - Slots oriented horizontally

  *Option B — Clip Mount:*
  - Flat back face with two M3 screw bosses
  - Separate clip plate that attaches to sports bra / compression shirt strap
  - M3 × 8mm screws

**Dimensions (overall enclosure target):**
- Length: ~52mm
- Width: ~26mm  
- Height: ~14mm
- Weight target: <30g printed in PETG

**Ventilation**
- 4x small holes (2mm diameter) on sides for heat dissipation
- Keep away from USB port end

**Labeling (top face, embossed)**
- "IMU TRACKER" text
- Arrow indicating forward/up orientation for consistent mounting

**Print Settings**
- Material: PETG (flexibility helps with snap-fit; heat resistance for gym environment)
- Layer height: 0.15mm
- Infill: 30% gyroid
- Walls: 3 perimeters minimum
- Supports: None if designed with proper draft angles

**Hardware to order:**
- M2 × 4mm heat-set inserts (×4 corners for lid)
- M3 × 8mm screws (×2, for clip option)
- 25mm wide elastic band, 60cm length (for band option)

---

## B3. Modeling Sequence (SolidWorks)

Recommended order to avoid rework:

1. Measure both PCBs with calipers, fill in blanks above
2. Model Arduino enclosure first (simpler geometry, good practice)
3. Model camera body and lens aperture
4. Model camera tilt neck and mount interface
5. Send both to print simultaneously
6. While printing: run validation trials with temporary mount (camera taped to tripod)
7. Assemble and test fit before first official trial session

**File naming convention:**
```
gymnast_tracker_camera_enclosure_v1.SLDPRT
gymnast_tracker_camera_lid_v1.SLDPRT
gymnast_tracker_arduino_enclosure_v1.SLDPRT
gymnast_tracker_arduino_lid_v1.SLDPRT
gymnast_tracker_tilt_neck_v1.SLDPRT
gymnast_tracker_assembly_v1.SLDASM
```
