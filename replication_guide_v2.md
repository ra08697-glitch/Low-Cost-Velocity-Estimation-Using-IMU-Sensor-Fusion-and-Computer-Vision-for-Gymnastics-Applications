# Gymnast Velocity Tracking System — Replication Guide

**Project:** Low-Cost Gymnast Velocity Tracking via Computer Vision and IMU  
**Hardware:** NVIDIA Jetson Orin Nano + Camera (see Section 3) + Arduino Nano 33 BLE Rev2  
**OS:** Ubuntu 22.04 (JetPack 6.2.1)  
**Date:** March 2026  
**OpenCV:** 4.10.0 (built from source with GStreamer + CUDA)

---

## Table of Contents

1. Hardware Requirements
2. Jetson Orin Nano Setup
3. Camera Setup — Choose Your Path
   - 3A: Sony IMX577 USB Camera
   - 3B: Arducam IMX477 CSI Camera (UC-517)
4. Python Environment and Dependencies
5. Computer Vision Pipeline
6. Arduino IMU Setup
7. Running the System
8. Calibration Protocol
9. Known Issues and Fixes

---

## 1. Hardware Requirements

### Core Hardware (Required)

| Component | Specification | Purpose |
|---|---|---|
| NVIDIA Jetson Orin Nano Dev Kit | 8GB, JetPack 6.2.1 | CV inference host |
| Arduino Nano 33 BLE Rev2 | BMI270 IMU, onboard BLE | Wearable IMU tracker |
| USB-C hub with USB 3.0 ports | Any brand | Peripherals + ethernet |
| USB-A to Micro-USB cable | Data-capable (not charge-only) | Arduino programming |

### Camera Options (Choose One or Both)

| Camera | Interface | Resolution | FPS | Notes |
|---|---|---|---|---|
| Sony IMX577 (HD USB Camera) | USB 2.0 | 1920×1080 | ~37fps actual | No lens swap, plug-and-play |
| Arducam IMX477 UC-517 | CSI (22-pin) | 1920×1080 / 3840×2160 | 60fps / 30fps | Requires C-to-CS adapter, manual focus lenses |

### Arducam IMX477 Lens Options

| Lens | Focal Length | Mount | Best Distance | Use Case |
|---|---|---|---|---|
| Computar 12mm f/1.4 | 12mm | C-mount (needs 5mm adapter) | 4-8m | **Primary lens** — vault, beam, bars, controlled trials |
| 6mm CCTV IR 3MP HD | 6mm | CS-mount (no adapter) | 2-4m | Wide backup — floor exercise full view |

**Computar 12mm controls:**
- **Aperture ring** (closest to PCB): `C → 16 → 8 → 4 → 1.4` — C = closed, 1.4 = fully open. Use f/4 for trials (depth of field forgiveness); f/1.4 only in very low light
- **Focus ring** (closest to front element): distance markings in meters, ∞ at far end. Set to your shooting distance and fine-tune on live feed

**CCTV 6mm note:** This is CS-mount — mount directly to camera body with **no adapter ring**. The 5mm C-to-CS adapter is only for the Computar.

---

## 2. Jetson Orin Nano Setup

### 2.1 Verify JetPack and CUDA

```bash
cat /etc/nv_tegra_release
nvcc --version
```

Expected: `R36 (release), REVISION: 4.7` and `Cuda compilation tools, release 12.6`

### 2.2 Install System Dependencies

```bash
sudo apt update && sudo apt install -y \
  v4l-utils \
  python3-pip python3-dev \
  ffmpeg \
  libjpeg-dev libpng-dev libtiff-dev \
  libavcodec-dev libavformat-dev libswscale-dev libavresample-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly gstreamer1.0-libav \
  libgtk-3-dev \
  libv4l-dev \
  libopenblas-dev \
  build-essential cmake git pkg-config \
  i2c-tools
```

### 2.3 Install cuSPARSELt (Required for PyTorch)

