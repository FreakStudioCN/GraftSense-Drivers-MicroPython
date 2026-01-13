# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/13 上午10:32
# @Author  : hogeiha
# @File    : mpu6050.py
# @Description : 串口IMU驱动代码
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from math import sqrt, atan2
from machine import Pin, SoftI2C
from time import sleep_ms, ticks_ms, ticks_diff

# ======================================== 全局变量 ============================================

error_msg = "\nError \n"
i2c_err_str = "not communicate with module at address 0x{:02X}, check wiring"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SimpleComplementaryFilter:
    """
    简单互补滤波器
    融合加速度计和陀螺仪数据计算俯仰角和滚转角
    """

    def __init__(self, alpha=0.98):
        """
        初始化滤波器

        参数:
        alpha: 滤波器系数 (0.0-1.0)
              0.98: 推荐值，98%信任陀螺仪，2%信任加速度计
        """
        self.alpha = alpha
        self.last_time = None

        # 角度初始值
        self.pitch = 0.0  # 俯仰角 (绕X轴)
        self.roll = 0.0  # 滚转角 (绕Y轴)

        # 陀螺仪零偏
        self.gyro_offset_x = 0.0
        self.gyro_offset_y = 0.0

    def signedIntFromBytes(self, x, endian="big"):
        """从字节转换为有符号整数"""
        y = int.from_bytes(x, endian)
        if (y >= 0x8000):
            return -((65535 - y) + 1)
        else:
            return y
    def calibrate(self, mpu, samples=100):
        """
        校准陀螺仪零偏
        将传感器静止放置，然后调用此函数
        """
        print("正在校准陀螺仪，请保持静止...")

        sum_x = 0.0
        sum_y = 0.0

        for i in range(samples):
            gyro = mpu.read_gyro_data()
            sum_x += gyro["x"]
            sum_y += gyro["y"]
            sleep_ms(10)  # 等待10ms

        self.gyro_offset_x = sum_x / samples
        self.gyro_offset_y = sum_y / samples

        print(f"校准完成: X偏移={self.gyro_offset_x:.2f}, Y偏移={self.gyro_offset_y:.2f}")

    def update(self, mpu):
        """
        更新滤波器，返回当前角度(pitch, roll)
        """
        # 获取当前时间
        current_time = ticks_ms()

        # 如果是第一次调用，只初始化时间
        if self.last_time is None:
            self.last_time = current_time
            return self.pitch, self.roll

        # 计算时间差（秒）
        dt = ticks_diff(current_time, self.last_time) / 1000.0
        self.last_time = current_time

        # 如果时间差太小，跳过
        if dt <= 0 or dt > 0.1:  # 避免过大或过小的时间差
            dt = 0.01  # 默认10ms

        # 读取传感器数据
        accel = mpu.read_accel_data(g=False)  # m/s²
        gyro = mpu.read_gyro_data()  # °/s

        # 1. 从加速度计计算角度
        ax, ay, az = accel["x"], accel["y"], accel["z"]

        # 计算俯仰角 (pitch) 和滚转角 (roll)，单位：度
        pitch_acc = math.degrees(math.atan2(ay, math.sqrt(ax * ax + az * az)))
        roll_acc = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))

        # 2. 从陀螺仪计算角度变化
        # 减去零偏
        gyro_y = gyro["y"] - self.gyro_offset_y  # 俯仰角变化率
        gyro_x = gyro["x"] - self.gyro_offset_x  # 滚转角变化率

        # 陀螺仪积分
        pitch_gyro = self.pitch + gyro_y * dt
        roll_gyro = self.roll + gyro_x * dt

        # 3. 互补滤波融合
        # alpha越大，越信任陀螺仪；alpha越小，越信任加速度计
        self.pitch = self.alpha * pitch_gyro + (1 - self.alpha) * pitch_acc
        self.roll = self.alpha * roll_gyro + (1 - self.alpha) * roll_acc

        return self.pitch, self.roll

    def get_angles(self):
        """获取当前角度"""
        return self.pitch, self.roll

    def reset(self):
        """重置滤波器"""
        self.pitch = 0.0
        self.roll = 0.0
        self.last_time = None

