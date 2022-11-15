from mpu6050 import MPU6050
import smbus

bus = smbus.SMBus(1)
mpu6050 = MPU6050(0x68, bus, calibrate=False)
while True:
	angle_x, angle_y = mpu6050.full_angle()
	print(angle_x, angle_y)
