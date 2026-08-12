# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 15:36
# @Author  : mimingxuan
# @File    : sht35.py
# @Description : SHT35 高精度 I²C 温湿度传感器驱动文件
# @License : MIT

__version__ = "1.0.0"
__author__ = "mimingxuan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import sleep_ms

try:
    from micropython import const
except ImportError:

    def const(x: object) -> object:
        return x


# ======================================== 全局变量 ============================================

SHT35_DEFAULT_ADDR = const(0x44)

REPEATABILITY_HIGH = const(0)
REPEATABILITY_MEDIUM = const(1)
REPEATABILITY_LOW = const(2)

CMD_SOFT_RESET = b"\x30\xa2"
CMD_READ_STATUS = b"\xf3\x2d"
CMD_CLEAR_STATUS = b"\x30\x41"
CMD_HEATER_ENABLE = b"\x30\x6d"
CMD_HEATER_DISABLE = b"\x30\x66"

# 复用 I2C 读取缓冲区，减少内存分配
_BUF6 = bytearray(6)
_BUF3 = bytearray(3)

# ======================================== 功能函数 ===========================================


def _sht35_crc8(data: bytes) -> int:
    """
    计算 SHT35 CRC-8 校验值（多项式 0x31）
    Args:
        data (bytes): 待校验数据
    Returns:
        int: CRC-8 校验值
    ==========================================
    Calculate SHT35 CRC-8 checksum (polynomial 0x31).
    Args:
        data (bytes): Data to verify
    Returns:
        int: CRC-8 checksum value
    """
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def _sht35_check_crc(data: bytes, checksum: int) -> bool:
    """
    校验 SHT35 CRC-8
    Args:
        data (bytes): 待校验数据
        checksum (int): 期望的校验值
    Returns:
        bool: 校验是否通过
    ==========================================
    Verify SHT35 CRC-8 checksum.
    Args:
        data (bytes): Data to verify
        checksum (int): Expected checksum
    Returns:
        bool: True if checksum matches
    """
    return _sht35_crc8(data) == checksum


# ======================================== 自定义类 ============================================


