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
    """
    互补卡尔曼滤波器类。

    该类实现了用于MPU6050姿态解算的融合算法，结合了互补滤波和卡尔曼滤波的优点。
    通过融合加速度计和陀螺仪数据，获得更稳定的角度估计。

    Attributes:
        dt: 采样时间间隔（秒）。
        alpha: 互补滤波系数（0-1），值越大越相信陀螺仪数据。
        Q_angle: 过程噪声协方差。
        Q_bias: 陀螺仪偏置噪声协方差。
        R_measure: 测量噪声协方差。
        angle: 角度估计（弧度）。
        bias: 陀螺仪偏置估计。
        P: 误差协方差矩阵。
        last_time: 上一次更新时间。
        roll: 横滚角估计（弧度）。
        pitch: 俯仰角估计（弧度）。

    Methods:
        __init__(): 初始化滤波器参数。
        update_complementary(): 使用互补滤波更新角度估计。
        update_kalman(): 使用卡尔曼滤波更新角度估计。
        update_roll_pitch(): 更新横滚角和俯仰角。
        get_angles_degrees(): 获取角度（度）。
        get_angles_radians(): 获取角度（弧度）。

    ==========================================

    Complementary Kalman Filter class.

    This class implements a fusion algorithm for MPU6050 attitude calculation,
    combining the advantages of complementary filtering and Kalman filtering.
    By fusing accelerometer and gyroscope data, more stable angle estimation is obtained.

    Attributes:
        dt: Sampling time interval (seconds).
        alpha: Complementary filter coefficient (0-1), higher values trust gyroscope more.
        Q_angle: Process noise covariance.
        Q_bias: Gyroscope bias noise covariance.
        R_measure: Measurement noise covariance.
        angle: Angle estimation (radians).
        bias: Gyroscope bias estimation.
        P: Error covariance matrix.
        last_time: Last update time.
        roll: Roll angle estimation (radians).
        pitch: Pitch angle estimation (radians).

    Methods:
        __init__(): Initialize filter parameters.
        update_complementary(): Update angle estimation using complementary filtering.
        update_kalman(): Update angle estimation using Kalman filtering.
        update_roll_pitch(): Update roll and pitch angles.
        get_angles_degrees(): Get angles in degrees.
        get_angles_radians(): Get angles in radians.
    """
    def __init__(self, dt=0.01, gyro_weight=0.98, Q_angle=0.001, Q_bias=0.003, R_measure=0.003):
        """
            初始化互补卡尔曼滤波器。

            Args:
                dt: 采样时间间隔（秒）。
                gyro_weight: 陀螺仪权重（0-1），值越大越相信陀螺仪数据。
                Q_angle: 过程噪声协方差。
                Q_bias: 陀螺仪偏置噪声协方差。
                R_measure: 测量噪声协方差。

            Note:
                - 默认参数适用于大多数应用场景。
                - 可根据实际需求调整滤波参数。

            ==========================================

            Initialize complementary Kalman filter.

            Args:
                dt: Sampling time interval (seconds).
                gyro_weight: Gyroscope weight (0-1), higher values trust gyroscope more.
                Q_angle: Process noise covariance.
                Q_bias: Gyroscope bias noise covariance.
                R_measure: Measurement noise covariance.

            Note:
                - Default parameters are suitable for most applications.
                - Filter parameters can be adjusted according to actual requirements.
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
           使用互补滤波更新角度估计。

           Args:
               accel_angle: 从加速度计计算的角度（弧度）。
               gyro_rate: 陀螺仪角速度（弧度/秒）。

           Returns:
               滤波后的角度（弧度）。

           ==========================================

           Update angle estimation using complementary filtering.

           Args:
               accel_angle: Angle calculated from accelerometer (radians).
               gyro_rate: Gyroscope angular velocity (radians/second).

           Returns:
               Filtered angle (radians).
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
        使用卡尔曼滤波更新角度估计。

        Args:
            accel_angle: 从加速度计计算的角度（弧度）。
            gyro_rate: 陀螺仪角速度（弧度/秒）。

        Returns:
            滤波后的角度（弧度）。

        ==========================================

        Update angle estimation using Kalman filtering.

        Args:
            accel_angle: Angle calculated from accelerometer (radians).
            gyro_rate: Gyroscope angular velocity (radians/second).

        Returns:
            Filtered angle (radians).
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
        更新横滚角和俯仰角。

        Args:
            accel_data: 加速度计数据字典 {'x': , 'y': , 'z': }。
            gyro_data: 陀螺仪数据字典 {'x': , 'y': , 'z': }。

        Returns:
            (roll, pitch) 横滚角和俯仰角（弧度）。

        ==========================================

        Update roll and pitch angles.

        Args:
            accel_data: Accelerometer data dictionary {'x': , 'y': , 'z': }.
            gyro_data: Gyroscope data dictionary {'x': , 'y': , 'z': }.

        Returns:
            (roll, pitch) Roll and pitch angles (radians).
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
        """
        获取横滚角和俯仰角（以度为单位）。

        Returns:
            tuple: 包含横滚角和俯仰角的元组（度）。
                   (roll_angle_deg, pitch_angle_deg)

        Note:
            - 角度范围为-180°到180°。
            - 横滚角（roll）表示绕X轴的旋转。
            - 俯仰角（pitch）表示绕Y轴的旋转。

        ==========================================

        Get roll and pitch angles in degrees.

        Returns:
            tuple: Tuple containing roll and pitch angles in degrees.
                   (roll_angle_deg, pitch_angle_deg)

        Note:
            - Angle range is -180° to 180°.
            - Roll angle represents rotation around X-axis.
            - Pitch angle represents rotation around Y-axis.
        """
        # 公式13: 弧度转角度
        # angle_deg = angle_rad * 180 / π
        return degrees(self.roll), degrees(self.pitch)

    def get_angles_radians(self):
        """
        获取横滚角和俯仰角（以弧度为单位）。

        Returns:
            tuple: 包含横滚角和俯仰角的元组（弧度）。
                   (roll_angle_rad, pitch_angle_rad)

        Note:
            - 角度范围为-π到π。
            - 横滚角（roll）表示绕X轴的旋转。
            - 俯仰角（pitch）表示绕Y轴的旋转。

        ==========================================

        Get roll and pitch angles in radians.

        Returns:
            tuple: Tuple containing roll and pitch angles in radians.
                   (roll_angle_rad, pitch_angle_rad)

        Note:
            - Angle range is -π to π.
            - Roll angle represents rotation around X-axis.
            - Pitch angle represents rotation around Y-axis.
        """
        return self.roll, self.pitch

class MPU6050(object):
    """
    MPU6050六轴运动传感器驱动类。

    该类提供MPU6050传感器的完整驱动功能，支持加速度计、陀螺仪和温度数据的读取，
    以及传感器范围和配置的设置。

    Attributes:
        _GRAVITIY_MS2: 重力加速度常数（m/s²）。
        _ACC_SCLR_2G, _ACC_SCLR_4G, _ACC_SCLR_8G, _ACC_SCLR_16G: 加速度计量程缩放因子。
        _GYR_SCLR_250DEG, _GYR_SCLR_500DEG, _GYR_SCLR_1000DEG, _GYR_SCLR_2000DEG: 陀螺仪量程缩放因子。
        _ACC_RNG_2G, _ACC_RNG_4G, _ACC_RNG_8G, _ACC_RNG_16G: 加速度计量程寄存器值。
        _GYR_RNG_250DEG, _GYR_RNG_500DEG, _GYR_RNG_1000DEG, _GYR_RNG_2000DEG: 陀螺仪量程寄存器值。
        _PWR_MGMT_1, _ACCEL_XOUT0, _TEMP_OUT0, _GYRO_XOUT0, _ACCEL_CONFIG, _GYRO_CONFIG: MPU6050寄存器地址。
        _MPU6050_ADDRESS: 默认I2C地址。
        i2c: I2C通信接口实例。
        addr: I2C设备地址。
        _failCount: I2C通信失败计数。
        _terminatingFailCount: 致命失败计数。

    Methods:
        __init__(): 初始化MPU6050传感器实例。
        _readData(): 从指定寄存器读取数据。
        read_temperature(): 读取温度数据。
        set_accel_range(): 设置加速度计量程。
        get_accel_range(): 获取加速度计量程设置。
        read_accel_data(): 读取加速度计数据。
        read_accel_abs(): 读取加速度绝对值。
        set_gyro_range(): 设置陀螺仪量程。
        get_gyro_range(): 获取陀螺仪量程设置。
        read_gyro_data(): 读取陀螺仪数据。
        read_angle(): 计算角度（基于加速度计）。

    ==========================================

    MPU6050 six-axis motion sensor driver class.

    This class provides complete driver functionality for MPU6050 sensor,
    supporting reading of accelerometer, gyroscope, and temperature data,
    as well as setting sensor ranges and configurations.

    Attributes:
        _GRAVITIY_MS2: Gravity acceleration constant (m/s²).
        _ACC_SCLR_2G, _ACC_SCLR_4G, _ACC_SCLR_8G, _ACC_SCLR_16G: Accelerometer range scaling factors.
        _GYR_SCLR_250DEG, _GYR_SCLR_500DEG, _GYR_SCLR_1000DEG, _GYR_SCLR_2000DEG: Gyroscope range scaling factors.
        _ACC_RNG_2G, _ACC_RNG_4G, _ACC_RNG_8G, _ACC_RNG_16G: Accelerometer range register values.
        _GYR_RNG_250DEG, _GYR_RNG_500DEG, _GYR_RNG_1000DEG, _GYR_RNG_2000DEG: Gyroscope range register values.
        _PWR_MGMT_1, _ACCEL_XOUT0, _TEMP_OUT0, _GYRO_XOUT0, _ACCEL_CONFIG, _GYRO_CONFIG: MPU6050 register addresses.
        _MPU6050_ADDRESS: Default I2C address.
        i2c: I2C communication interface instance.
        addr: I2C device address.
        _failCount: I2C communication failure count.
        _terminatingFailCount: Terminating failure count.

    Methods:
        __init__(): Initialize MPU6050 sensor instance.
        _readData(): Read data from specified register.
        read_temperature(): Read temperature data.
        set_accel_range(): Set accelerometer range.
        get_accel_range(): Get accelerometer range setting.
        read_accel_data(): Read accelerometer data.
        read_accel_abs(): Read absolute acceleration value.
        set_gyro_range(): Set gyroscope range.
        get_gyro_range(): Get gyroscope range setting.
        read_gyro_data(): Read gyroscope data.
        read_angle(): Calculate angles (based on accelerometer).
    """
    _GRAVITIY_MS2 = 9.80665

    _ACC_SCLR_2G = 16384.0
    _ACC_SCLR_4G = 8192.0
    _ACC_SCLR_8G = 4096.0
    _ACC_SCLR_16G = 2048.0

    _GYR_SCLR_250DEG = 131.0
    _GYR_SCLR_500DEG = 65.5
    _GYR_SCLR_1000DEG = 32.8
    _GYR_SCLR_2000DEG = 16.4

    _ACC_RNG_2G = 0x00
    _ACC_RNG_4G = 0x08
    _ACC_RNG_8G = 0x10
    _ACC_RNG_16G = 0x18

    _GYR_RNG_250DEG = 0x00
    _GYR_RNG_500DEG = 0x08
    _GYR_RNG_1000DEG = 0x10
    _GYR_RNG_2000DEG = 0x18

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
        """
        初始化MPU6050传感器实例。

        Args:
            i2c: 已配置好的I2C实例。
            addr: I2C设备地址（默认0x68）。

        Raises:
            Exception: I2C通信失败时抛出异常。

        Note:
            - 初始化时会唤醒MPU6050（从睡眠模式）。
            - 默认I2C地址为0x68。

        ==========================================

        Initialize MPU6050 sensor instance.

        Args:
            i2c: Configured I2C instance.
            addr: I2C device address (default 0x68).

        Raises:
            Exception: Raised when I2C communication fails.

        Note:
            - Initialization wakes up MPU6050 (from sleep mode).
            - Default I2C address is 0x68.
        """
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
        def _readData(self, register):
            """
            从指定寄存器读取6字节数据（3个轴的16位值）。

            Args:
                register: 要读取的起始寄存器地址。

            Returns:
                dict: 包含x、y、z轴原始数据的字典。
                      {'x': x_raw, 'y': y_raw, 'z': z_raw}

            Note:
                - 使用带重试机制的I2C读取。
                - 最大重试次数由_maxFails定义。
                - 如果读取失败超过最大次数，返回NaN值。

            ==========================================

            Read 6-byte data from specified register (3 axes of 16-bit values).

            Args:
                register: Starting register address to read from.

            Returns:
                dict: Dictionary containing raw x, y, z axis data.
                      {'x': x_raw, 'y': y_raw, 'z': z_raw}

            Note:
                - Uses I2C read with retry mechanism.
                - Maximum retry count defined by _maxFails.
                - Returns NaN values if reading fails beyond maximum attempts.
            """
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

    def read_temperature(self):
        """
        读取温度数据。

        Returns:
            温度值（摄氏度）。

        ==========================================

        Read temperature data.

        Returns:
            Temperature value (degrees Celsius).
        """
        try:
            rawData = self.i2c.readfrom_mem(self.addr, MPU6050._TEMP_OUT0, 2)
            raw_temp = (signedIntFromBytes(rawData, "big"))
        except:
            print(i2c_err_str.format(self.addr))
            return float("NaN")
        actual_temp = (raw_temp / 340) + 36.53
        return actual_temp

    def set_accel_range(self, accel_range):
        """
        设置加速度计的量程。

        Args:
            accel_range: 要设置的量程值，使用预定义的常量：
                         _ACC_RNG_2G, _ACC_RNG_4G, _ACC_RNG_8G, _ACC_RNG_16G

        Note:
            - 必须在读取加速度数据之前设置。
            - 无效的量程值会被拒绝。
            - 设置后会影响read_accel_data()的返回值。

        ==========================================

        Set accelerometer measurement range.

        Args:
            accel_range: Range value to set, use predefined constants:
                         _ACC_RNG_2G, _ACC_RNG_4G, _ACC_RNG_8G, _ACC_RNG_16G

        Note:
            - Must be set before reading accelerometer data.
            - Invalid range values will be rejected.
            - Affects return value of read_accel_data() after setting.
        """
        if accel_range not in [MPU6050._ACC_RNG_2G, MPU6050._ACC_RNG_4G, MPU6050._ACC_RNG_8G, MPU6050._ACC_RNG_16G]:
            print("Error: Invalid accelerometer range. Range not set.")
            return
        self.i2c.writeto_mem(self.addr, MPU6050._ACCEL_CONFIG, bytes([accel_range]))
        self._accel_range = accel_range

    def get_accel_range(self, raw=False):
        """
        获取加速度计当前设置的量程。

        Args:
            raw: 是否返回原始寄存器值。
                  True: 返回ACCEL_CONFIG寄存器的原始值。
                  False: 返回整数表示的g值（2, 4, 8, 16）。

        Returns:
            int: 根据raw参数返回相应的值。
                 如果raw=False且量程未知，返回-1。

        Note:
            - 读取ACCEL_CONFIG寄存器的值。
            - 默认返回g值，便于理解和使用。

        ==========================================

        Get current accelerometer measurement range.

        Args:
            raw: Whether to return raw register value.
                  True: Return raw value from ACCEL_CONFIG register.
                  False: Return integer g value (2, 4, 8, 16).

        Returns:
            int: Corresponding value based on raw parameter.
                 Returns -1 if raw=False and range is unknown.

        Note:
            - Reads value from ACCEL_CONFIG register.
            - Returns g value by default for easier understanding and use.
        """
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

    def read_accel_data(self, g=False):
        """
        读取加速度计数据。

        Args:
            g: 是否以g为单位返回数据，False表示以m/s²为单位。

        Returns:
            包含x、y、z轴加速度数据的字典。

        ==========================================

        Read accelerometer data.

        Args:
            g: Whether to return data in g units, False means in m/s².

        Returns:
            Dictionary containing x, y, z axis acceleration data.
        """
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
        """
        计算加速度的合向量大小（绝对值）。

        Args:
            g: 数据单位选择，与read_accel_data()一致。

        Returns:
            float: 三轴加速度的合向量大小。

        Note:
            - 计算公式：√(ax² + ay² + az²)
            - 可用于检测总体加速度大小。
            - 单位由g参数决定。

        ==========================================

        Calculate magnitude of acceleration vector (absolute value).

        Args:
            g: Data unit selection, consistent with read_accel_data().

        Returns:
            float: Magnitude of three-axis acceleration vector.

        Note:
            - Calculation formula: √(ax² + ay² + az²)
            - Can be used to detect overall acceleration magnitude.
            - Unit determined by g parameter.
        """
        d = self.read_accel_data(g)
        return sqrt(d["x"] ** 2 + d["y"] ** 2 + d["z"] ** 2)

    def set_gyro_range(self, gyro_range):
        """
        设置陀螺仪的量程。

        Args:
            gyro_range: 要设置的量程值，使用预定义的常量：
                        _GYR_RNG_250DEG, _GYR_RNG_500DEG,
                        _GYR_RNG_1000DEG, _GYR_RNG_2000DEG

        Note:
            - 必须在读取陀螺仪数据之前设置。
            - 无效的量程值会被拒绝。
            - 设置后会影响read_gyro_data()的返回值。

        ==========================================

        Set gyroscope measurement range.

        Args:
            gyro_range: Range value to set, use predefined constants:
                        _GYR_RNG_250DEG, _GYR_RNG_500DEG,
                        _GYR_RNG_1000DEG, _GYR_RNG_2000DEG

        Note:
            - Must be set before reading gyroscope data.
            - Invalid range values will be rejected.
            - Affects return value of read_gyro_data() after setting.
        """
        if gyro_range not in [MPU6050._GYR_RNG_250DEG, MPU6050._GYR_RNG_500DEG, MPU6050._GYR_RNG_1000DEG, MPU6050._GYR_RNG_2000DEG]:
            print("Error: Invalid gyroscope range. Range not set.")
            return
        self.i2c.writeto_mem(self.addr, MPU6050._GYRO_CONFIG, bytes([gyro_range]))
        self._gyro_range = gyro_range

    def get_gyro_range(self, raw=False):
        """
        获取陀螺仪当前设置的量程。

        Args:
            raw: 是否返回原始寄存器值。
                  True: 返回GYRO_CONFIG寄存器的原始值。
                  False: 返回整数表示的度/秒值（250, 500, 1000, 2000）。

        Returns:
            int: 根据raw参数返回相应的值。
                 如果raw=False且量程未知，返回-1。

        Note:
            - 读取GYRO_CONFIG寄存器的值。
            - 默认返回度/秒值，便于理解和使用。

        ==========================================

        Get current gyroscope measurement range.

        Args:
            raw: Whether to return raw register value.
                  True: Return raw value from GYRO_CONFIG register.
                  False: Return integer deg/s value (250, 500, 1000, 2000).

        Returns:
            int: Corresponding value based on raw parameter.
                 Returns -1 if raw=False and range is unknown.

        Note:
            - Reads value from GYRO_CONFIG register.
            - Returns deg/s value by default for easier understanding and use.
        """
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

    def read_gyro_data(self):
        """
        读取陀螺仪的X、Y、Z轴角速度数据。

        Returns:
            dict: 包含三轴角速度数据的字典（度/秒）。
                  {'x': x_value, 'y': y_value, 'z': z_value}

        Note:
            - 数据会根据当前设置的量程进行缩放。
            - 返回单位为度/秒。
            - 静止时各轴应接近0°/s。

        ==========================================

        Read gyroscope X, Y, Z axis angular velocity data.

        Returns:
            dict: Dictionary containing three-axis angular velocity data (deg/s).
                  {'x': x_value, 'y': y_value, 'z': z_value}

        Note:
            - Data is scaled according to currently set range.
            - Returns units in degrees per second.
            - Should be close to 0°/s on each axis when stationary.
        """
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

    def read_angle(self):
        """
        基于加速度计数据计算横滚角和俯仰角。

        Returns:
            dict: 包含横滚角和俯仰角的字典（弧度）。
                  {'x': pitch_angle, 'y': roll_angle}

        Note:
            - x: 俯仰角（pitch，绕Y轴旋转）。
            - y: 横滚角（roll，绕X轴旋转）。
            - 仅使用加速度计数据，未融合陀螺仪。
            - 静态时精度较高，动态时受加速度影响。
            - 角度范围为-π到π。

        ==========================================

        Calculate roll and pitch angles based on accelerometer data.

        Returns:
            dict: Dictionary containing roll and pitch angles in radians.
                  {'x': pitch_angle, 'y': roll_angle}

        Note:
            - x: Pitch angle (rotation around Y-axis).
            - y: Roll angle (rotation around X-axis).
            - Uses only accelerometer data, no gyroscope fusion.
            - High accuracy when static, affected by acceleration when dynamic.
            - Angle range is -π to π.
        """
        a = self.read_accel_data()
        x = atan2(a["y"], a["z"])
        y = atan2(-a["x"], a["z"])
        return {"x": x, "y": y}

    # ======================================== 初始化配置 ==========================================

    # ========================================  主程序  ============================================
