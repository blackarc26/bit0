#include <Wire.h>

// MPU-9250 air-mouse firmware.
//
// Output, one line per sample, 100 Hz:
//   ax,ay,az,gx,gy,gz,micros
//   ax..az in g, gx..gz in degrees/second, micros = device clock.
//
// The host reads the 7th field when present (older 6-field firmware still
// works). Using the device clock removes the USB-serial timing jitter from
// the motion integration.

const uint8_t MPU9250_ADDRESS = 0x68;

// 100 Hz. For 200 Hz set 5000 and raise Serial to 460800 (and the same
// baud_rate in airmouse/config.py), otherwise the serial link is too slow.
const unsigned long SAMPLE_INTERVAL_US = 10000;

// Gyro range. Fast wrist flicks can pass 250 deg/s, which clips and
// distorts strokes, so use +-500 deg/s.
//   0x00 = +-250 (131.0)   0x08 = +-500 (65.5)   0x10 = +-1000 (32.8)
const uint8_t GYRO_RANGE_BITS = 0x08;
const float GYRO_LSB_PER_DPS = 65.5;

const float ACCEL_LSB_PER_G = 16384.0;   // +-2 g

unsigned long nextSampleUs = 0;


void setup() {
  Wire.begin();
  Wire.setClock(400000);          // fast I2C: keeps the read well inside 10 ms

  Serial.begin(115200);
  delay(1000);

  setupMPU9250();

  nextSampleUs = micros() + SAMPLE_INTERVAL_US;
}


void loop() {
  unsigned long now = micros();

  // Fixed schedule: no drift, even if one loop is late.
  if ((long)(now - nextSampleUs) >= 0) {
    nextSampleUs += SAMPLE_INTERVAL_US;
    readSensorData(now);
  }
}


void setupMPU9250() {
  writeMPU9250(0x6B, 0x00);             // wake up
  writeMPU9250(0x1B, GYRO_RANGE_BITS);  // gyro range
  writeMPU9250(0x1C, 0x00);             // accelerometer +-2 g
  writeMPU9250(0x1A, 0x03);             // gyro low-pass ~41 Hz
}


void readSensorData(unsigned long sampleTimeUs) {
  Wire.beginTransmission(MPU9250_ADDRESS);
  Wire.write(0x3B);                     // ACCEL_XOUT_H
  Wire.endTransmission(false);

  Wire.requestFrom(MPU9250_ADDRESS, (uint8_t)14);
  if (Wire.available() < 14) {
    return;
  }

  int16_t accelX = (Wire.read() << 8) | Wire.read();
  int16_t accelY = (Wire.read() << 8) | Wire.read();
  int16_t accelZ = (Wire.read() << 8) | Wire.read();
  Wire.read(); Wire.read();             // temperature (unused)
  int16_t gyroX = (Wire.read() << 8) | Wire.read();
  int16_t gyroY = (Wire.read() << 8) | Wire.read();
  int16_t gyroZ = (Wire.read() << 8) | Wire.read();

  Serial.print(accelX / ACCEL_LSB_PER_G, 3);  Serial.print(",");
  Serial.print(accelY / ACCEL_LSB_PER_G, 3);  Serial.print(",");
  Serial.print(accelZ / ACCEL_LSB_PER_G, 3);  Serial.print(",");
  Serial.print(gyroX / GYRO_LSB_PER_DPS, 3);  Serial.print(",");
  Serial.print(gyroY / GYRO_LSB_PER_DPS, 3);  Serial.print(",");
  Serial.print(gyroZ / GYRO_LSB_PER_DPS, 3);  Serial.print(",");
  Serial.println(sampleTimeUs);
}


void writeMPU9250(byte reg, byte data) {
  Wire.beginTransmission(MPU9250_ADDRESS);
  Wire.write(reg);
  Wire.write(data);
  Wire.endTransmission();
}
