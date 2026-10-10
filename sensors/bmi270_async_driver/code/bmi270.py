# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : bmi270.py
# @Description : Bosch BMI270 6-axis IMU (加速度计+陀螺仪) 驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from micropython import const
from i2c_helpers import CBits, RegisterStruct
from config_file import bmi270_config_file

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================
__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# WHO_AM_I 寄存器地址
_REG_WHOAMI = const(0x00)
# 错误代码寄存器地址
_ERROR_CODE = const(0x02)
# 命令寄存器地址
_COMMAND = const(0x7E)
# 加速度量程寄存器地址
_ACC_RANGE = const(0x41)
# 电源控制寄存器地址
_PWR_CTRL = const(0x7D)
# 陀螺仪量程寄存器地址
_GYRO_RANGE = const(0x43)

# 标准重力加速度 (m/s^2)
_STANDARD_GRAVITY = const(9.80665)

# 加速度数据寄存器地址
# 加速度 X 轴低字节
ACC_X_LSB = const(0x0C)
# 加速度 Y 轴低字节
ACC_Y_LSB = const(0x0E)
# 加速度 Z 轴低字节
ACC_Z_LSB = const(0x10)

# 陀螺仪数据寄存器地址
# 陀螺仪 X 轴低字节
GYRO_X_LSB = const(0x12)
# 陀螺仪 Y 轴低字节
GYRO_Y_LSB = const(0x14)
# 陀螺仪 Z 轴低字节
GYRO_Z_LSB = const(0x16)

# 加速度量程选项
# 加速度量程: ±2g
ACCEL_RANGE_2G = const(0b00)
# 加速度量程: ±4g
ACCEL_RANGE_4G = const(0b01)
# 加速度量程: ±8g
ACCEL_RANGE_8G = const(0b10)
# 加速度量程: ±16g
ACCEL_RANGE_16G = const(0b11)
acceleration_range_values = (
    ACCEL_RANGE_2G,
    ACCEL_RANGE_4G,
    ACCEL_RANGE_8G,
    ACCEL_RANGE_16G,
)

# 加速度计禁用
ACCELERATOR_DISABLED = const(0b0)
# 加速度计启用
ACCELERATOR_ENABLED = const(0b1)
acceleration_operation_mode_values = (ACCELERATOR_DISABLED, ACCELERATOR_ENABLED)

# 陀螺仪量程选项
# 陀螺仪量程: ±2000 dps
GYRO_RANGE_2000 = const(0b000)
# 陀螺仪量程: ±1000 dps
GYRO_RANGE_1000 = const(0b001)
# 陀螺仪量程: ±500 dps
GYRO_RANGE_500 = const(0b010)
# 陀螺仪量程: ±250 dps
GYRO_RANGE_250 = const(0b011)
# 陀螺仪量程: ±125 dps
GYRO_RANGE_125 = const(0b100)
gyro_range_values = (
    GYRO_RANGE_2000,
    GYRO_RANGE_1000,
    GYRO_RANGE_500,
    GYRO_RANGE_250,
    GYRO_RANGE_125,
)

# 软复位命令
RESET_COMMAND = const(0xB6)

# 电源配置寄存器地址
_PWR_CONF = const(0x7C)
# 初始化控制寄存器地址
_INIT_CTRL = const(0x59)
# 初始化地址0寄存器地址
_INIT_ADDR_0 = const(0x5B)
# 初始化地址1寄存器地址
_INIT_ADDR_1 = const(0x5C)
# 初始化数据寄存器地址
_INIT_DATA = const(0x5E)

# WHO_AM_I 期望值
_BMI270_CHIP_ID = const(0x24)

# ======================================== 功能函数 ============================================
# 无独立功能函数，所有操作封装在类中


