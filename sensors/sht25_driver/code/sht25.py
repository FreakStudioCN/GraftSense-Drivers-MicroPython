# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:10
# @Author  : Miceuz
# @File    : sht25.py
# @Description : SHT25 温湿度传感器驱动文件
# @License : MIT

__version__ = "1.0.0"
__author__ = "Miceuz"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython

from time import sleep_ms

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _celsius_to_fahrenheit(celsius):
    """摄氏温度转华氏温度。"""
    return celsius * 9.0 / 5.0 + 32.0


def _clamp_rh(value):
    """相对湿度值钳位至 [0.0, 100.0] 范围。"""
    if value < 0.0:
        return 0.0
    if value > 100.0:
        return 100.0
    return value


# ======================================== 自定义类 ============================================


class SHT25:
    """
    SHT25 温湿度传感器驱动类。
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        temperature_c(): 读取摄氏温度
        temperature_f(): 读取华氏温度
        humidity(): 读取相对湿度
        read_user_register(): 读取用户寄存器
        write_user_register(value): 写入用户寄存器
        reset(): 软复位传感器
        getTemperature(): 兼容旧接口，读取摄氏温度
        getHumidity(): 兼容旧接口，读取相对湿度
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 复位后需等待 15ms 方可通信
    ==========================================
    MicroPython driver for the Sensirion SHT25 temperature and humidity sensor.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        temperature_c(): Read temperature in Celsius
        temperature_f(): Read temperature in Fahrenheit
        humidity(): Read relative humidity
        read_user_register(): Read user register
        write_user_register(value): Write user register
        reset(): Soft reset the sensor
        getTemperature(): Compatibility alias for temperature_c()
        getHumidity(): Compatibility alias for humidity()
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - 15ms wait required after reset before communication
    """

    DEFAULT_ADDR = micropython.const(0x40)

    CMD_TRIGGER_TEMP_NO_HOLD = micropython.const(0xF3)
    CMD_TRIGGER_HUMIDITY_NO_HOLD = micropython.const(0xF5)
    CMD_READ_USER_REGISTER = micropython.const(0xE7)
    CMD_WRITE_USER_REGISTER = micropython.const(0xE6)
    CMD_SOFT_RESET = micropython.const(0xFE)

    def __init__(self, i2c, address: int = DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 SHT25 传感器驱动。
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x40
            debug (bool): 调试日志开关，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 参数无效
        Notes:
            - 不在内部创建 I2C 总线
        ==========================================
        Initialize SHT25 sensor driver.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x40
            debug (bool): Debug log switch, default False
        Returns:
            None
        Raises:
            ValueError: Invalid i2c parameter
        Notes:
            - I2C bus is not created internally
        """
        # 参数校验：i2c 对象不能为 None
        if i2c is None:
            raise ValueError("i2c object is required")
        # 参数校验：i2c 必须具有 writeto 方法（鸭子类型检查）
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：地址值范围检查
        if not isinstance(address, int) or address < 0 or address > 0x7F:
            raise ValueError("address must be a valid 7-bit I2C address")
        # 参数校验：debug 类型检查
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = address
        self._debug = debug

    # ---------- 公共方法 ----------

    def temperature_c(self):
        """
        读取摄氏温度。
        Args:
            无
        Returns:
            float: 摄氏温度值（℃）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 测量耗时约 90ms
        ==========================================
        Read temperature in Celsius.
        Args:
            None
        Returns:
            float: Temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Measurement takes ~90ms
        """
        # 发送无保持测量命令并读取原始数据
        raw = self._read_measurement(self.CMD_TRIGGER_TEMP_NO_HOLD, 90)
        # 根据 SHT25 数据手册公式转换为摄氏温度
        return -46.85 + 175.72 * raw / 65536.0

    def temperature_f(self):
        """
        读取华氏温度。
        Args:
            无
        Returns:
            float: 华氏温度值（℉）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 内部调用 temperature_c() 并转换单位
        ==========================================
        Read temperature in Fahrenheit.
        Args:
            None
        Returns:
            float: Temperature in Fahrenheit
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Internally calls temperature_c() and converts
        """
        # 调用模块级温度转换函数
        return _celsius_to_fahrenheit(self.temperature_c())

    def humidity(self):
        """
        读取相对湿度。
        Args:
            无
        Returns:
            float: 相对湿度值（%RH），范围 [0.0, 100.0]
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 测量耗时约 30ms
            - 返回值自动钳位到 [0, 100] 范围
        ==========================================
        Read relative humidity.
        Args:
            None
        Returns:
            float: Relative humidity (%RH), range [0.0, 100.0]
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Measurement takes ~30ms
            - Return value clamped to [0, 100] range
        """
        # 发送无保持测量命令并读取原始数据
        raw = self._read_measurement(self.CMD_TRIGGER_HUMIDITY_NO_HOLD, 30)
        # 根据 SHT25 数据手册公式转换为相对湿度
        rh = -6.0 + 125.0 * raw / 65536.0
        # 钳位至物理有效范围
        return _clamp_rh(rh)

    def read_user_register(self):
        """
        读取用户寄存器。
        Args:
            无
        Returns:
            int: 用户寄存器值（8 位）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read user register.
        Args:
            None
        Returns:
            int: User register value (8-bit)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        # 发送读寄存器命令
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_READ_USER_REGISTER,)))
            # 读取 1 字节寄存器值
            return self._i2c.readfrom(self._addr, 1)[0]
        except OSError as e:
            raise RuntimeError("I2C read user register failed") from e

    def write_user_register(self, value):
        """
        写入用户寄存器。
        Args:
            value (int): 待写入的 8 位值
        Returns:
            None
        Raises:
            ValueError: value 参数无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 直接修改传感器配置，需谨慎使用
        ==========================================
        Write user register.
        Args:
            value (int): 8-bit value to write
        Returns:
            None
        Raises:
            ValueError: Invalid value parameter
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Directly modifies sensor configuration, use with care
        """
        # 参数校验：value 必须是 int 且在 0-255 范围内
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if value < 0 or value > 0xFF:
            raise ValueError("value must be 0~255, got %d" % value)
        # 发送写寄存器命令
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_WRITE_USER_REGISTER, value & 0xFF)))
        except OSError as e:
            raise RuntimeError("I2C write user register failed") from e

    def reset(self):
        """
        软复位传感器。
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 复位后需等待 15ms 方可进行后续通信
        ==========================================
        Soft reset the sensor.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - 15ms wait required before subsequent communication
        """
        # 发送软复位命令
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_SOFT_RESET,)))
        except OSError as e:
            raise RuntimeError("I2C soft reset failed") from e
        # 等待传感器复位完成
        sleep_ms(15)

    # ---------- 兼容旧接口 ----------

    def getTemperature(self):
        """
        兼容旧接口，读取摄氏温度。
        ==========================================
        Compatibility alias for temperature_c().
        """
        return self.temperature_c()

    def getHumidity(self):
        """
        兼容旧接口，读取相对湿度。
        ==========================================
        Compatibility alias for humidity().
        """
        return self.humidity()

    # ---------- 资源释放 ----------

    def deinit(self):
        """
        释放传感器资源。
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 释放 I2C 总线引用，软复位传感器
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Releases I2C bus reference, soft resets sensor
        """
        # 释放前执行软复位
        try:
            self._i2c.writeto(self._addr, bytes((self.CMD_SOFT_RESET,)))
        except OSError:
            pass
        sleep_ms(15)
        # 清除实例引用
        self._i2c = None
        self._addr = None

    # ---------- 私有方法 ----------

    def _read_measurement(self, command, delay_ms):
        """
        发送无保持测量命令并读取原始数据。
        Args:
            command (int): 测量命令字节
            delay_ms (int): 等待延时（毫秒）
        Returns:
            int: 16 位原始测量值（低 2 位已清零）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 阻塞等待测量完成
        ==========================================
        Send no-hold measurement command and read raw data.
        Args:
            command (int): Measurement command byte
            delay_ms (int): Wait delay in milliseconds
        Returns:
            int: 16-bit raw measurement (lower 2 bits cleared)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Blocks until measurement completes
        """
        if isinstance(command, int) is False:
            raise ValueError("command must be int")

        if command < 0 or command > 0xFF:
            raise ValueError("command must be 0~255")
        if isinstance(delay_ms, int) is False:
            raise ValueError("delay_ms must be int")
        # 发送测量命令（不保持主机模式）
        try:
            self._i2c.writeto(self._addr, bytes((command,)))
        except OSError as e:
            raise RuntimeError("I2C write command 0x%02X failed" % command) from e
        # 等待测量完成
        sleep_ms(delay_ms)
        # 读取 3 字节：高字节+低字节+校验和（校验和未验证，如需启用请参考数据手册 CRC 校验）
        try:
            data = self._i2c.readfrom(self._addr, 3)
        except OSError as e:
            raise RuntimeError("I2C read measurement failed") from e
        # 合并高/低字节，清除状态位（低 2 位）
        return ((data[0] << 8) | data[1]) & 0xFFFC

    # ---------- 调试日志 ----------

    def _log(self, msg):
        """
        调试日志输出。
        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 _debug=True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[SHT25] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
