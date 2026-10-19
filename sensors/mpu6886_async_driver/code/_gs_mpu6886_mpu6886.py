# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 12:00
# @Author  : Mika Tuupola
# @File    : mpu6886.py
# @Description : MPU6886 6-axis motion tracking device driver (I2C)
# @License : MIT

"""
MicroPython I2C driver for MPU6886 6-axis motion tracking device
"""

__version__ = "1.0.0"
__author__ = "Mika Tuupola"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import ustruct
import utime
import time
from machine import I2C, Pin
from micropython import const

# ======================================== 全局变量 ============================================
# 寄存器地址常量
_CONFIG = const(0x1A)
_GYRO_CONFIG = const(0x1B)
_ACCEL_CONFIG = const(0x1C)
_ACCEL_CONFIG2 = const(0x1D)
_ACCEL_XOUT_H = const(0x3B)
_ACCEL_XOUT_L = const(0x3C)
_ACCEL_YOUT_H = const(0x3D)
_ACCEL_YOUT_L = const(0x3E)
_ACCEL_ZOUT_H = const(0x3F)
_ACCEL_ZOUT_L = const(0x40)
_TEMP_OUT_H = const(0x41)
_TEMP_OUT_L = const(0x42)
_GYRO_XOUT_H = const(0x43)
_GYRO_XOUT_L = const(0x44)
_GYRO_YOUT_H = const(0x45)
_GYRO_YOUT_L = const(0x46)
_GYRO_ZOUT_H = const(0x47)
_GYRO_ZOUT_L = const(0x48)
_PWR_MGMT_1 = const(0x6B)
_WHO_AM_I = const(0x75)

# 加速度计满量程范围选择位
ACCEL_FS_SEL_2G = const(0b00000000)
ACCEL_FS_SEL_4G = const(0b00001000)
ACCEL_FS_SEL_8G = const(0b00010000)
ACCEL_FS_SEL_16G = const(0b00011000)

# 加速度计灵敏度分频系数（LSB/g）
# 1 / 16384，即 0.061 mg/LSB
_ACCEL_SO_2G = 16384
# 1 / 8192，即 0.122 mg/LSB
_ACCEL_SO_4G = 8192
# 1 / 4096，即 0.244 mg/LSB
_ACCEL_SO_8G = 4096
# 1 / 2048，即 0.488 mg/LSB
_ACCEL_SO_16G = 2048

# 陀螺仪满量程范围选择位
GYRO_FS_SEL_250DPS = const(0b00000000)
GYRO_FS_SEL_500DPS = const(0b00001000)
GYRO_FS_SEL_1000DPS = const(0b00010000)
GYRO_FS_SEL_2000DPS = const(0b00011000)

# 陀螺仪灵敏度分频系数（LSB/度/秒）
_GYRO_SO_250DPS = 131
_GYRO_SO_500DPS = 62.5
_GYRO_SO_1000DPS = 32.8
_GYRO_SO_2000DPS = 16.4

# 温度传感器转换系数
_TEMP_SO = 326.8
_TEMP_OFFSET = 25

# 加速度/陀螺仪换算尺度因子
SF_G = 1
# 1 g = 9.80665 m/s^2（标准重力加速度）
SF_M_S2 = 9.80665
SF_DEG_S = 1
# 1 deg/s = 0.017453292519943 rad/s
SF_RAD_S = 0.017453292519943


# ======================================== 功能函数 ============================================
# 无通用功能函数，所有函数封装在类中


