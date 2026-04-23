/*
 * Gymnast IMU Velocity Tracker — Data Logging Version
 * Hardware: Arduino Nano 33 BLE Rev2 (BMI270)
 * 
 * Outputs:
 *   - Serial: CSV at 115200 baud for real-time monitoring
 *   - Serial commands: 'r' = reset velocity, 's' = start/stop trial logging
 * 
 * Mount location: Sternum (chest)
 * Orientation: USB connector pointing down
 */

#include "Arduino_BMI270_BMM150.h"
#include <Wire.h>

// ── Configuration ─────────────────────────────────────────────────────────────
const float G_TO_MS2        = 9.81;
const float STILL_THRESHOLD = 2.0;    // m/s² — tune if false resets occur
const int   ZERO_VEL_COUNT  = 20;     // ~200ms at 104Hz before reset
const float HP_ALPHA        = 0.95;   // high-pass filter (0.9=aggressive, 0.99=gentle)
const int   LOG_INTERVAL_MS = 10;     // log every 10ms = 100Hz output rate

// ── State ─────────────────────────────────────────────────────────────────────
float vx=0, vy=0, vz=0;
float ax_hp=0, ay_hp=0, az_hp=0;
float ax_prev=0, ay_prev=0, az_prev=0;
unsigned long last_us=0;
unsigned long last_log_ms=0;
int still_count=0;
bool logging=false;
unsigned long trial_start_ms=0;
unsigned long sample_count=0;
float peak_speed=0;

// ── IMU Setup ──────────────────────────────────────────────────────────────────
void setRange16g() {
    // BMI270 ACC_RANGE register: 0x41, value 0x03 = ±16g
    Wire1.beginTransmission(0x68);
    Wire1.write(0x41);
    Wire1.write(0x03);
    Wire1.endTransmission();
    delay(10);
}

void calibrate() {
    Serial.println("# Hold still for 2-second calibration...");
    float bx=0, by=0, bz=0;
    int n=0;
    unsigned long t=millis();
    while (millis()-t < 2000) {
        if (IMU.accelerationAvailable()) {
            float ax, ay, az;
            IMU.readAcceleration(ax, ay, az);
            bx += ax*4.0*G_TO_MS2;
            by += ay*4.0*G_TO_MS2;
            bz += az*4.0*G_TO_MS2;
            n++;
        }
    }
    ax_prev = bx/n;
    ay_prev = by/n;
    az_prev = bz/n;
    Serial.print("# Calibration complete. Bias: ");
    Serial.print(ax_prev,3); Serial.print(", ");
    Serial.print(ay_prev,3); Serial.print(", ");
    Serial.println(az_prev,3);
}

// ── Setup ──────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    while (!Serial);
    Wire1.begin();

    if (!IMU.begin()) {
        Serial.println("# ERROR: IMU failed to initialize!");
        while (1);
    }

    setRange16g();
    calibrate();

    Serial.println("# Commands: 's' = start/stop trial, 'r' = reset velocity, 'c' = recalibrate");
    Serial.println("# CSV format: timestamp_ms,ax,ay,az,vx,vy,vz,speed,peak_speed");
    Serial.println("timestamp_ms,ax_mps2,ay_mps2,az_mps2,vx_mps,vy_mps,vz_mps,speed_mps,peak_mps");

    last_us = micros();
    last_log_ms = millis();
}

// ── Main Loop ──────────────────────────────────────────────────────────────────
void loop() {

    // Handle serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        if (cmd == 's') {
            logging = !logging;
            if (logging) {
                trial_start_ms = millis();
                peak_speed = 0;
                sample_count = 0;
                vx = vy = vz = 0;
                Serial.println("# TRIAL STARTED");
            } else {
                Serial.print("# TRIAL ENDED — samples: ");
                Serial.print(sample_count);
                Serial.print(" | peak speed: ");
                Serial.print(peak_speed, 3);
                Serial.println(" m/s");
            }
        } else if (cmd == 'r') {
            vx = vy = vz = 0;
            peak_speed = 0;
            Serial.println("# Velocity reset");
        } else if (cmd == 'c') {
            calibrate();
        }
    }

    if (!IMU.accelerationAvailable()) return;

    // Read and scale to ±16g
    float ax_raw, ay_raw, az_raw;
    IMU.readAcceleration(ax_raw, ay_raw, az_raw);
    float ax = ax_raw * 4.0 * G_TO_MS2;
    float ay = ay_raw * 4.0 * G_TO_MS2;
    float az = az_raw * 4.0 * G_TO_MS2;

    // High-pass filter — removes gravity and low-frequency drift
    ax_hp = HP_ALPHA * (ax_hp + ax - ax_prev);
    ay_hp = HP_ALPHA * (ay_hp + ay - ay_prev);
    az_hp = HP_ALPHA * (az_hp + az - az_prev);
    ax_prev = ax;
    ay_prev = ay;
    az_prev = az;

    // Timing
    unsigned long now_us = micros();
    float dt = (now_us - last_us) / 1e6;
    last_us = now_us;

    // Zero-velocity update
    float accel_mag = sqrt(ax_hp*ax_hp + ay_hp*ay_hp + az_hp*az_hp);
    if (accel_mag < STILL_THRESHOLD) {
        still_count++;
        if (still_count >= ZERO_VEL_COUNT) {
            vx = vy = vz = 0;
        }
    } else {
        still_count = 0;
        vx += ax_hp * dt;
        vy += ay_hp * dt;
        vz += az_hp * dt;
    }

    float speed = sqrt(vx*vx + vy*vy + vz*vz);
    if (speed > peak_speed) peak_speed = speed;

    // Log at defined interval
    unsigned long now_ms = millis();
    if (logging && (now_ms - last_log_ms >= LOG_INTERVAL_MS)) {
        last_log_ms = now_ms;
        sample_count++;

        unsigned long t_rel = now_ms - trial_start_ms;
        Serial.print(t_rel);        Serial.print(",");
        Serial.print(ax_hp, 3);     Serial.print(",");
        Serial.print(ay_hp, 3);     Serial.print(",");
        Serial.print(az_hp, 3);     Serial.print(",");
        Serial.print(vx, 3);        Serial.print(",");
        Serial.print(vy, 3);        Serial.print(",");
        Serial.print(vz, 3);        Serial.print(",");
        Serial.print(speed, 3);     Serial.print(",");
        Serial.println(peak_speed, 3);
    }

    // Always output to plotter (even when not logging a trial)
    // Comment out this block if you only want trial data
    if (!logging && (now_ms - last_log_ms >= LOG_INTERVAL_MS)) {
        last_log_ms = now_ms;
        Serial.print("Ax(m/s2):"); Serial.print(ax_hp,3); Serial.print(",");
        Serial.print("Ay(m/s2):"); Serial.print(ay_hp,3); Serial.print(",");
        Serial.print("Az(m/s2):"); Serial.print(az_hp,3); Serial.print(",");
        Serial.print("Vx(m/s):");  Serial.print(vx,3);    Serial.print(",");
        Serial.print("Vy(m/s):");  Serial.print(vy,3);    Serial.print(",");
        Serial.print("Vz(m/s):");  Serial.print(vz,3);    Serial.print(",");
        Serial.print("Speed(m/s):"); Serial.println(speed,3);
    }
}
