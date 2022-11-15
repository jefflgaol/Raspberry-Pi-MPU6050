# Raspberry-Pi-MPU6050
This is an example on how to read gyroscope and accelerometer angle data from MPU6050 in Python using Raspberry Pi. The code is also equipped with calibration function to measure the offset.

![alt text](https://github.com/jefflgaol/Raspberry-Pi-MPU6050/blob/main/meow.gif)

## Example
```
from mpu6050 import MPU6050
import smbus

bus = smbus.SMBus(1)
mpu6050 = MPU6050(0x68, bus, calibrate=False)
while True:
	angle_x, angle_y = mpu6050.full_angle()
	print(angle_x, angle_y)
```

## Example for calibration
Please make sure the sensor is properly placed before running this.
```
mpu6050 = MPU6050(0x68, bus, calibrate=True)
```
