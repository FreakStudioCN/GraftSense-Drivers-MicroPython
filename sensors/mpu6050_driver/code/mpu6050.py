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

from math import sqrt, atan2, radians ,degrees
from machine import Pin, SoftI2C
from time import sleep_ms, ticks_ms, ticks_diff

# ======================================== 全局变量 ============================================

error_msg = "\nError \n"
i2c_err_str = "not communicate with module at address 0x{:02X}, check wiring"

# ======================================== 功能函数 ============================================

def signedIntFromBytes(x, endian="big"):
    y = int.from_bytes(x, endian)
    if (y >= 0x8000):
        return -((65535 - y) + 1)
    else:
        return y

# ======================================== 自定义类 ============================================

class ComplementaryKalmanFilter:
    def __init__(self, dt=0.01, gyro_weight=0.98, Q_angle=0.001, Q_bias=0.003, R_measure=0.003):
        """
        初始化互补卡尔曼滤波器

        参数:
        dt: 采样时间间隔 (秒)
        gyro_weight: 陀螺仪权重 (0-1)，值越大越相信陀螺仪数据
        """
        self.dt = dt
        self.alpha = gyro_weight  # 互补滤波系数

        # 初始化角度估计 (弧度)
        self.roll = 0.0  # 横滚角
        self.pitch = 0.0  # 俯仰角

        # 卡尔曼滤波器参数
        self.Q_angle = Q_angle  # 过程噪声协方差
        self.Q_bias = Q_bias  # 陀螺仪偏置噪声协方差
        self.R_measure = R_measure  # 测量噪声协方差

        # 卡尔曼滤波器状态
        self.angle = 0.0  # 角度估计
        self.bias = 0.0  # 陀螺仪偏置估计
        self.P = [[0.0, 0.0], [0.0, 0.0]]  # 误差协方差矩阵

        # 时间跟踪
        self.last_time = ticks_ms()

    def update_complementary(self, accel_angle, gyro_rate):
        """
        使用互补滤波更新角度估计

        参数:
        accel_angle: 从加速度计计算的角度 (弧度)
        gyro_rate: 陀螺仪角速度 (弧度/秒)

        返回:
        滤波后的角度 (弧度)
        """
        # 计算时间间隔
        current_time = ticks_ms()
        dt = ticks_diff(current_time, self.last_time) / 1000.0
        self.last_time = current_time

        if dt > 0:
            # 公式1: 陀螺仪积分得到角度
            # θ_gyro = θ_prev + ω * Δt
            gyro_angle = self.angle + gyro_rate * dt

            # 公式2: 互补滤波融合
            # θ_filtered = α * θ_gyro + (1-α) * θ_accel
            self.angle = self.alpha * gyro_angle + (1 - self.alpha) * accel_angle

        return self.angle

    def update_kalman(self, accel_angle, gyro_rate):
        """
        使用卡尔曼滤波更新角度估计

        参数:
        accel_angle: 从加速度计计算的角度 (弧度)
        gyro_rate: 陀螺仪角速度 (弧度/秒)

        返回:
        滤波后的角度 (弧度)
        """
        # 计算时间间隔
        current_time = ticks_ms()
        dt = ticks_diff(current_time, self.last_time) / 1000.0
        self.last_time = current_time

        if dt > 0:
            # ========== 预测步骤（时间更新）==========
            # 公式3: 预测状态
            # x̂_k|k-1 = F_k * x̂_k-1|k-1 + B_k * u_k
            # 其中 x = [θ, b]^T, F = [[1, -Δt], [0, 1]], u = ω
            self.angle += (gyro_rate - self.bias) * dt

            # 公式4: 预测误差协方差
            # P_k|k-1 = F_k * P_k-1|k-1 * F_k^T + Q_k
            # 这里直接展开计算
            self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.Q_angle)
            self.P[0][1] -= dt * self.P[1][1]
            self.P[1][0] -= dt * self.P[1][1]
            self.P[1][1] += self.Q_bias * dt

            # ========== 更新步骤（测量更新）==========
            # 公式5: 计算卡尔曼增益
            # K_k = P_k|k-1 * H_k^T * (H_k * P_k|k-1 * H_k^T + R_k)^{-1}
            # 这里H = [1, 0]，所以简化为：
            S = self.P[0][0] + self.R_measure
            K = [self.P[0][0] / S, self.P[1][0] / S]

            # 公式6: 计算测量残差
            # ỹ_k = z_k - H_k * x̂_k|k-1
            y = accel_angle - self.angle

            # 公式7: 更新状态估计
            # x̂_k|k = x̂_k|k-1 + K_k * ỹ_k
            self.angle += K[0] * y
            self.bias += K[1] * y

            # 公式8: 更新误差协方差
            # P_k|k = (I - K_k * H_k) * P_k|k-1
            P00_temp = self.P[0][0]
            P01_temp = self.P[0][1]

            self.P[0][0] -= K[0] * P00_temp
            self.P[0][1] -= K[0] * P01_temp
            self.P[1][0] -= K[1] * P00_temp
            self.P[1][1] -= K[1] * P01_temp

        return self.angle

    def update_roll_pitch(self, accel_data, gyro_data):
        """
        更新横滚角和俯仰角

        参数:
        accel_data: 加速度计数据字典 {'x': , 'y': , 'z': }
        gyro_data: 陀螺仪数据字典 {'x': , 'y': , 'z': }

        返回:
        (roll, pitch) 横滚角和俯仰角 (弧度)
        """
        # 将角速度从度/秒转换为弧度/秒
        # 公式9: ω_rad = ω_deg * π / 180
        gyro_roll_rate = radians(gyro_data['y'])
        gyro_pitch_rate = radians(gyro_data['x'])

        # 从加速度计计算角度
        acc_x = accel_data['x']
        acc_y = accel_data['y']
        acc_z = accel_data['z']

        # 公式10: 加速度计横滚角（绕X轴）
        # φ_accel = atan2(a_y, sqrt(a_x² + a_z²))
        accel_roll = atan2(acc_y, sqrt(acc_x * acc_x + acc_z * acc_z))

        # 公式11: 加速度计俯仰角（绕Y轴）
        # θ_accel = atan2(-a_x, sqrt(a_y² + a_z²))
        accel_pitch = atan2(-acc_x, sqrt(acc_y * acc_y + acc_z * acc_z))

        # 分别滤波横滚角和俯仰角
        # 公式12: 使用卡尔曼滤波分别估计横滚和俯仰
        self.roll = self.update_kalman(accel_roll, gyro_roll_rate)
        self.pitch = self.update_kalman(accel_pitch, gyro_pitch_rate)

        return self.roll, self.pitch

    def get_angles_degrees(self):
        """获取角度（度）"""
        # 公式13: 弧度转角度
        # angle_deg = angle_rad * 180 / π
        return degrees(self.roll), degrees(self.pitch)

    def get_angles_radians(self):
        """获取角度（弧度）"""
        return self.roll, self.pitch

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


    def __init__(self, i2c,addr=_MPU6050_ADDRESS):
        # Checks any erorr would happen with I2C communication protocol.
        self._failCount = 0
        self._terminatingFailCount = 0

        self.i2c = i2c
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
        x = signedIntFromBytes(data[0:2])
        y = signedIntFromBytes(data[2:4])
        z = signedIntFromBytes(data[4:6])
        return {"x": x, "y": y, "z": z}

    # Reads the temperature from the onboard temperature sensor of the MPU-6050.
    # Returns the temperature [degC].
    def read_temperature(self):
        try:
            rawData = self.i2c.readfrom_mem(self.addr, MPU6050._TEMP_OUT0, 2)
            raw_temp = (signedIntFromBytes(rawData, "big"))
        except:
            print(i2c_err_str.format(self.addr))
            return float("NaN")
        actual_temp = (raw_temp / 340) + 36.53
        return actual_temp

    # Sets the range of the accelerometer
    # accel_range : the range to set the accelerometer to. Using a pre-defined range is advised.
    def set_accel_range(self, accel_range):
        if accel_range not in [MPU6050._ACC_RNG_2G, MPU6050._ACC_RNG_4G, MPU6050._ACC_RNG_8G, MPU6050._ACC_RNG_16G]:
            print("Error: Invalid accelerometer range. Range not set.")
            return
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
        if gyro_range not in [MPU6050._GYR_RNG_250DEG, MPU6050._GYR_RNG_500DEG, MPU6050._GYR_RNG_1000DEG, MPU6050._GYR_RNG_2000DEG]:
            print("Error: Invalid gyroscope range. Range not set.")
            return
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