class MPU6050(object):
    # Global Variables
    _GRAVITIY_MS2 = 9.80665
    # Scale Modifiers
    _ACC_SCLR_2G = 16384.0
    _ACC_SCLR_4G = 8192.0
    _ACC_SCLR_8G = 4096.0
    _ACC_SCLR_16G = 2048.0

    _GYR_SCLR_250DEG = 131.0
    _GYR_SCLR_500DEG = 65.5
    _GYR_SCLR_1000DEG = 32.8
    _GYR_SCLR_2000DEG = 16.4

    # Pre-defined ranges
    _ACC_RNG_2G = 0x00
    _ACC_RNG_4G = 0x08
    _ACC_RNG_8G = 0x10
    _ACC_RNG_16G = 0x18

    _GYR_RNG_250DEG = 0x00
    _GYR_RNG_500DEG = 0x08
    _GYR_RNG_1000DEG = 0x10
    _GYR_RNG_2000DEG = 0x18

    # MPU-6050 Registers
    _PWR_MGMT_1 = 0x6B

    _ACCEL_XOUT0 = 0x3B

    _TEMP_OUT0 = 0x41

    _GYRO_XOUT0 = 0x43

    _ACCEL_CONFIG = 0x1C
    _GYRO_CONFIG = 0x1B

    _maxFails = 3

    # Address
    _MPU6050_ADDRESS = 0x68


    def __init__(self, bus=None, freq=None, sda=None, scl=None, addr=_MPU6050_ADDRESS):
        # Checks any erorr would happen with I2C communication protocol.
        self._failCount = 0
        self._terminatingFailCount = 0

        # Initializing the I2C method for ESP32
        # Pin assignment:
        # SCL -> GPIO 22
        # SDA -> GPIO 21
        self.i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)

        # Initializing the I2C method for ESP8266
        # Pin assignment:
        # SCL -> GPIO 5
        # SDA -> GPIO 4
        # self.i2c = I2C(scl=Pin(5), sda=Pin(4))

        self.addr = addr
        try:
            # Wake up the MPU-6050 since it starts in sleep mode
            self.i2c.writeto_mem(self.addr, MPU6050._PWR_MGMT_1, bytes([0x00]))
            sleep_ms(5)
        except Exception as e:
            print(i2c_err_str.format(self.addr))
            print(error_msg)
            raise e
        self._accel_range = self.get_accel_range(True)
        self._gyro_range = self.get_gyro_range(True)

    def _readData(self, register):
        failCount = 0
        while failCount < MPU6050._maxFails:
            try:
                sleep_ms(10)
                data = self.i2c.readfrom_mem(self.addr, register, 6)
                break
            except:
                failCount = failCount + 1
                self._failCount = self._failCount + 1
                if failCount >= MPU6050._maxFails:
                    self._terminatingFailCount = self._terminatingFailCount + 1
                    print(i2c_err_str.format(self.addr))
                    return {"x": float("NaN"), "y": float("NaN"), "z": float("NaN")}
        x = self.signedIntFromBytes(data[0:2])
        y = self.signedIntFromBytes(data[2:4])
        z = self.signedIntFromBytes(data[4:6])
        return {"x": x, "y": y, "z": z}

    # Reads the temperature from the onboard temperature sensor of the MPU-6050.
    # Returns the temperature [degC].
    def read_temperature(self):
        try:
            rawData = self.i2c.readfrom_mem(self.addr, MPU6050._TEMP_OUT0, 2)
            raw_temp = (self.signedIntFromBytes(rawData, "big"))
        except:
            print(i2c_err_str.format(self.addr))
            return float("NaN")
        actual_temp = (raw_temp / 340) + 36.53
        return actual_temp

    # Sets the range of the accelerometer
    # accel_range : the range to set the accelerometer to. Using a pre-defined range is advised.
    def set_accel_range(self, accel_range):
        self.i2c.writeto_mem(self.addr, MPU6050._ACCEL_CONFIG, bytes([accel_range]))
        self._accel_range = accel_range

    # Gets the range the accelerometer is set to.
    # raw=True: Returns raw value from the ACCEL_CONFIG register
    # raw=False: Return integer: -1, 2, 4, 8 or 16. When it returns -1 something went wrong.
    def get_accel_range(self, raw=False):
        # Get the raw value
        raw_data = self.i2c.readfrom_mem(self.addr, MPU6050._ACCEL_CONFIG, 2)

        if raw is True:
            return raw_data[0]
        elif raw is False:
            if raw_data[0] == MPU6050._ACC_RNG_2G:
                return 2
            elif raw_data[0] == MPU6050._ACC_RNG_4G:
                return 4
            elif raw_data[0] == MPU6050._ACC_RNG_8G:
                return 8
            elif raw_data[0] == MPU6050._ACC_RNG_16G:
                return 16
            else:
                return -1

    # Reads and returns the AcX, AcY and AcZ values from the accelerometer.
    # Returns dictionary data in g or m/s^2 (g=False)
    def read_accel_data(self, g=False):
        accel_data = self._readData(MPU6050._ACCEL_XOUT0)
        accel_range = self._accel_range
        scaler = None
        if accel_range == MPU6050._ACC_RNG_2G:
            scaler = MPU6050._ACC_SCLR_2G
        elif accel_range == MPU6050._ACC_RNG_4G:
            scaler = MPU6050._ACC_SCLR_4G
        elif accel_range == MPU6050._ACC_RNG_8G:
            scaler = MPU6050._ACC_SCLR_8G
        elif accel_range == MPU6050._ACC_RNG_16G:
            scaler = MPU6050._ACC_SCLR_16G
        else:
            print("Unkown range - scaler set to _ACC_SCLR_2G")
            scaler = MPU6050._ACC_SCLR_2G

        x = accel_data["x"] / scaler
        y = accel_data["y"] / scaler
        z = accel_data["z"] / scaler

        if g is True:
            return {"x": x, "y": y, "z": z}
        elif g is False:
            x = x * MPU6050._GRAVITIY_MS2
            y = y * MPU6050._GRAVITIY_MS2
            z = z * MPU6050._GRAVITIY_MS2
            return {"x": x, "y": y, "z": z}

    def read_accel_abs(self, g=False):
        d = self.read_accel_data(g)
        return sqrt(d["x"] ** 2 + d["y"] ** 2 + d["z"] ** 2)

    def set_gyro_range(self, gyro_range):
        self.i2c.writeto_mem(self.addr, MPU6050._GYRO_CONFIG, bytes([gyro_range]))
        self._gyro_range = gyro_range

    # Gets the range the gyroscope is set to.
    # raw=True: return raw value from GYRO_CONFIG register
    # raw=False: return range in deg/s
    def get_gyro_range(self, raw=False):
        # Get the raw value
        raw_data = self.i2c.readfrom_mem(self.addr, MPU6050._GYRO_CONFIG, 2)

        if raw is True:
            return raw_data[0]
        elif raw is False:
            if raw_data[0] == MPU6050._GYR_RNG_250DEG:
                return 250
            elif raw_data[0] == MPU6050._GYR_RNG_500DEG:
                return 500
            elif raw_data[0] == MPU6050._GYR_RNG_1000DEG:
                return 1000
            elif raw_data[0] == MPU6050._GYR_RNG_2000DEG:
                return 2000
            else:
                return -1

    # Gets and returns the GyX, GyY and GyZ values from the gyroscope.
    # Returns the read values in a dictionary.
    def read_gyro_data(self):
        gyro_data = self._readData(MPU6050._GYRO_XOUT0)
        gyro_range = self._gyro_range
        scaler = None
        if gyro_range == MPU6050._GYR_RNG_250DEG:
            scaler = MPU6050._GYR_SCLR_250DEG
        elif gyro_range == MPU6050._GYR_RNG_500DEG:
            scaler = MPU6050._GYR_SCLR_500DEG
        elif gyro_range == MPU6050._GYR_RNG_1000DEG:
            scaler = MPU6050._GYR_SCLR_1000DEG
        elif gyro_range == MPU6050._GYR_RNG_2000DEG:
            scaler = MPU6050._GYR_SCLR_2000DEG
        else:
            print("Unkown range - scaler set to _GYR_SCLR_250DEG")
            scaler = MPU6050._GYR_SCLR_250DEG

        x = gyro_data["x"] / scaler
        y = gyro_data["y"] / scaler
        z = gyro_data["z"] / scaler

        return {"x": x, "y": y, "z": z}

    def read_angle(self):  # returns radians. orientation matches silkscreen
        a = self.read_accel_data()
        x = atan2(a["y"], a["z"])
        y = atan2(-a["x"], a["z"])
        return {"x": x, "y": y}

    # ======================================== 初始化配置 ==========================================

    # ========================================  主程序  ============================================