```bash
wget https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-aarch64/libcusparse_lt-linux-aarch64-0.6.3.2-archive.tar.xz
tar -xf libcusparse_lt-linux-aarch64-0.6.3.2-archive.tar.xz
sudo cp libcusparse_lt-linux-aarch64-0.6.3.2-archive/lib/libcusparseLt.so.0 /usr/local/cuda-12.6/targets/aarch64-linux/lib/
sudo cp libcusparse_lt-linux-aarch64-0.6.3.2-archive/lib/libcusparseLt.so.0.6.3.2 /usr/local/cuda-12.6/targets/aarch64-linux/lib/
sudo ln -sf /usr/local/cuda-12.6/targets/aarch64-linux/lib/libcusparseLt.so.0 /usr/local/cuda-12.6/targets/aarch64-linux/lib/libcusparseLt.so
sudo ldconfig
```

---

## 3. Camera Setup — Choose Your Path

---

### 3A: Sony IMX577 USB Camera

#### 3A.1 Connection

Plug the camera into a USB port. The camera's internal controller is USB 2.0 — actual throughput will be ~37fps at 1080p regardless of port type.

#### 3A.2 Verify Detection

```bash
v4l2-ctl --list-devices
ls /dev/video*
```

Expected: `HD USB Camera` listed with `/dev/video0`

#### 3A.3 Check Supported Formats

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

Confirm `MJPG` format available at `1920x1080`.

#### 3A.4 Measure Actual FPS

```bash
python3 - <<'EOF'
import cv2, time
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
for _ in range(10): cap.read()
count, t0 = 0, time.time()
while time.time() - t0 < 5.0:
    ret, frame = cap.read()
    if ret: count += 1
print(f"Actual FPS: {count/5:.1f}")
cap.release()
EOF
```

Expected: ~37fps at 1080p MJPG.

#### 3A.5 OpenCV Requirement

The USB camera uses standard V4L2 — the pip-installed `opencv-python` works fine. No GStreamer build required.

**Skip to Section 4.**

---

### 3B: Arducam IMX477 CSI Camera (UC-517)

#### 3B.1 Physical Setup

1. **Power off the Jetson completely** before connecting CSI cameras
2. Confirm the **C-to-CS 5mm adapter ring** is installed on your lens
3. Attach the desired lens to the camera body
4. Insert the 22-pin FFC cable into the **CAM0** CSI connector (port closer to board edge) — contacts facing toward the board
5. Power on

#### 3B.2 Enable Camera Overlay

```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

Navigate to **"Configure Jetson 24pin CSI Connector"** → select **"Camera IMX477-A"** → save and reboot.

#### 3B.3 Verify Detection

```bash
v4l2-ctl --list-devices
```

Expected:
```
vi-output, imx477 9-001a (platform:tegra-capture-vi:1):
    /dev/video0
```

#### 3B.4 Test Live Feed

```bash
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! \
  'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=60/1' ! \
  nvvidconv ! videoconvert ! autovideosink
