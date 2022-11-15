from config import Config
import math, time

class MPU6050():

    """
    Raspberry Pi small guide:
    1. sudo raspi-config
    2. Go to Interfacing Options
    3. Hit Yes
    4. sudo reboot

    Private _read_raw_data
    Private _gyro_raw_data
    Private _accel_raw_data
    Private _calc_gyro_offset
    Private _calc_accel_offset
    Private _gyro_angle
    Private _accel_angle

    Public full_angle
    
    Inspired by electronoobs.com/eng_robotica_tut9_2.php
    """

    def __init__(self, device_address, bus, gyro_full_scale_range=1000, accel_full_scale_range=2, calibrate=False):

        # registerification
        self.gyro_config            = 0x1B
        self.accel_config           = 0x1C
        self.power_management       = 0x6B
        self.sample_rate            = 0x19
        self.configuration_register = 0x1A
        self.interrupt_enable       = 0x38
        self.accel_xout_high        = 0x3B
        self.accel_yout_high        = 0x3D
        self.accel_zout_high        = 0x3F
        self.gyro_xout_high         = 0x43
        self.gyro_yout_high         = 0x45
        self.gyro_zout_high         = 0x47
        self.sleep                  = 0x40
        
        self.device_address         = device_address
        self.bus                    = bus
        self.time0                  = None
        self.time1                  = None
        self.gyro_raw_offset_x      = 0
        self.gyro_raw_offset_y      = 0
        self.gyro_raw_offset_z      = 0
        self.acc_angle_offset_x     = 0
        self.acc_angle_offset_y     = 0
        self.total_angle_x          = 0
        self.total_angle_y          = 0
        
        self.rad_to_deg             = 180 / 3.141592654
        
        print("[MPU6050] Initializing ...")

        # register init
        self.bus.write_byte_data(device_address, self.sample_rate, 7)
        self.bus.write_byte_data(device_address, self.power_management, 0)
        self.bus.write_byte_data(device_address, self.power_management, 1)
        self.bus.write_byte_data(device_address, self.configuration_register, 0)
        self.bus.write_byte_data(device_address, self.interrupt_enable, 1)

        # gyro full scale select [4:3]
        # 00 = +/-  250 dps
        # 01 = +/-  500 dps
        # 10 = +/- 1000 dps
        # 11 = +/- 2000 dps
        self.gyro_full_scale_range = gyro_full_scale_range
        if self.gyro_full_scale_range == 250:
            self.gyro_divider = 131.0
            self.gyro_reg = 0x0   
        elif self.gyro_full_scale_range == 500:
            self.gyro_divider = 65.5
            self.gyro_reg = 0x1
        elif self.gyro_full_scale_range == 1000:
            self.gyro_divider = 32.8
            self.gyro_reg = 0x2
        elif self.gyro_full_scale_range == 2000:
            self.gyro_divider = 16.4
            self.gyro_reg = 0x3
        else:
            raise Exception("[MPU6050] ERROR! Unknown gyroscope full-scale range option!")
        self.bus.write_byte_data(device_address, self.gyro_config, self.gyro_reg << 3)

        # accel full scale select [4:3]
        # 00: +/-  2g
        # 01: +/-  4g
        # 10: +/-  8g
        # 11: +/- 16g
        self.accel_full_scale_range = accel_full_scale_range
        if self.accel_full_scale_range == 2:
            self.accel_divider = 16384.0 # 14-bit resolution
            self.accel_reg = 0x0    
        elif self.accel_full_scale_range == 4:
            self.accel_divider = 8192.0 # 13-bit resolution
            self.accel_reg = 0x1
        elif self.accel_full_scale_range == 8:
            self.accel_divider = 4096.0 # 12-bit resolution
            self.accel_reg = 0x2
        elif self.accel_full_scale_range == 16:
            self.accel_divider = 2048.0 # 11-bit resolution
            self.accel_reg = 0x3
        else:
            raise Exception("[MPU6050] ERROR! Unknown accelerometer full-scale range option!")
        self.bus.write_byte_data(device_address, self.accel_config, self.accel_reg << 3)

        # checking for offset config
        if calibrate == False:
            offset_keyword = ["acc_angle_offset_x", "acc_angle_offset_y", "gyro_raw_offset_x", "gyro_raw_offset_y", "gyro_raw_offset_z"]
            for content in offset_keyword:
                value = Config.extract(content)
                if value == None:
                    raise Exception("[MPU6050] ERROR! Please perform gyroscope and accelerometer calibration!")
            self.gyro_raw_offset_x      = float(Config.extract("gyro_raw_offset_x"))
            self.gyro_raw_offset_y      = float(Config.extract("gyro_raw_offset_y"))
            self.gyro_raw_offset_z      = float(Config.extract("gyro_raw_offset_z"))
            self.acc_angle_offset_x     = float(Config.extract("acc_angle_offset_x"))
            self.acc_angle_offset_y     = float(Config.extract("acc_angle_offset_y"))
        else:
            self._calc_gyro_offset()
            self._calc_accel_offset()

    def _read_raw_data(self, addr):
        high = self.bus.read_byte_data(self.device_address, addr)
        low = self.bus.read_byte_data(self.device_address, addr + 1)

        # the data for gyro and accel is divided in two 8-bit registers, so need to combine
        value = (high << 8) | low
        
        if value > 32768:
            value -= 65536
        
        return value
     
    def _gyro_raw_data(self):
        gyro_x = self._read_raw_data(self.gyro_xout_high)
        gyro_y = self._read_raw_data(self.gyro_yout_high)
        gyro_z = self._read_raw_data(self.gyro_zout_high)
	
        gx = (gyro_x / self.gyro_divider) - self.gyro_raw_offset_x
        gy = (gyro_y / self.gyro_divider) - self.gyro_raw_offset_y
        gz = (gyro_z / self.gyro_divider) - self.gyro_raw_offset_z

        return gx, gy, gz

    def _accel_raw_data(self):
        acc_x = self._read_raw_data(self.accel_xout_high)
        acc_y = self._read_raw_data(self.accel_yout_high)
        acc_z = self._read_raw_data(self.accel_zout_high)

        ax = acc_x / self.accel_divider
        ay = acc_y / self.accel_divider
        az = acc_z / self.accel_divider

        return ax, ay, az

    def _calc_gyro_offset(self):
        print("[MPU6050] Calibrating gyro ...")

        offset_loop = 200
        for i in range(0, offset_loop, 1):
            self.gyro_raw_offset_x += self._read_raw_data(self.gyro_xout_high)/self.gyro_divider
            self.gyro_raw_offset_y += self._read_raw_data(self.gyro_yout_high)/self.gyro_divider
            self.gyro_raw_offset_z += self._read_raw_data(self.gyro_zout_high)/self.gyro_divider
        self.gyro_raw_offset_x = self.gyro_raw_offset_x/offset_loop
        self.gyro_raw_offset_y = self.gyro_raw_offset_y/offset_loop
        self.gyro_raw_offset_z = self.gyro_raw_offset_z/offset_loop      

        Config.write("gyro_raw_offset_x", self.gyro_raw_offset_x)
        Config.write("gyro_raw_offset_y", self.gyro_raw_offset_y)
        Config.write("gyro_raw_offset_z", self.gyro_raw_offset_z)

    def _calc_accel_offset(self):
        print("[MPU6050] Calibrating accel ...")

        offset_loop = 200
        for i in range(0, offset_loop, 1):
            ax, ay, az = self._accel_raw_data()
            # The atan() and atan2() functions calculate the arctangent of x and y/x respectively
            self.acc_angle_offset_x += (math.atan2(ay , math.sqrt(pow((ax),2) + pow((az),2)) ) * self.rad_to_deg)
            self.acc_angle_offset_y += (math.atan2(-1 * ax , math.sqrt(pow((ay),2) + pow((az),2)) ) * self.rad_to_deg)

        self.acc_angle_offset_x /= offset_loop
        self.acc_angle_offset_y /= offset_loop

        Config.write("acc_angle_offset_x", self.acc_angle_offset_x)
        Config.write("acc_angle_offset_y", self.acc_angle_offset_y)

    def _gyro_angle(self):
        if self.time0 == None:
            while self.time0 == None:
                self.time0 = time.time()
                time.sleep(1)

        self.time1 = time.time()
        self.elapsed = self.time1 - self.time0
        self.time0 = self.time1

        gx, gy, gz = self._gyro_raw_data()

        gyro_angle_x = gx * self.elapsed
        gyro_angle_y = gy * self.elapsed
        gyro_angle_z = gz * self.elapsed
        
        return gyro_angle_x, gyro_angle_y, gyro_angle_z  

    def _accel_angle(self):
        ax, ay, az = self._accel_raw_data()

        
        acc_angle_x = (math.atan2(ay , math.sqrt(pow((ax),2) + pow((az),2)) ) * self.rad_to_deg) - self.acc_angle_offset_x
        acc_angle_y = (math.atan2(-1 * ax , math.sqrt(pow((ay),2) + pow((az),2)) ) * self.rad_to_deg) - self.acc_angle_offset_y

        return acc_angle_x, acc_angle_y

    def full_angle(self):
        gyro_angle_x, gyro_angle_y, _ = self._gyro_angle()
        acc_angle_x, acc_angle_y = self._accel_angle()

        self.total_angle_x = 0.98 *(self.total_angle_x + gyro_angle_x) + 0.02 * acc_angle_x
        self.total_angle_y = 0.98 *(self.total_angle_y + gyro_angle_y) + 0.02 * acc_angle_y

        return self.total_angle_x, self.total_angle_y