class SHT35:
    """
    Sensirion SHT35 高精度 I²C 温湿度传感器驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        reset(): 软复位传感器
        read_status(): 读取状态寄存器
        clear_status(): 清除状态寄存器
        heater(): 控制内部加热器
        read_raw(): 读取原始温湿度计数值
        measure(): 测量温湿度
        temperature(): 单独读取温度
        humidity(): 单独读取湿度
        get_temp_humi(): 兼容接口，同 measure()
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在类内部创建
        - CRC 校验方法已抽离为模块级函数
        - 所有公共方法非 ISR-safe
    ==========================================
    Sensirion SHT35 high-precision I2C temperature and humidity sensor driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log flag
    Methods:
        reset(): Soft-reset the sensor
        read_status(): Read status register
        clear_status(): Clear status register
        heater(): Control internal heater
        read_raw(): Read raw temperature and humidity ticks
        measure(): Measure temperature and humidity
        temperature(): Read temperature only
        humidity(): Read humidity only
        get_temp_humi(): Compatibility wrapper, same as measure()
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - CRC functions extracted to module level
        - All public methods are not ISR-safe
    """

    # 类级常量
    _MEASURE_COMMANDS = {
        True: {
            REPEATABILITY_HIGH: b"\x2c\x06",
            REPEATABILITY_MEDIUM: b"\x2c\x0d",
            REPEATABILITY_LOW: b"\x2c\x10",
        },
        False: {
            REPEATABILITY_HIGH: b"\x24\x00",
            REPEATABILITY_MEDIUM: b"\x24\x0b",
            REPEATABILITY_LOW: b"\x24\x16",
        },
    }

    _MEASURE_DELAYS_MS = {
        REPEATABILITY_HIGH: 16,
        REPEATABILITY_MEDIUM: 7,
        REPEATABILITY_LOW: 5,
    }

    def __init__(self, i2c: object, addr: int = SHT35_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 SHT35 传感器

        Args:
            i2c (I2C): I2C 总线实例（必须支持 writeto/readfrom 方法）
            addr (int): 设备 I2C 地址，默认 0x44
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: i2c 参数无效或地址超出范围
        Notes:
            - 不在类内部创建 I2C 实例
            - ISR-safe: 否
        ==========================================
        Initialize SHT35 sensor.

        Args:
            i2c (I2C): I2C bus instance (must support writeto/readfrom methods)
            addr (int): Device I2C address, defaults to 0x44
            debug (bool): Enable debug logging, defaults to False
        Raises:
            ValueError: Invalid i2c parameter or address out of range
        Notes:
            - I2C instance is not created internally
            - ISR-safe: No
        """
        # 参数校验：None 检查
        if i2c is None:
            raise ValueError("i2c must not be None")
        # 参数校验：鸭子类型检查，确保支持所需 I2C 方法
        if hasattr(i2c, "writeto") is False or hasattr(i2c, "readfrom") is False:
            raise ValueError("i2c must be an I2C instance with writeto/readfrom")
        # 参数校验：地址类型和范围检查
        if isinstance(addr, int) is False:
            raise ValueError("addr must be int, got %s" % type(addr))
        if addr < 0 or addr > 127:
            raise ValueError("addr must be 0~127, got %d" % addr)

        self._i2c = i2c
        self._addr = addr
        self._debug = debug

    def _log(self, msg: str) -> None:
        """输出调试日志（仅 debug=True 时生效）"""
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[SHT35] %s" % msg)

    def _write_command(self, command: bytes) -> None:
        """
        向传感器发送命令

        Args:
            command (bytes): 命令字节序列
        Raises:
            RuntimeError: I2C 写入失败
        ==========================================
        Send command to sensor.

        Args:
            command (bytes): Command byte sequence
        Raises:
            RuntimeError: I2C write failed
        """
        if isinstance(command, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("command must be a buffer or sequence")
        try:
            self._i2c.writeto(self._addr, command)
        except OSError as e:
            raise RuntimeError("I2C write command failed") from e

    def _read(self, count: int) -> bytearray:
        """
        从传感器读取指定字节数

        Args:
            count (int): 要读取的字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: I2C 读取失败
        ==========================================
        Read specified number of bytes from sensor.

        Args:
            count (int): Number of bytes to read
        Returns:
            bytearray: Data read from sensor
        Raises:
            RuntimeError: I2C read failed
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("count must be a positive integer")
        try:
            return self._i2c.readfrom(self._addr, count)
        except OSError as e:
            raise RuntimeError("I2C read failed") from e

    # ==================== 公共方法 ====================

    def reset(self) -> None:
        """
        软复位传感器

        Notes:
            - 复位后需等待 2ms 再发送后续命令
            - ISR-safe: 否
        ==========================================
        Soft-reset the sensor.

        Notes:
            - Wait 2ms after reset before sending further commands
            - ISR-safe: No
        """
        self._log("soft reset")
        self._write_command(CMD_SOFT_RESET)
        sleep_ms(2)

    def read_status(self, check_crc: bool = True) -> int:
        """
        读取传感器 16 位状态寄存器

        Args:
            check_crc (bool): 是否校验 CRC，默认 True
        Returns:
            int: 状态寄存器值
        Raises:
            RuntimeError: CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read the 16-bit status register.

        Args:
            check_crc (bool): Whether to verify CRC, default True
        Returns:
            int: Status register value
        Raises:
            RuntimeError: CRC check failed
        Notes:
            - ISR-safe: No
        """
        self._log("reading status")
        self._write_command(CMD_READ_STATUS)
        # 读取 3 字节：2 字节数据 + 1 字节 CRC
        data = self._read(3)
        # CRC 校验
        if check_crc and not _sht35_check_crc(data[0:2], data[2]):
            raise RuntimeError("SHT35 status CRC check failed")
        # 合并为 16 位状态值
        return (data[0] << 8) | data[1]

    def clear_status(self) -> None:
        """
        清除状态寄存器

        Notes:
            - 副作用：清除传感器状态寄存器
            - ISR-safe: 否
        ==========================================
        Clear the status register.

        Notes:
            - Side effect: Clears sensor status register
            - ISR-safe: No
        """
        self._log("clearing status")
        self._write_command(CMD_CLEAR_STATUS)

    def heater(self, enable: bool) -> None:
        """
        控制内部加热器开关

        Args:
            enable (bool): True 开启加热，False 关闭加热
        Notes:
            - 副作用：修改传感器加热器状态
            - ISR-safe: 否
        ==========================================
        Enable or disable the internal heater.

        Args:
            enable (bool): True to enable, False to disable
        Notes:
            - Side effect: Modifies sensor heater state
            - ISR-safe: No
        """
        if isinstance(enable, bool) is False:
            raise ValueError("enable must be bool")
        self._log("heater %s" % ("ON" if enable else "OFF"))
        self._write_command(CMD_HEATER_ENABLE if enable else CMD_HEATER_DISABLE)

    def read_raw(self, repeatability: int = REPEATABILITY_HIGH, clock_stretch: bool = False, check_crc: bool = True) -> tuple:
        """
        读取原始温湿度计数值

        Args:
            repeatability (int): 重复性等级，可选 REPEATABILITY_HIGH/MEDIUM/LOW
            clock_stretch (bool): 是否启用时钟拉伸，默认 False
            check_crc (bool): 是否校验 CRC，默认 True
        Returns:
            tuple: (temperature_ticks, humidity_ticks) 原始计数值
        Raises:
            ValueError: repeatability 参数无效
            RuntimeError: CRC 校验失败
        Notes:
            - 阻塞方法，根据重复性等级等待 5~16ms
            - ISR-safe: 否
        ==========================================
        Read raw temperature and humidity ticks.

        Args:
            repeatability (int): Repeatability level, REPEATABILITY_HIGH/MEDIUM/LOW
            clock_stretch (bool): Enable clock stretching, default False
            check_crc (bool): Verify CRC, default True
        Returns:
            tuple: (temperature_ticks, humidity_ticks) raw values
        Raises:
            ValueError: Invalid repeatability
            RuntimeError: CRC check failed
        Notes:
            - Blocking, waits 5~16ms depending on repeatability
            - ISR-safe: No
        """
        # 参数校验：重复性等级
        if repeatability not in self._MEASURE_COMMANDS[clock_stretch]:
            raise ValueError("invalid repeatability: %d" % repeatability)

        # 发送测量命令
        self._write_command(self._MEASURE_COMMANDS[clock_stretch][repeatability])
        # 等待测量完成，延时取决于重复性等级
        sleep_ms(self._MEASURE_DELAYS_MS[repeatability])

        # 读取 6 字节：[温度高, 温度低, CRC, 湿度高, 湿度低, CRC]
        data = self._read(6)
        # 拆分温度数据（前 2 字节）和湿度数据（第 4-5 字节）
        temp_data = data[0:2]
        humi_data = data[3:5]

        # CRC 校验
        if check_crc:
            if not _sht35_check_crc(temp_data, data[2]):
                raise RuntimeError("SHT35 temperature CRC check failed")
            if not _sht35_check_crc(humi_data, data[5]):
                raise RuntimeError("SHT35 humidity CRC check failed")

        # 大端合并为 16 位计数值
        temperature_ticks = (data[0] << 8) | data[1]
        humidity_ticks = (data[3] << 8) | data[4]
        return temperature_ticks, humidity_ticks

    def measure(self, repeatability: int = REPEATABILITY_HIGH, clock_stretch: bool = False, celsius: bool = True, check_crc: bool = True) -> tuple:
        """
        测量温度和相对湿度

        Args:
            repeatability (int): 重复性等级，默认 REPEATABILITY_HIGH
            clock_stretch (bool): 是否启用时钟拉伸，默认 False
            celsius (bool): True 返回摄氏度，False 返回华氏度
            check_crc (bool): 是否校验 CRC，默认 True
        Returns:
            tuple: (temperature, humidity) 温度值和相对湿度值
        Notes:
            - 阻塞方法
            - ISR-safe: 否
        ==========================================
        Measure temperature and relative humidity.

        Args:
            repeatability (int): Repeatability level, default REPEATABILITY_HIGH
            clock_stretch (bool): Enable clock stretching, default False
            celsius (bool): True for Celsius, False for Fahrenheit
            check_crc (bool): Verify CRC, default True
        Returns:
            tuple: (temperature, humidity) temperature and relative humidity
        Notes:
            - Blocking method
            - ISR-safe: No
        """
        if isinstance(repeatability, int) is False:
            raise ValueError("repeatability must be int")
        if isinstance(clock_stretch, bool) is False:
            raise ValueError("clock_stretch must be bool")
        if isinstance(celsius, bool) is False:
            raise ValueError("celsius must be bool")
        if isinstance(check_crc, bool) is False:
            raise ValueError("check_crc must be bool")
        # 获取原始计数值
        temperature_ticks, humidity_ticks = self.read_raw(
            repeatability=repeatability,
            clock_stretch=clock_stretch,
            check_crc=check_crc,
        )

        # 温度转换公式（数据手册公式）
        if celsius:
            temperature = -45 + (175 * temperature_ticks / 65535)
        else:
            temperature = -49 + (315 * temperature_ticks / 65535)

        # 湿度转换公式（数据手册公式）
        humidity = 100 * humidity_ticks / 65535
        return temperature, humidity

    def temperature(self, celsius: bool = True) -> float:
        """
        单独读取温度值

        Args:
            celsius (bool): True 返回摄氏度，False 返回华氏度
        Returns:
            float: 温度值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read temperature only.

        Args:
            celsius (bool): True for Celsius, False for Fahrenheit
        Returns:
            float: Temperature value
        Notes:
            - ISR-safe: No
        """
        if isinstance(celsius, bool) is False:
            raise ValueError("celsius must be bool")
        return self.measure(celsius=celsius)[0]

    def humidity(self) -> float:
        """
        单独读取相对湿度值

        Returns:
            float: 相对湿度值（%RH）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read relative humidity only.

        Returns:
            float: Relative humidity (%RH)
        Notes:
            - ISR-safe: No
        """
        return self.measure()[1]

    def get_temp_humi(self, resolution: int = REPEATABILITY_HIGH, clock_stretch: bool = False, celsius: bool = True) -> tuple:
        """
        兼容辅助方法，与 SHT31 示例风格保持一致

        Args:
            resolution (int): 分辨率/重复性等级
            clock_stretch (bool): 是否启用时钟拉伸
            celsius (bool): True 摄氏度，False 华氏度
        Returns:
            tuple: (temperature, humidity)
        Notes:
            - 功能等同于 measure() 方法
            - ISR-safe: 否
        ==========================================
        Compatibility helper matching the SHT31 example style.

        Args:
            resolution (int): Resolution / repeatability level
            clock_stretch (bool): Enable clock stretching
            celsius (bool): True for Celsius, False for Fahrenheit
        Returns:
            tuple: (temperature, humidity)
        Notes:
            - Functionally equivalent to measure()
            - ISR-safe: No
        """
        if isinstance(resolution, int) is False:
            raise ValueError("resolution must be int")
        if isinstance(clock_stretch, bool) is False:
            raise ValueError("clock_stretch must be bool")
        if isinstance(celsius, bool) is False:
            raise ValueError("celsius must be bool")
        return self.measure(
            repeatability=resolution,
            clock_stretch=clock_stretch,
            celsius=celsius,
        )

    def deinit(self) -> None:
        """
        释放传感器资源

        Notes:
            - 清除 I2C 总线引用
            - ISR-safe: 否
        ==========================================
        Release sensor resources.

        Notes:
            - Clears I2C bus reference
            - ISR-safe: No
        """
        self._log("deinit")
        self._i2c = None
        self._addr = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