```

A live window should open. Press Ctrl+C to stop.

#### 3B.5 Focus Procedure

The IMX477 has no autofocus. Manual focus must be set before each session if the camera is moved.

**Lens mounting:**
- **Computar 12mm** (C-mount): install 5mm C-to-CS adapter ring between lens and camera body, then attach lens
- **6mm CCTV** (CS-mount): mount directly to camera body — no adapter ring

**Computar 12mm controls:**
- **Aperture ring** (closest to PCB): `C → 16 → 8 → 4 → 1.4` — use **f/4 for trials** (sufficient depth of field); f/1.4 only in very low light
- **Focus ring** (closest to front element): distance markings in meters with ∞ at far end

**Focusing steps:**
1. Run the live feed (command above)
2. Place a high-contrast target (printed text, checkerboard) at your **intended shooting distance** (4-6m for Computar, 2-3m for CCTV)
3. Set aperture to f/1.4 temporarily — shallow depth of field makes the focus point easier to identify
4. Rotate focus ring slowly through its full range, watching for edges to snap sharp
5. Once sharp, stop down aperture to f/4 for trials
6. Lock focus ring with set screw if present
7. Do not move camera after focusing — recalibrate `PIXELS_PER_METER` if position changes

**Troubleshooting focus:**

| Symptom | Cause | Fix |
|---|---|---|
| Computar blurry at all distances | C-to-CS adapter missing | Install 5mm adapter ring between lens and camera |
| CCTV lens blurry at all distances | Spacer incorrectly installed | Remove 5mm adapter — CCTV is CS-mount, mounts direct |
| Never truly sharp | Focus ring locking screw engaged | Loosen set screw on focus ring barrel |
| One side sharp, other soft | Lens not seated straight | Unscrew and reseat firmly |
| Sharp only on dust/debris near sensor | Debris on sensor surface | Remove lens, use rocket blower on sensor — never compressed air or contact |

#### 3B.6 Build OpenCV with GStreamer Support

The pip-installed opencv-python does not include GStreamer support. The IMX477 requires GStreamer — rebuild OpenCV from source.

**Important:** Use OpenCV **4.10.0** — earlier versions (4.8.x) have a cudev compatibility bug with CUDA 12.x that causes the build to fail at ~33%.

```bash
cd ~
git clone --branch 4.10.0 --depth 1 https://github.com/opencv/opencv.git
git clone --branch 4.10.0 --depth 1 https://github.com/opencv/opencv_contrib.git
mkdir -p opencv/build && cd opencv/build

# Configure — verify GStreamer: YES, CUDA: YES, Python 3: YES before building
cmake -D CMAKE_BUILD_TYPE=RELEASE \
  -D CMAKE_INSTALL_PREFIX=/usr/local \
  -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
  -D WITH_GSTREAMER=ON \
  -D WITH_LIBV4L=ON \
  -D WITH_CUDA=ON \
  -D CUDA_ARCH_BIN=8.7 \
  -D WITH_CUDNN=ON \
  -D OPENCV_DNN_CUDA=ON \
  -D WITH_OPENGL=ON \
  -D BUILD_opencv_python3=ON \
  -D PYTHON3_EXECUTABLE=$(which python3) \
  -D BUILD_EXAMPLES=OFF \
  -D BUILD_TESTS=OFF \
  -D BUILD_PERF_TESTS=OFF \
  ..

# Build (~2 hours on Orin Nano 6-core)
make -j$(nproc) 2>&1 | tee ~/opencv_build.log

# Install
sudo make install
sudo ldconfig
```

Verify all four lines:
```bash
python3 -c "
import cv2
print(f'OpenCV: {cv2.__version__}')
info = cv2.getBuildInformation()
for line in info.split('\n'):
    if any(x in line for x in ['GStreamer','CUDA','Python 3','cuDNN']):
        print(line.strip())