# ======================================== 自定义类 ============================================
class MPU6886:
    """
    MPU6886 6轴运动跟踪传感器驱动类
    通过 I2C 接口读取加速度、角速度、温度数据
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _accel_so (float): 加速度计灵敏度分频系数
        _gyro_so (float): 陀螺仪灵敏度分频系数
        _accel_sf (float): 加速度换算尺度因子
        _gyro_sf (float): 陀螺仪换算尺度因子
        _gyro_offset (tuple): 陀螺仪零偏校准值
        _debug (bool): 调试日志开关
    Methods:
        calibrate(): 校准陀螺仪零偏
        acceleration: 读取加速度值 (property)
        gyro: 读取角速度值 (property)
        temperature: 读取温度值 (property)
        whoami: 读取芯片 ID (property)
        deinit(): 释放资源
    Notes:
        - I2C 总线必须由外部注入，不在类内创建
        - 支持上下文管理器（with 语句）
        - ISR-safe: 否（所有方法均涉及 I2C 通信）
    ==========================================
    MPU6886 6-axis motion tracking device driver.
    Reads acceleration, gyroscope, and temperature via I2C interface.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _accel_so (float): Accelerometer sensitivity divider
        _gyro_so (float): Gyroscope sensitivity divider
        _accel_sf (float): Accelerometer scale factor
        _gyro_sf (float): Gyroscope scale factor
        _gyro_offset (tuple): Gyroscope zero offset calibration
        _debug (bool): Debug logging flag
    Methods:
        calibrate(): Calibrate gyroscope zero offset
        acceleration: Read acceleration values (property)
        gyro: Read gyroscope values (property)
        temperature: Read temperature value (property)
        whoami: Read chip ID (property)
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C bus instance
        - Supports context manager (with statement)
        - ISR-safe: No (all methods involve I2C communication)
    """

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = const(0x68)

    def __init__(
        self,
        i2c,
        address=I2C_DEFAULT_ADDR,
        accel_fs=ACCEL_FS_SEL_2G,
        gyro_fs=GYRO_FS_SEL_250DPS,
        accel_sf=SF_M_S2,
        gyro_sf=SF_RAD_S,
        gyro_offset=(0, 0, 0),
        debug=False,
    ):
        """
        初始化 MPU6886 传感器驱动
        Args:
            i2c (I2C): I2C 总线实例（必须外部注入）
            address (int): 设备 I2C 地址，默认 0x68
            accel_fs (int): 加速度计满量程范围，默认 ACCEL_FS_SEL_2G
            gyro_fs (int): 陀螺仪满量程范围，默认 GYRO_FS_SEL_250DPS
            accel_sf (float): 加速度换算因子，默认 SF_M_S2（m/s^2）
            gyro_sf (float): 陀螺仪换算因子，默认 SF_RAD_S（rad/s）
            gyro_offset (tuple): 陀螺仪零偏校准值 (x, y, z)，默认 (0, 0, 0)
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型不正确
            RuntimeError: 设备未在 I2C 总线上找到
        Notes:
            - 初始化时执行芯片复位和时钟自动选择
            - ISR-safe: 否
        ==========================================
        Initialize MPU6886 sensor driver.
        Args:
            i2c (I2C): I2C bus instance (must be externally provided)
            address (int): Device I2C address, default 0x68
            accel_fs (int): Accelerometer full-scale range, default ACCEL_FS_SEL_2G
            gyro_fs (int): Gyroscope full-scale range, default GYRO_FS_SEL_250DPS
            accel_sf (float): Accelerometer scale factor, default SF_M_S2 (m/s^2)
            gyro_sf (float): Gyroscope scale factor, default SF_RAD_S (rad/s)
            gyro_offset (tuple): Gyroscope zero offset (x, y, z), default (0, 0, 0)
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Device not found on I2C bus
        Notes:
            - Performs chip reset and auto clock selection during init
            - ISR-safe: No
        """
        # 参数校验：i2c 为空
        if i2c is None:
            raise ValueError("i2c must not be None")
        # 参数校验：i2c 类型检查（鸭子类型）
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 类型和范围检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be 0x08-0x77, got 0x%02X" % address)
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 检查芯片 ID，确认设备存在
        chip_id = self.whoami
        if chip_id != 0x19:
            raise RuntimeError("MPU6886 not found at I2C address 0x%02X, device ID: 0x%02X" % (address, chip_id))

        # 芯片复位
        self._register_char(_PWR_MGMT_1, 0b10000000)
        # Async facade preserves the required 100 ms reset settling interval.
        # 时钟自动选择
        self._register_char(_PWR_MGMT_1, 0b00000001)

        # 设置量程并获取对应灵敏度系数
        self._accel_so = self._accel_fs(accel_fs)
        self._gyro_so = self._gyro_fs(gyro_fs)
        self._accel_sf = accel_sf
        self._gyro_sf = gyro_sf
        self._gyro_offset = gyro_offset

    # ========== 调试日志 ==========

    def _log(self, msg):
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 debug=True 时输出，ISR-safe: 否
        ==========================================
        Output debug log message.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when debug=True, ISR-safe: No
        """
        if self._debug:
            print("[MPU6886] %s" % msg)

    # ========== 公共方法 ==========

    def calibrate(self, count=256, delay=0):
        """
        校准陀螺仪零偏
        在静止状态下采集多次陀螺仪读数并计算平均值作为零偏
        Args:
            count (int): 采样次数，默认 256
            delay (int): 每次采样间隔（毫秒），默认 0
        Returns:
            tuple: 校准后的零偏值 (x_offset, y_offset, z_offset)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 校准时设备必须保持静止
            - 副作用：修改 self._gyro_offset
            - ISR-safe: 否
        ==========================================
        Calibrate gyroscope zero offset.
        Collects multiple gyro readings while stationary and averages them.
        Args:
            count (int): Number of samples, default 256
            delay (int): Delay between samples in ms, default 0
        Returns:
            tuple: Calibrated zero offset (x_offset, y_offset, z_offset)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Device must remain stationary during calibration
            - Side effects: Modifies self._gyro_offset
            - ISR-safe: No
        """
        # 参数校验
        if not isinstance(count, int):
            raise ValueError("count must be int, got %s" % type(count))
        if not isinstance(delay, int):
            raise ValueError("delay must be int, got %s" % type(delay))
        if count < 1:
            raise ValueError("count must be >= 1, got %d" % count)

        ox, oy, oz = (0.0, 0.0, 0.0)
        # 暂时清零偏移量，以获得原始读数
        self._gyro_offset = (0.0, 0.0, 0.0)
        n = float(count)

        # 采集 count 次读数并累加
        while count:
            utime.sleep_ms(delay)
            gx, gy, gz = self.gyro
            ox += gx
            oy += gy
            oz += gz
            count -= 1

        # 计算平均值作为零偏
        self._gyro_offset = (ox / n, oy / n, oz / n)
        self._log("Calibration complete, offset: (%f, %f, %f)" % self._gyro_offset)
        return self._gyro_offset

    # ========== 属性访问器 ==========

    @property
    def acceleration(self):
        """
        读取加速度计测量值
        默认返回 m/s^2 单位的三轴加速度值，若构造时传入 accel_sf=SF_G 则返回 g 单位
        Returns:
            tuple: (x, y, z) 三轴加速度值 (float)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read accelerometer measurements.
        By default returns acceleration in m/s^2. Use accel_sf=SF_G for g units.
        Returns:
            tuple: (x, y, z) 3-axis acceleration values (float)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        so = self._accel_so
        sf = self._accel_sf

        # 从寄存器读取 3 个 16 位有符号整数（大端序）
        xyz = self._register_three_shorts(_ACCEL_XOUT_H)
        # 转换为物理单位
        return tuple([value / so * sf for value in xyz])

    @property
    def gyro(self):
        """
        读取陀螺仪测量值
        默认返回 rad/s 单位的三轴角速度值，若构造时传入 gyro_sf=SF_DEG_S 则返回 deg/s 单位
        Returns:
            tuple: (x, y, z) 三轴角速度值 (float)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 返回值已减去校准零偏
            - ISR-safe: 否
        ==========================================
        Read gyroscope measurements.
        By default returns angular velocity in rad/s. Use gyro_sf=SF_DEG_S for deg/s.
        Returns:
            tuple: (x, y, z) 3-axis angular velocity (float)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Values are corrected for calibrated zero offset
            - ISR-safe: No
        """
        so = self._gyro_so
        sf = self._gyro_sf
        ox, oy, oz = self._gyro_offset

        # 从寄存器读取 3 个 16 位有符号整数（大端序）
        xyz = self._register_three_shorts(_GYRO_XOUT_H)
        # 转换为物理单位
        xyz = [value / so * sf for value in xyz]

        # 减去零偏校准值
        xyz[0] -= ox
        xyz[1] -= oy
        xyz[2] -= oz

        return tuple(xyz)

    @property
    def temperature(self):
        """
        读取芯片温度
        Returns:
            float: 芯片温度（摄氏度）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 此温度为芯片内部温度，非环境温度
            - ISR-safe: 否
        ==========================================
        Read chip die temperature.
        Returns:
            float: Die temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - This is internal chip temperature, not ambient
            - ISR-safe: No
        """
        # 读取温度寄存器原始值
        temp = self._register_short(_TEMP_OUT_H)
        # 转换为摄氏度
        return (temp / _TEMP_SO) + _TEMP_OFFSET

    @property
    def whoami(self):
        """
        读取芯片 ID 寄存器
        Returns:
            int: WHO_AM_I 寄存器值（应为 0x19）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 可用于验证设备是否连接正确
            - ISR-safe: 否
        ==========================================
        Read chip ID register.
        Returns:
            int: WHO_AM_I register value (expected 0x19)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Can be used to verify device connection
            - ISR-safe: No
        """
        return self._register_char(_WHO_AM_I)

    # ========== 上下文管理器 ==========

    def __enter__(self):
        """
        进入上下文管理器
        Returns:
            MPU6886: 当前实例
        ==========================================
        Enter context manager.
        Returns:
            MPU6886: Current instance
        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """
        退出上下文管理器
        Args:
            exception_type: 异常类型
            exception_value: 异常值
            traceback: 异常回溯
        Returns:
            None
        Notes:
            - 当前实现无特殊清理操作
        ==========================================
        Exit context manager.
        Args:
            exception_type: Exception type
            exception_value: Exception value
            traceback: Exception traceback
        Returns:
            None
        Notes:
            - No special cleanup in current implementation
        """
        pass

    # ========== 私有方法 ==========

    def _register_short(self, register, value=None, buf=bytearray(2)):
        """
        读写 16 位寄存器（大端序）
        Args:
            register (int): 寄存器地址
            value (int): 写入值（None 表示读取）
            buf (bytearray): 复用缓冲区
        Returns:
            int 或 None: 读取时返回 16 位有符号整数，写入时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：读取/写入 I2C 设备寄存器
        ==========================================
        Read or write a 16-bit register (big-endian).
        Args:
            register (int): Register address
            value (int): Value to write (None for read)
            buf (bytearray): Reusable buffer
        Returns:
            int or None: 16-bit signed value on read, None on write
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effects: Reads/writes I2C device registers
        """
        # 读取模式
        if value is None:
            try:
                self._i2c.readfrom_mem_into(self._address, register, buf)
            except OSError as e:
                raise RuntimeError("I2C read failed at register 0x%02X" % register) from e
            return ustruct.unpack(">h", buf)[0]

        # 写入模式
        ustruct.pack_into(">h", buf, 0, value)
        try:
            return self._i2c.writeto_mem(self._address, register, buf)
        except OSError as e:
            raise RuntimeError("I2C write failed at register 0x%02X" % register) from e

    def _register_three_shorts(self, register, buf=bytearray(6)):
        """
        连续读取 3 个 16 位寄存器（大端序）
        用于一次性读取三轴传感器数据（X、Y、Z）
        Args:
            register (int): 起始寄存器地址
            buf (bytearray): 复用缓冲区（6 字节）
        Returns:
            tuple: (x, y, z) 三个 16 位有符号整数
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：从 I2C 设备连续读取 6 字节数据
        ==========================================
        Read 3 consecutive 16-bit registers (big-endian).
        Used for reading 3-axis sensor data at once.
        Args:
            register (int): Start register address
            buf (bytearray): Reusable buffer (6 bytes)
        Returns:
            tuple: (x, y, z) three 16-bit signed integers
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effects: Reads 6 bytes from I2C device
        """
        try:
            self._i2c.readfrom_mem_into(self._address, register, buf)
        except OSError as e:
            raise RuntimeError("I2C read failed at register 0x%02X (3 shorts)" % register) from e
        return ustruct.unpack(">hhh", buf)

    def _register_char(self, register, value=None, buf=bytearray(1)):
        """
        读写 8 位寄存器（小端序）
        Args:
            register (int): 寄存器地址
            value (int): 写入值（None 表示读取）
            buf (bytearray): 复用缓冲区
        Returns:
            int 或 None: 读取时返回 8 位无符号整数，写入时返回 None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：读取/写入 I2C 设备寄存器
        ==========================================
        Read or write an 8-bit register (little-endian).
        Args:
            register (int): Register address
            value (int): Value to write (None for read)
            buf (bytearray): Reusable buffer
        Returns:
            int or None: 8-bit unsigned value on read, None on write
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effects: Reads/writes I2C device registers
        """
        # 读取模式
        if value is None:
            try:
                self._i2c.readfrom_mem_into(self._address, register, buf)
            except OSError as e:
                raise RuntimeError("I2C read failed at register 0x%02X" % register) from e
            return buf[0]

        # 写入模式
        ustruct.pack_into("<b", buf, 0, value)
        try:
            return self._i2c.writeto_mem(self._address, register, buf)
        except OSError as e:
            raise RuntimeError("I2C write failed at register 0x%02X" % register) from e

    def _accel_fs(self, value):
        """
        设置加速度计满量程范围并返回对应灵敏度系数
        Args:
            value (int): 量程选择值（ACCEL_FS_SEL_2G/4G/8G/16G）
        Returns:
            float: 对应的灵敏度分频系数
        Notes:
            - 副作用：写入 ACCEL_CONFIG 寄存器
        ==========================================
        Set accelerometer full-scale range and return sensitivity divider.
        Args:
            value (int): Full-scale selection (ACCEL_FS_SEL_2G/4G/8G/16G)
        Returns:
            float: Corresponding sensitivity divider
        Notes:
            - Side effects: Writes ACCEL_CONFIG register
        """
        self._register_char(_ACCEL_CONFIG, value)

        # 返回对应灵敏度系数
        if ACCEL_FS_SEL_2G == value:
            return _ACCEL_SO_2G
        elif ACCEL_FS_SEL_4G == value:
            return _ACCEL_SO_4G
        elif ACCEL_FS_SEL_8G == value:
            return _ACCEL_SO_8G
        elif ACCEL_FS_SEL_16G == value:
            return _ACCEL_SO_16G

    def _gyro_fs(self, value):
        """
        设置陀螺仪满量程范围并返回对应灵敏度系数
        Args:
            value (int): 量程选择值（GYRO_FS_SEL_250DPS/500DPS/1000DPS/2000DPS）
        Returns:
            float: 对应的灵敏度分频系数
        Notes:
            - 副作用：写入 GYRO_CONFIG 寄存器
        ==========================================
        Set gyroscope full-scale range and return sensitivity divider.
        Args:
            value (int): Full-scale selection (GYRO_FS_SEL_250DPS/500DPS/1000DPS/2000DPS)
        Returns:
            float: Corresponding sensitivity divider
        Notes:
            - Side effects: Writes GYRO_CONFIG register
        """
        self._register_char(_GYRO_CONFIG, value)

        # 返回对应灵敏度系数
        if GYRO_FS_SEL_250DPS == value:
            return _GYRO_SO_250DPS
        elif GYRO_FS_SEL_500DPS == value:
            return _GYRO_SO_500DPS
        elif GYRO_FS_SEL_1000DPS == value:
            return _GYRO_SO_1000DPS
        elif GYRO_FS_SEL_2000DPS == value:
            return _GYRO_SO_2000DPS

    # ========== 资源释放 ==========

    def deinit(self):
        """
        释放硬件资源
        将设备置于睡眠模式以降低功耗
        Returns:
            None
        Notes:
            - 副作用：写入 PWR_MGMT_1 寄存器使设备睡眠
            - 可多次调用而不产生错误
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Puts device into sleep mode to reduce power consumption.
        Returns:
            None
        Notes:
            - Side effects: Writes PWR_MGMT_1 register to sleep mode
            - Safe to call multiple times
            - ISR-safe: No
        """
        try:
            # 将设备置于睡眠模式
            self._register_char(_PWR_MGMT_1, 0b01000000)
            self._log("MPU6886 deinitialized (sleep mode)")
        except Exception:
            # 静默处理释放错误，避免二次异常
            pass


# ======================================== 初始化配置 ==========================================
# 驱动文件不在此区域实例化硬件

# ========================================  主程序  ===========================================
# 驱动文件不在此区域运行主程序