# ======================================== 自定义类 ============================================
class BMI270:
    """
    BMI270 6轴惯性测量单元驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        acceleration: 获取三轴加速度值 (m/s^2)
        gyro: 获取三轴陀螺仪值 (dps)
        acceleration_range: 获取/设置加速度量程
        gyro_range: 获取/设置陀螺仪量程
        acceleration_operation_mode: 获取/设置加速度计工作模式
        error_code(): 读取错误代码寄存器
        soft_reset(): 执行软复位
        load_config_file(): 加载配置文件
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 配置文件 config_file.py 包含传感器初始化所需的二进制数据
        - 初始化时自动加载配置文件并设置默认参数
    ==========================================
    BMI270 6-axis IMU driver class.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        acceleration: Get 3-axis acceleration values (m/s^2)
        gyro: Get 3-axis gyroscope values (dps)
        acceleration_range: Get/set acceleration range
        gyro_range: Get/set gyroscope range
        acceleration_operation_mode: Get/set accelerometer operating mode
        error_code(): Read error code register
        soft_reset(): Perform soft reset
        load_config_file(): Load configuration file
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - config_file.py contains binary data required for sensor initialization
        - Automatically loads config file and sets default parameters on init
    """

    # 类级常量
    # WHO_AM_I 设备ID寄存器
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    # 错误代码寄存器
    _error_code = RegisterStruct(_ERROR_CODE, "B")
    # 软复位寄存器
    _soft_reset = RegisterStruct(_COMMAND, "B")
    # 命令寄存器读取
    _read = RegisterStruct(_COMMAND, "B")

    # 电源控制寄存器
    power_control = RegisterStruct(_PWR_CTRL, "B")
    # 电源配置寄存器
    power_config = RegisterStruct(0x7C, "B")

    # 加速度原始数据寄存器
    _acc_data_x = RegisterStruct(ACC_X_LSB, "<h")
    _acc_data_y = RegisterStruct(ACC_Y_LSB, "<h")
    _acc_data_z = RegisterStruct(ACC_Z_LSB, "<h")

    # 陀螺仪原始数据寄存器
    _gyro_data_x = RegisterStruct(GYRO_X_LSB, "<h")
    _gyro_data_y = RegisterStruct(GYRO_Y_LSB, "<h")
    _gyro_data_z = RegisterStruct(GYRO_Z_LSB, "<h")

    # 陀螺仪量程寄存器 (0x43)
    _gyro_range = CBits(3, _GYRO_RANGE, 0)
    # 陀螺仪灵敏度比例因子 (mdeg/LSB)
    gyro_scale = (16.4, 32.8, 65.6, 131.2, 262.4)

    # 加速度量程寄存器 (0x41)
    # 该寄存器用于选择加速度计量程
    _acceleration_range = CBits(2, _ACC_RANGE, 0)
    # 加速度灵敏度比例因子 (LSB/g)
    acceleration_scale = (16384, 8192, 4096, 2048)

    # 加速度计工作模式位
    _acceleration_operation_mode = CBits(1, _PWR_CTRL, 2)

    # 电源配置寄存器
    _power_configuration = RegisterStruct(_PWR_CONF, "B")

    # 内部状态寄存器
    internal_status = RegisterStruct(0x21, "B")

    # 初始化控制寄存器
    _init_control = RegisterStruct(_INIT_CTRL, "B")

    # 初始化地址寄存器
    _init_address_0 = RegisterStruct(_INIT_ADDR_0, "B")
    _init_address_1 = RegisterStruct(_INIT_ADDR_1, "B")
    # 初始化数据寄存器 (16 个 16-bit 值)
    _init_data = RegisterStruct(_INIT_DATA, ">HHHHHHHHHHHHHHHH")

    def __init__(self, i2c, address: int = 0x68, debug: bool = False) -> None:
        """
        初始化 BMI270 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): I2C 设备地址，默认 0x68
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型错误
            RuntimeError: 设备未找到或 I2C 通信失败
        Notes:
            - 初始化时自动加载配置文件和设置默认参数
            - ISR-safe: 否
        ==========================================
        Initialize BMI270 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x68
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Device not found or I2C communication failed
        Notes:
            - Automatically loads config file and sets defaults on init
            - ISR-safe: No
        """
        # 参数校验：检查 i2c 参数类型
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：检查 address 参数类型和值范围
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got 0x%02X" % address)
        # 参数校验：检查 debug 参数类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 缓存变量初始化（在 setter 中更新）
        self._acceleration_factor_cached = 0
        self._gyro_factor_cached = 0

        # 读取设备 ID 验证设备存在
        try:
            chip_id = self._device_id
        except OSError as e:
            raise RuntimeError("Failed to communicate with BMI270 at 0x%02X" % address) from e
        if chip_id != _BMI270_CHIP_ID:
            raise RuntimeError("Failed to find BMI270: expected 0x%02X, got 0x%02X" % (_BMI270_CHIP_ID, chip_id))

        # 配置文件上传和两段 100 ms 上电等待由 BMI270Async.initialize_async()
        # 协作执行；构造函数不在事件循环中执行单体长循环。
        self._initialized = False

    def error_code(self) -> None:
        """
        读取错误代码寄存器
        该寄存器用于调试目的，不应用于常规操作完成验证。
        Fatal Error 表示启动期间的错误，读取寄存器后该标志不会被清除，
        只能通过上电复位清除。
        Notes:
            - ISR-safe: 否
        ==========================================
        Read error code register.
        This register is for debug purposes, not for regular verification
        if an operation completed successfully.
        Fatal Error indicates error during bootup. This flag will not be
        cleared after reading. Only POR can clear it.
        Notes:
            - ISR-safe: No
        """
        # 读取错误代码寄存器
        errors = self._error_code
        # 解析 I2C 主控制器错误
        i2c_err = (errors & 0x80) >> 7
        # 解析 FIFO 错误
        fifo_err = (errors & 0x40) >> 6
        # 解析内部错误码
        internal_error = (errors & 0x1E) >> 1
        # 解析致命错误标志
        fatal_error = errors & 0x01
        if i2c_err:
            self._log("Error in I2C-Master detected. This flag will be reset when read.")
        if fifo_err:
            self._log(
                "Error when a frame is read in streaming mode (so skipping is not "
                "possible) and fifo is overfilled (with virtual and/or regular frames). "
                "This flag will be reset when read."
            )
        if internal_error != 0:
            self._log("Internal Sensor Error")
        if fatal_error:
            self._log("Fatal Error. This flag will be reset when read")

    def soft_reset(self) -> None:
        """
        执行软复位
        Notes:
            - 复位后需要等待 15ms
            - ISR-safe: 否
        ==========================================
        Perform a soft reset.
        Notes:
            - Requires 15ms wait after reset
            - ISR-safe: No
        """
        # 写入复位命令到命令寄存器
        self._soft_reset = RESET_COMMAND
        # 等待复位完成
        time.sleep(0.015)

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        获取三轴加速度值
        Returns:
            Tuple[float, float, float]: (x, y, z) 三轴加速度，单位 m/s^2
        Notes:
            - ISR-safe: 否
            - 依赖 _acceleration_factor_cached 缓存值（由 acceleration_range setter 设置）
        ==========================================
        Get 3-axis acceleration values.
        Returns:
            Tuple[float, float, float]: (x, y, z) acceleration in m/s^2
        Notes:
            - ISR-safe: No
            - Depends on _acceleration_factor_cached cached by acceleration_range setter
        """
        # 读取原始数据并转换为 m/s^2
        x = self._acc_data_x / self._acceleration_factor_cached * _STANDARD_GRAVITY
        y = self._acc_data_y / self._acceleration_factor_cached * _STANDARD_GRAVITY
        z = self._acc_data_z / self._acceleration_factor_cached * _STANDARD_GRAVITY
        return x, y, z

    @property
    def acceleration_range(self) -> str:
        """
        获取当前加速度量程
        Returns:
            str: 量程名称字符串
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current acceleration range.
        Returns:
            str: Range name string
        Notes:
            - ISR-safe: No
        """
        # 量程名称映射表
        values = (
            "ACCEL_RANGE_2G",
            "ACCEL_RANGE_4G",
            "ACCEL_RANGE_8G",
            "ACCEL_RANGE_16G",
        )
        return values[self._acceleration_range]

    @acceleration_range.setter
    def acceleration_range(self, value: int) -> None:
        if value not in acceleration_range_values:
            raise ValueError("Value must be a valid acceleration_range setting")
        # 写入加速度量程寄存器
        self._acceleration_range = value
        # 更新缓存的灵敏度因子
        self._acceleration_factor_cached = self.acceleration_scale[value]

    @property
    def acceleration_operation_mode(self) -> str:
        """
        获取加速度计工作模式
        Returns:
            str: 工作模式名称字符串
        Notes:
            - ISR-safe: 否
        ==========================================
        Get accelerometer operation mode.
        Returns:
            str: Operation mode name string
        Notes:
            - ISR-safe: No
        """
        # 模式名称映射表
        values = ("ACCELERATOR_DISABLED", "ACCELERATOR_ENABLED")
        return values[self._acceleration_operation_mode]

    @acceleration_operation_mode.setter
    def acceleration_operation_mode(self, value: int) -> None:
        if value not in acceleration_operation_mode_values:
            raise ValueError("Value must be a valid acceleration_operation_mode setting")
        # 写入加速度计工作模式
        self._acceleration_operation_mode = value

    def load_config_file(self) -> None:
        """
        加载配置文件
        配置文件包含传感器正常工作所需的初始化数据。
        该方法改编自 CoRoLab-Berlin/bmi270_python (MIT License)。
        Notes:
            - 首次上电后必须调用该方法
            - 重复调用时若已初始化则跳过
            - ISR-safe: 否
        ==========================================
        Load configuration file.
        The config file contains initialization data required for
        the sensor to function properly.
        Adapted from CoRoLab-Berlin/bmi270_python (MIT License).
        Notes:
            - Must be called after first power-up
            - Skips if already initialized on repeated calls
            - ISR-safe: No
        """
        # 检查是否已完成初始化
        if self.internal_status == 0x01:
            self._log("0x%02X --> Initialization already done" % self._address)
        else:
            self._log("0x%02X --> Initializing..." % self._address)
            # 禁用高级省电模式
            self._power_configuration = 0x00
            time.sleep(0.00045)
            # 清除初始化控制位
            self._init_control = 0x00
            # 分块写入配置文件数据 (256个块，每块32字节)
            for i in range(256):
                self._init_address_0 = 0x00
                self._init_address_1 = i
                time.sleep(0.03)
                try:
                    self._i2c.writeto_mem(
                        self._address,
                        0x5E,
                        bytes(bmi270_config_file[i * 32 : (i + 1) * 32]),
                    )
                except OSError as e:
                    raise RuntimeError("Failed to write config file at block %d" % i) from e
                time.sleep(0.000020)
            # 设置初始化完成标志
            self._init_control = 0x01
            time.sleep(0.02)
            self._log("0x%02X --> Initialization status: %s (00000001 --> OK)" % (self._address, "{:08b}".format(self.internal_status)))

    @property
    def gyro_range(self) -> str:
        """
        获取当前陀螺仪量程
        Returns:
            str: 量程名称字符串
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current gyroscope range.
        Returns:
            str: Range name string
        Notes:
            - ISR-safe: No
        """
        # 量程名称映射表
        values = (
            "GYRO_RANGE_2000",
            "GYRO_RANGE_1000",
            "GYRO_RANGE_500",
            "GYRO_RANGE_250",
            "GYRO_RANGE_125",
        )
        return values[self._gyro_range]

    @gyro_range.setter
    def gyro_range(self, value: int) -> None:
        if value not in gyro_range_values:
            raise ValueError("Value must be a valid gyro_range setting")
        # 写入陀螺仪量程寄存器
        self._gyro_range = value
        # 更新缓存的灵敏度因子
        self._gyro_factor_cached = self.gyro_scale[value]

    @property
    def gyro(self) -> Tuple[float, float, float]:
        """
        获取三轴陀螺仪值
        Returns:
            Tuple[float, float, float]: (x, y, z) 三轴角速度，单位 dps
        Notes:
            - ISR-safe: 否
            - 依赖 _gyro_factor_cached 缓存值（由 gyro_range setter 设置）
        ==========================================
        Get 3-axis gyroscope values.
        Returns:
            Tuple[float, float, float]: (x, y, z) angular velocity in dps
        Notes:
            - ISR-safe: No
            - Depends on _gyro_factor_cached cached by gyro_range setter
        """
        # 读取原始数据并转换为 dps
        x = self._gyro_data_x / self._gyro_factor_cached
        y = self._gyro_data_y / self._gyro_factor_cached
        z = self._gyro_data_z / self._gyro_factor_cached
        return x, y, z

    async def initialize_async(self) -> None:
        """Cooperatively upload the required configuration and power up the IMU."""
        if self.internal_status != 0x01:
            self._power_configuration = 0x00
            await asyncio.sleep_ms(1)
            self._init_control = 0x00
            for block in range(256):
                self._init_address_0 = 0x00
                self._init_address_1 = block
                await asyncio.sleep_ms(30)
                start = block * 32
                try:
                    self._i2c.writeto_mem(self._address, 0x5E, bytes(bmi270_config_file[start:start + 32]))
                except OSError as exc:
                    raise RuntimeError("Failed to write config file at block %d" % block) from exc
                await asyncio.sleep_ms(1)
            self._init_control = 0x01
            await asyncio.sleep_ms(20)
        self.power_control = 0x0E
        await asyncio.sleep_ms(100)
        self.power_config = 0x00
        await asyncio.sleep_ms(100)
        self.acceleration_range = ACCEL_RANGE_2G
        self.gyro_range = GYRO_RANGE_250
        self._initialized = True

    async def error_code_async(self) -> None:
        self.error_code()

    async def aclose(self) -> None:
        self.deinit()
        self._initialized = False
    def deinit(self) -> None:
        """
        释放传感器资源
        将加速度计设为禁用模式以降低功耗。
        Notes:
            - ISR-safe: 否
            - 调用后传感器停止采样
        ==========================================
        Release sensor resources.
        Sets accelerometer to disabled mode to reduce power consumption.
        Notes:
            - ISR-safe: No
            - Sensor stops sampling after call
        """
        try:
            self._acceleration_operation_mode = ACCELERATOR_DISABLED
        except OSError:
            pass

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug=True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
        """
        if self._debug:
            print("[BMI270] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