"
```

Expected:
```
OpenCV:    4.10.0
GStreamer: YES (1.20.3)
CUDA:      YES (ver 12.6, CUFFT CUBLAS)
cuDNN:     YES (ver 9.3.0)
```

---

## 4. Python Environment and Dependencies

### 4.1 Install NumPy (version-locked)

```bash
pip3 install "numpy>=1.26,<2.0"
```

**Critical:** NumPy must stay below 2.0. Reinstall after any major pip install session if version conflict warnings appear.

### 4.2 Install PyTorch (NVIDIA Jetson Wheel)

```bash
wget https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl
pip3 install --no-cache-dir torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl
```

**Warning:** Never run `pip3 install torch` — this installs a CPU-only build. Always use `--no-deps` when installing packages that list torch as a dependency.

### 4.3 Build torchvision from Source

```bash
cd ~
git clone --branch v0.20.0 --depth 1 https://github.com/pytorch/vision torchvision
cd torchvision
export BUILD_VERSION=0.20.0
export TORCH_CUDA_ARCH_LIST="8.7"
pip3 install --no-build-isolation . 2>&1 | tee ~/torchvision_build.log
```

Build time: ~20-30 minutes.

### 4.4 Install Remaining Packages

```bash
pip3 install ultralytics --no-deps
pip3 install lapx filterpy scipy seaborn pandas psutil py-cpuinfo PyYAML tqdm matplotlib pillow
pip3 install "numpy>=1.26,<2.0"  # reinstall after lapx may upgrade it
```

### 4.5 Verify Full Stack

```bash
python3 - <<'EOF'
import numpy as np, torch, cv2, torchvision
from ultralytics import YOLO
print(f"NumPy:       {np.__version__}")
print(f"PyTorch:     {torch.__version__}")
print(f"CUDA:        {torch.cuda.is_available()}")
print(f"GPU:         {torch.cuda.get_device_name(0)}")
print(f"OpenCV:      {cv2.__version__}")
print(f"GStreamer:   {cv2.getBuildInformation().split('GStreamer')[1].split()[1]}")
print(f"torchvision: {torchvision.__version__}")
print(f"ultralytics: OK")
print("Full stack ready.")
EOF
```

---

## 5. Computer Vision Pipeline

Two tracker scripts are provided — use the one matching your camera.

### 5A: USB Camera Tracker (IMX577)

Save as `~/gymnast_tracker_usb.py`:

```python
from ultralytics import YOLO
import cv2, numpy as np, time
from collections import deque

CAMERA_ID          = 0
WIDTH, HEIGHT      = 1920, 1080
PIXELS_PER_METER   = 150    # CALIBRATE — see Section 8
SMOOTHING_FRAMES   = 5
# ── Velocity filtering thresholds ──────────────────────────────────────────
KP_CONF_COM        = 0.6    # min confidence for hip keypoints to compute CoM
KP_CONF_PEAK       = 0.75   # min confidence to update peak speed
MAX_PLAUSIBLE_SPEED = 12.0  # m/s — discard readings above this (world-record sprint ~12.4)
KP = dict(l_hip=11, r_hip=12)

def center_of_mass(kps):
    l, r = kps[KP['l_hip']], kps[KP['r_hip']]
    # Require both hips above confidence threshold
    if l[2] > KP_CONF_COM and r[2] > KP_CONF_COM:
        return np.array([(l[0]+r[0])/2, (l[1]+r[1])/2])
    return None

def compute_velocity(history, px_per_m):
    if len(history) < 2: return None, None
    positions = [h[0] for h in history]
    times = [h[1] for h in history]
    t = np.array(times) - times[0]
    px = np.array(positions)
    if len(t) >= 3:
        vx = np.polyfit(t, px[:,0], 1)[0]
        vy = np.polyfit(t, px[:,1], 1)[0]
    else:
        dt = times[-1] - times[0]
        if dt < 1e-6: return None, None
        vx = (px[-1,0]-px[0,0])/dt
        vy = (px[-1,1]-px[0,1])/dt
    speed = np.sqrt((vx/px_per_m)**2 + (vy/px_per_m)**2)
    return speed, np.array([vx/px_per_m, vy/px_per_m])

