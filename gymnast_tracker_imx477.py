from ultralytics import YOLO
import cv2, numpy as np, time
from collections import deque

# ── Configuration ──────────────────────────────────────────────────────────
WIDTH, HEIGHT       = 1920, 1080
FPS                 = 60
PIXELS_PER_METER    = 150    # CALIBRATE before each session — see calibration protocol
SMOOTHING_FRAMES    = 5

# ── Velocity filtering thresholds ──────────────────────────────────────────
# These three values are the primary quality control parameters.
# Adjust KP_CONF_COM down if valid detections are being skipped in good lighting.
# Adjust MAX_PLAUSIBLE_SPEED up slightly if tracking elite sprinters (>10 m/s).
KP_CONF_COM         = 0.6    # min keypoint confidence to compute CoM
                              # 0.3 = permissive (original), 0.6 = recommended, 0.8 = strict
KP_CONF_PEAK        = 0.75   # min keypoint confidence to update peak speed record
                              # higher than KP_CONF_COM — peak should only reflect clean detections
MAX_PLAUSIBLE_SPEED = 12.0   # m/s — readings above this are discarded as artifacts
                              # world-record 100m sprint avg ~10.4 m/s, peak ~12.4 m/s

KP = dict(l_hip=11, r_hip=12)

# ── GStreamer pipeline ──────────────────────────────────────────────────────
def gstreamer_pipeline(width=1920, height=1080, fps=60, flip=0):
    return (
        f"nvarguscamerasrc sensor-id=0 ! "
        f"video/x-raw(memory:NVMM),width={width},height={height},framerate={fps}/1 ! "
        f"nvvidconv flip-method={flip} ! "
        f"video/x-raw,width={width},height={height},format=BGRx ! "
        f"videoconvert ! video/x-raw,format=BGR ! appsink max-buffers=1 drop=true"
    )

# ── CoM from hip keypoints ──────────────────────────────────────────────────
def center_of_mass(kps):
    l, r = kps[KP['l_hip']], kps[KP['r_hip']]
    # Both hips must exceed confidence threshold — partial detections are skipped
    if l[2] > KP_CONF_COM and r[2] > KP_CONF_COM:
        return np.array([(l[0]+r[0])/2, (l[1]+r[1])/2])
    return None

# ── Least-squares velocity over history window ──────────────────────────────
def compute_velocity(history, px_per_m):
    if len(history) < 2: return None, None
    positions = [h[0] for h in history]
    times     = [h[1] for h in history]
    t  = np.array(times) - times[0]
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

# ── Main loop ───────────────────────────────────────────────────────────────
def main():
    model = YOLO('yolov8n-pose.pt')

    print("Opening IMX477 via GStreamer...")
    cap = cv2.VideoCapture(gstreamer_pipeline(WIDTH, HEIGHT, FPS), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("ERROR: Could not open IMX477.")
        print("Check: camera connected, IMX477-A overlay loaded (jetson-io.py), OpenCV built with GStreamer")
        return

    for _ in range(3): cap.read()
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Could not read frame from IMX477.")
        return

    # Warmup inference pass — avoids latency spike on first real frame
    model(frame, verbose=False, device='cuda')
    print(f"IMX477 ready — {WIDTH}x{HEIGHT}@{FPS}fps")
    print(f"Filters: CoM conf>{KP_CONF_COM} | Peak conf>{KP_CONF_PEAK} | Max speed<{MAX_PLAUSIBLE_SPEED}m/s")
    print("Press Q to quit.")

    history        = deque(maxlen=SMOOTHING_FRAMES)
    fps_hist       = deque(maxlen=30)
    peak_speed     = 0.0
    discarded      = 0   # frames discarded by speed clamp — logged at exit

    while True:
        ret, frame = cap.read()
        if not ret: break
        t0 = time.time()

        results = model(frame, verbose=False, device='cuda')
        fps_hist.append(1.0 / (time.time() - t0 + 1e-6))
        annotated    = results[0].plot()
        speed_display = None

        if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            kps = results[0].keypoints.data[0].cpu().numpy()
            com = center_of_mass(kps)

            if com is not None:
                history.append((com, t0))
                speed, vec = compute_velocity(history, PIXELS_PER_METER)

                if speed is not None:
                    if speed > MAX_PLAUSIBLE_SPEED:
                        # Physically impossible — artifact from partial/erratic detection
                        # Clear history so poisoned positions don't influence next frames
                        discarded += 1
                        history.clear()
                    else:
                        speed_display = speed

                        # Peak update — only when both hips are cleanly detected
                        l_conf = kps[KP['l_hip']][2]
                        r_conf = kps[KP['r_hip']][2]
                        if min(l_conf, r_conf) > KP_CONF_PEAK:
                            peak_speed = max(peak_speed, speed)

                        # Draw CoM marker and velocity arrow
                        cx, cy = int(com[0]), int(com[1])
                        cv2.circle(annotated, (cx, cy), 10, (0, 0, 255), -1)
                        if vec is not None and np.linalg.norm(vec) > 0.1:
                            ex = int(cx + vec[0] * 50)
                            ey = int(cy + vec[1] * 50)
                            cv2.arrowedLine(annotated, (cx,cy), (ex,ey), (0,255,255), 3, tipLength=0.3)

        # HUD
        avg_fps = sum(fps_hist) / len(fps_hist)
        cv2.putText(annotated, f"FPS: {avg_fps:.1f}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)
        cv2.putText(annotated, f"IMX477 CSI {WIDTH}x{HEIGHT}@{FPS} | discarded: {discarded}",
                    (20, HEIGHT-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

        if speed_display is not None:
            color = (0,255,0) if speed_display < 3 else (0,165,255) if speed_display < 6 else (0,0,255)
            cv2.putText(annotated, f"Speed: {speed_display:.2f} m/s", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 4)
            cv2.putText(annotated, f"Peak:  {peak_speed:.2f} m/s", (20, 155),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,0), 3)

        cv2.imshow('Gymnast Tracker — IMX477', cv2.resize(annotated, (1280, 720)))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nSession summary:")
    print(f"  Peak speed:       {peak_speed:.2f} m/s")
    print(f"  Discarded frames: {discarded} (speed > {MAX_PLAUSIBLE_SPEED} m/s or conf < {KP_CONF_COM})")

if __name__ == '__main__':
    main()