def main():
    model = YOLO('yolov8n-pose.pt')
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    for _ in range(3): cap.read()
    ret, frame = cap.read()
    model(frame, verbose=False, device='cuda')
    print("USB Camera ready. Press Q to quit.")
    history, fps_hist, peak_speed = deque(maxlen=SMOOTHING_FRAMES), deque(maxlen=30), 0.0
    discarded_frames = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        t0 = time.time()
        results = model(frame, verbose=False, device='cuda')
        fps_hist.append(1.0/(time.time()-t0+1e-6))
        annotated = results[0].plot()
        speed_display = None
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            kps = results[0].keypoints.data[0].cpu().numpy()
            com = center_of_mass(kps)
            if com is not None:
                history.append((com, t0))
                speed, vec = compute_velocity(history, PIXELS_PER_METER)
                if speed is not None:
                    # Sanity clamp — discard physically impossible readings
                    if speed > MAX_PLAUSIBLE_SPEED:
                        discarded_frames += 1
                        history.clear()  # poisoned history — reset
                    else:
                        speed_display = speed
                        # Only update peak when confidence is high
                        if min(kps[KP['l_hip']][2], kps[KP['r_hip']][2]) > KP_CONF_PEAK:
                            peak_speed = max(peak_speed, speed)
                        cx, cy = int(com[0]), int(com[1])
                        cv2.circle(annotated, (cx,cy), 10, (0,0,255), -1)
                        if vec is not None and np.linalg.norm(vec) > 0.1:
                            cv2.arrowedLine(annotated,(cx,cy),(int(cx+vec[0]*50),int(cy+vec[1]*50)),(0,255,255),3,tipLength=0.3)
        avg_fps = sum(fps_hist)/len(fps_hist)
        cv2.putText(annotated,f"FPS: {avg_fps:.1f}",(20,50),cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,255,0),3)
        cv2.putText(annotated,f"IMX577 USB | discarded: {discarded_frames}",(20,HEIGHT-30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(200,200,200),2)
        if speed_display is not None:
            color = (0,255,0) if speed_display<3 else (0,165,255) if speed_display<6 else (0,0,255)
            cv2.putText(annotated,f"Speed: {speed_display:.2f} m/s",(20,100),cv2.FONT_HERSHEY_SIMPLEX,1.5,color,4)
            cv2.putText(annotated,f"Peak:  {peak_speed:.2f} m/s",(20,155),cv2.FONT_HERSHEY_SIMPLEX,1.0,(255,255,0),3)
        cv2.imshow('Gymnast Tracker — IMX577', cv2.resize(annotated,(1280,720)))
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()
    print(f"Peak speed: {peak_speed:.2f} m/s | Discarded frames: {discarded_frames}")

if __name__ == '__main__':
    main()
```

Run: `python3 ~/gymnast_tracker_usb.py`

---

### 5B: CSI Camera Tracker (IMX477)

**Requires:** OpenCV built with GStreamer (Section 3B.6)

Save as `~/gymnast_tracker_imx477.py`:

```python
from ultralytics import YOLO
import cv2, numpy as np, time
from collections import deque

WIDTH, HEIGHT       = 1920, 1080
FPS                 = 60
PIXELS_PER_METER    = 150    # CALIBRATE — see Section 8
SMOOTHING_FRAMES    = 5
# ── Velocity filtering thresholds ──────────────────────────────────────────
KP_CONF_COM         = 0.6    # min confidence for hip keypoints to compute CoM
KP_CONF_PEAK        = 0.75   # min confidence to update peak speed
MAX_PLAUSIBLE_SPEED = 12.0   # m/s — discard readings above this (world-record sprint ~12.4)
KP = dict(l_hip=11, r_hip=12)

def gstreamer_pipeline(width=1920, height=1080, fps=60, flip=0):
    return (
        f"nvarguscamerasrc sensor-id=0 ! "
        f"video/x-raw(memory:NVMM),width={width},height={height},framerate={fps}/1 ! "
        f"nvvidconv flip-method={flip} ! "
        f"video/x-raw,width={width},height={height},format=BGRx ! "
        f"videoconvert ! video/x-raw,format=BGR ! appsink max-buffers=1 drop=true"
    )

def center_of_mass(kps):
    l, r = kps[KP['l_hip']], kps[KP['r_hip']]
    # Require both hips above confidence threshold
    if l[2] > KP_CONF_COM and r[2] > KP_CONF_COM:
        return np.array([(l[0]+r[0])/2, (l[1]+r[1])/2])
    return None

def compute_velocity(history, px_per_m):
    if len(history) < 2: return None, None
    positions = [h[0] for h in history]
    times = [h[1] for h in history]
    t = np.array(times) - times[0]
    px = np.array(positions)
    if len(t) >= 3:
        vx = np.polyfit(t, px[:,0], 1)[0]
        vy = np.polyfit(t, px[:,1], 1)[0]
    else:
        dt = times[-1] - times[0]
        if dt < 1e-6: return None, None
        vx = (px[-1,0]-px[0,0])/dt
        vy = (px[-1,1]-px[0,1])/dt
    speed = np.sqrt((vx/px_per_m)**2 + (vy/px_per_m)**2)
    return speed, np.array([vx/px_per_m, vy/px_per_m])

def main():
    model = YOLO('yolov8n-pose.pt')
    print("Opening IMX477 via GStreamer...")
    cap = cv2.VideoCapture(gstreamer_pipeline(WIDTH, HEIGHT, FPS), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("ERROR: Could not open IMX477.")
        print("Check: camera connected, overlay loaded, OpenCV built with GStreamer")
        return
    for _ in range(3): cap.read()
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Could not read frame.")
        return
    model(frame, verbose=False, device='cuda')
    print(f"IMX477 ready at {WIDTH}x{HEIGHT}@{FPS}fps. Press Q to quit.")
    history, fps_hist, peak_speed = deque(maxlen=SMOOTHING_FRAMES), deque(maxlen=30), 0.0
    discarded_frames = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        t0 = time.time()
        results = model(frame, verbose=False, device='cuda')
        fps_hist.append(1.0/(time.time()-t0+1e-6))
        annotated = results[0].plot()
        speed_display = None
        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            kps = results[0].keypoints.data[0].cpu().numpy()
            com = center_of_mass(kps)
            if com is not None:
                history.append((com, t0))
                speed, vec = compute_velocity(history, PIXELS_PER_METER)
                if speed is not None:
                    # Sanity clamp — discard physically impossible readings
                    if speed > MAX_PLAUSIBLE_SPEED:
                        discarded_frames += 1
                        history.clear()  # poisoned history — reset
                    else:
                        speed_display = speed
                        # Only update peak when confidence is high
                        if min(kps[KP['l_hip']][2], kps[KP['r_hip']][2]) > KP_CONF_PEAK:
                            peak_speed = max(peak_speed, speed)
                        cx, cy = int(com[0]), int(com[1])
                        cv2.circle(annotated,(cx,cy),10,(0,0,255),-1)
                        if vec is not None and np.linalg.norm(vec) > 0.1:
                            cv2.arrowedLine(annotated,(cx,cy),(int(cx+vec[0]*50),int(cy+vec[1]*50)),(0,255,255),3,tipLength=0.3)
        avg_fps = sum(fps_hist)/len(fps_hist)
        cv2.putText(annotated,f"FPS: {avg_fps:.1f}",(20,50),cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,255,0),3)
        cv2.putText(annotated,f"IMX477 CSI {WIDTH}x{HEIGHT}@{FPS} | discarded: {discarded_frames}",(20,HEIGHT-30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(200,200,200),2)
        if speed_display is not None:
            color = (0,255,0) if speed_display<3 else (0,165,255) if speed_display<6 else (0,0,255)
            cv2.putText(annotated,f"Speed: {speed_display:.2f} m/s",(20,100),cv2.FONT_HERSHEY_SIMPLEX,1.5,color,4)
            cv2.putText(annotated,f"Peak:  {peak_speed:.2f} m/s",(20,155),cv2.FONT_HERSHEY_SIMPLEX,1.0,(255,255,0),3)
        cv2.imshow('Gymnast Tracker — IMX477', cv2.resize(annotated,(1280,720)))
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()
    print(f"Peak speed: {peak_speed:.2f} m/s | Discarded frames: {discarded_frames}")

if __name__ == '__main__':
    main()
```

Run: `python3 ~/gymnast_tracker_imx477.py`

---

## 6. Arduino IMU Setup

### 6.1 Hardware

- Arduino Nano 33 BLE Rev2 (BMI270 IMU onboard)
- Mounting location: sternum center
- Connection for programming: USB Micro-B to laptop

### 6.2 Arduino IDE Setup

1. Install Arduino IDE 2.x from arduino.cc
2. Install board: **Tools → Board Manager** → search "Arduino Mbed OS Nano Boards" → install
3. Select board: **Tools → Board → Arduino Nano 33 BLE**
4. Install library: **Tools → Library Manager** → search "Arduino_BMI270_BMM150" → install

### 6.3 Flash the IMU Sketch

Create a new sketch in a new folder and paste the contents of `imu_velocity_logger.ino`.

Key parameters at top of sketch:
- `STILL_THRESHOLD 2.0` — increase if velocity doesn't reset when still
- `HP_ALPHA 0.95` — increase toward 0.99 for less aggressive drift correction
- `LOG_INTERVAL_MS 10` — logging rate (10ms = 100Hz output)

Serial commands during operation:
- `s` — start/stop trial logging
- `r` — reset velocity to zero
- `c` — recalibrate (hold still for 2 seconds after sending)

Open **Serial Plotter or Monitor** at **115200 baud**.

---

## 7. Running the System

### 7.1 USB Camera Only

```bash
python3 ~/gymnast_tracker_usb.py
```

### 7.2 CSI Camera Only

```bash
python3 ~/gymnast_tracker_imx477.py
```

### 7.3 Simultaneous IMU + CV

1. Connect Arduino to laptop via USB
2. Open Arduino Serial Monitor at 115200 baud
3. On Jetson, run appropriate tracker script
4. Send `s` in Serial Monitor to start IMU trial
5. Execute skill
6. Send `s` to stop IMU trial
7. Note peak CV speed from display

---

## 8. Calibration Protocol

### 8.1 CV Pixel-to-Meter Calibration

1. Place a 1-meter reference object (tape measure, meter stick) flat on the floor at the same depth as where the gymnast will be
2. Capture a frame:
   ```bash
   # USB camera:
   python3 -c "import cv2; cap=cv2.VideoCapture(0); ret,f=cap.read(); cv2.imwrite('/tmp/cal.jpg',f); cap.release()"
   ```
3. Open `/tmp/cal.jpg` and measure pixel width of the 1m object
4. Set `PIXELS_PER_METER = <measured pixels>` in the tracker script
5. Record value and camera position — recalibrate if camera moves

### 8.2 Validation Protocol

1. Mark a 5-meter distance on floor with tape
2. Walk/jog/sprint the distance, time with stopwatch → reference speed = 5 / elapsed_time
3. Run both CV and IMU simultaneously during same pass
4. Compare measured speeds to reference
5. Repeat 5 times per speed condition (walk, jog, sprint)

Target accuracy: both systems within ±15% of reference.

---

## 9. Known Issues and Fixes

| Issue | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: torch` | CPU-only torch installed | `pip3 uninstall torch && pip3 install --no-cache-dir <nvidia_wheel.whl>` |
| `ImportError: libcusparseLt.so.0` | Missing library | Follow Section 2.3 |
| `PackageNotFoundError: torchvision` | No pip metadata | `pip3 install --no-build-isolation .` from source dir |
| OpenCV build fails at 33% with cudev error | OpenCV 4.8.x incompatible with CUDA 12.x | Use OpenCV 4.10.0 — has the fix |
| IMX477: `Could not open camera` | OpenCV lacks GStreamer | Follow Section 3B.6 |
| IMX477: camera not detected | Overlay not loaded | Run `jetson-io.py`, select IMX477-A, reboot |
| IMX477: cannot achieve focus | C-to-CS adapter missing | Install 5mm adapter ring between lens and camera |
| IMX477: blurry at all distances | Focus ring locked | Loosen set screw on focus ring barrel |
| USB camera ~37fps not 120fps | IMX577 has USB 2.0 chip | Expected — not a bug |
| IMU velocity won't reset | Threshold too low or wrong baud | Increase `STILL_THRESHOLD`; confirm 115200 baud |
| numpy version conflict | lapx/opencv require numpy>=2 | `pip3 install "numpy>=1.26,<2.0"` after installs |
| torch overwritten with CPU version | pip dependency resolution | Always use `--no-deps` when installing packages that depend on torch |
