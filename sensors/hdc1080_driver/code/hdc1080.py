# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Mike Causer
# @File    : hdc1080.py
# @Description : HDC1080 温湿度传感器驱动
# @License : MIT

__version__ = "1.0.1"
__author__ = "Mike Causer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from machine import I2C
from time import sleep_ms

# ======================================== 全局变量 ============================================

# 寄存器地址
_REG_TEMPERATURE = const(0x00)
_REG_HUMIDITY = const(0x01)
_REG_CONFIG = const(0x02)
_REG_SERIAL_ID0 = const(0xFB)
_REG_SERIAL_ID1 = const(0xFC)
_REG_SERIAL_ID2 = const(0xFD)
_REG_MANUFACTURER_ID = const(0xFE)
_REG_DEVICE_ID = const(0xFF)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class HDC1080:
    """
    HDC1080 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _config (int): 当前配置寄存器值
        _debug (bool): 调试日志开关
        _buf1 (bytearray): 1 字节复用缓冲区
        _buf2 (bytearray): 2 字节复用缓冲区
    Methods:
        check(): 检查设备是否存在
        config(): 配置传感器参数
        reset(): 软件复位传感器
        battery_status(): 读取电池状态
        temperature(): 读取温度值
        humidity(): 读取湿度值
        serial_number(): 读取唯一序列号
        manufacturer_id(): 读取制造商 ID
        device_id(): 读取设备 ID
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - I2C 固定地址 0x40
        - ISR-safe: 否
        - 支持 with 语句上下文管理
    ==========================================
    HDC1080 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _config (int): Current configuration register value
        _debug (bool): Debug log switch
        _buf1 (bytearray): 1-byte reusable buffer
        _buf2 (bytearray): 2-byte reusable buffer
    Methods:
        check(): Check if device is present
        config(): Configure sensor parameters
        reset(): Software reset the sensor
        battery_status(): Read battery status
        temperature(): Read temperature value
        humidity(): Read humidity value
        serial_number(): Read unique serial number
        manufacturer_id(): Read manufacturer ID
        device_id(): Read device ID
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Fixed I2C address 0x40
        - ISR-safe: No
        - Supports with-statement context management
    """

    # 类级常量
    I2C_DEFAULT_ADDR = const(0x40)

    def __init__(self, i2c: I2C, addr: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 HDC1080 传感器
        Args:
            i2c (I2C): I2C 总线实例
            addr (int): 设备 I2C 地址，默认 0x40
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: 参数类型错误
        Notes:
            - 初始化时加热器默认关闭（bit 4=0）
            - ISR-safe: 否
        ==========================================
        Initialize HDC1080 sensor.
        Args:
            i2c (I2C): I2C bus instance
            addr (int): Device I2C address, default 0x40
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
        Notes:
            - Heater is off by default (bit 4=0)
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(addr, int) or not 0 <= addr <= 0x7F:
            raise ValueError("addr must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        # 参数校验：I2C 实例必须具备 writeto 方法
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：地址必须为整数
        if isinstance(addr, int) is False:
            raise ValueError("addr must be int, got %s" % type(addr))
        # 参数校验：debug 必须为布尔值
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = addr
        self._debug = debug
        # 默认配置：14 位温湿度分辨率，单独采集模式
        self._config = 0x10
        # 复用 I/O 缓冲区
        self._buf1 = bytearray(1)
        self._buf2 = bytearray(2)

    def __enter__(self):
        """
        上下文管理器入口
        Returns:
            HDC1080: 当前实例
        ==========================================
        Context manager entry.
        Returns:
            HDC1080: This instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        上下文管理器出口，自动释放资源
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        Returns:
            bool: False 表示不抑制异常
        ==========================================
        Context manager exit, auto-release resources.
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        Returns:
            bool: False to not suppress exceptions
        """
        if exc_type is not None and not hasattr(exc_type, "__name__"):
            raise ValueError("exc_type must be an exception type or None")
        self.deinit()
        return False

    def check(self) -> bool:
        """
        检查设备是否存在于 I2C 总线上
        Returns:
            bool: 设备存在返回 True
        Raises:
            OSError: 设备未找到
        Notes:
            - ISR-safe: 否
            - 副作用: 执行 I2C 总线扫描
        ==========================================
        Check if device is present on I2C bus.
        Returns:
            bool: True if device found
        Raises:
            OSError: Device not found
        Notes:
            - ISR-safe: No
            - Side effects: Performs I2C bus scan
        """
        if self._i2c.scan().count(self._addr) == 0:
            raise OSError("HDC1080 not found at I2C address 0x%02X" % self._addr)
        return True

    def config(
        self,
        config: int = None,
        humid_res: int = None,
        temp_res: int = None,
        mode: int = None,
        heater: int = None,
    ) -> None:
        """
        配置传感器参数
        支持直接写入配置值或单独设置各项参数，可同时设置多个参数
        Args:
            config (int): 直接写入的配置寄存器值，为 None 则读取当前配置后修改
            humid_res (int): 湿度分辨率，可选 8/11/14 位
            temp_res (int): 温度分辨率，可选 11/14 位
            mode (int): 采集模式，0=单独采集温度或湿度，1=顺序采集温度和湿度
            heater (int): 加热器开关，0=关闭，1=开启
        Returns:
            None
        Raises:
            ValueError: 分辨率参数值无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 写入配置寄存器，影响后续测量行为
        ==========================================
        Configure sensor parameters.
        Supports direct config value or individual parameter settings.
        Args:
            config (int): Direct config register value, None to read then modify
            humid_res (int): Humidity resolution, 8/11/14 bits
            temp_res (int): Temperature resolution, 11/14 bits
            mode (int): Acquisition mode, 0=single, 1=sequential
            heater (int): Heater switch, 0=off, 1=on
        Returns:
            None
        Raises:
            ValueError: Invalid resolution value
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes config register, affects subsequent measurements
        """
        if isinstance(config, int) is False:
            raise ValueError("config must be int")
        if isinstance(humid_res, int) is False:
            raise ValueError("humid_res must be int")
        if isinstance(temp_res, int) is False:
            raise ValueError("temp_res must be int")
        if isinstance(mode, int) is False:
            raise ValueError("mode must be int")
        if isinstance(heater, bool) is False:
            raise ValueError("heater must be bool")
        if config is not None:
            self._config = config
            self._write_config()
        else:
            self._read_config()
            if humid_res is not None:
                # 湿度分辨率: 00=14位, 01=11位, 10=8位
                if humid_res == 8:
                    self._config |= 2
                    self._config &= ~1
                elif humid_res == 11:
                    self._config &= ~2
                    self._config |= 1
                elif humid_res == 14:
                    self._config &= ~3
                else:
                    raise ValueError("humid_res must be 8, 11 or 14")
            if temp_res is not None:
                # 温度分辨率: 0=14位, 1=11位
                if temp_res == 11:
                    self._config |= 4
                elif temp_res == 14:
                    self._config &= ~4
                else:
                    raise ValueError("temp_res must be 11 or 14")
            if mode is not None:
                # 采集模式: bit 4, 0=单独采集, 1=顺序采集（先温度后湿度）
                self._config &= ~16
                self._config |= (mode & 1) << 4
            if heater is not None:
                # 加热器: bit 5, 0=关闭, 1=开启
                self._config &= ~32
                self._config |= (heater & 1) << 5
            self._write_config()

    def reset(self) -> None:
        """
        软件复位传感器
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 复位后配置恢复默认值，软件复位位自动清除
        ==========================================
        Software reset the sensor.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Configuration resets to default, SW reset bit self-clears
        """
        # 写入复位命令（bit 7=1）
        self._config = 128
        self._write_config()
        # 软件复位位自动清除，读回确认复位完成
        self._read_config()

    def battery_status(self) -> int:
        """
        读取电池电压状态
        Returns:
            int: 0 表示 Vcc > 2.8V，1 表示 Vcc < 2.8V
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 无（仅读取状态寄存器）
        ==========================================
        Read battery voltage status.
        Returns:
            int: 0 if Vcc > 2.8V, 1 if Vcc < 2.8V
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: None (read-only)
        """
        self._read_config()
        # 电池状态位于 bit 3
        return (self._config >> 3) & 1

    def temperature(self) -> float:
        """
        读取温度值
        Returns:
            float: 温度值（摄氏度）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 触发温度测量
        ==========================================
        Read temperature value.
        Returns:
            float: Temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Triggers temperature measurement
        """
        # 公式: T = (raw / 2^16) * 165 - 40
        return (self._read16(_REG_TEMPERATURE) / 65536) * 165 - 40

    def humidity(self) -> float:
        """
        读取湿度值
        Returns:
            float: 相对湿度百分比（%RH）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 触发湿度测量
        ==========================================
        Read humidity value.
        Returns:
            float: Relative humidity percentage (%RH)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Triggers humidity measurement
        """
        # 公式: RH = (raw / 2^16) * 100
        return (self._read16(_REG_HUMIDITY) / 65536) * 100

    def serial_number(self) -> int:
        """
        读取设备唯一序列号
        Returns:
            int: 40 位唯一序列号
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 无（仅读取）
        ==========================================
        Read unique serial number.
        Returns:
            int: 40-bit unique serial number
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: None (read-only)
        """
        # 从 3 个 ID 寄存器组合为 40 位序列号
        return (self._read16(_REG_SERIAL_ID0) << 24) | (self._read16(_REG_SERIAL_ID1) << 8) | (self._read16(_REG_SERIAL_ID2) >> 8)

    def manufacturer_id(self) -> int:
        """
        读取制造商 ID
        Returns:
            int: 制造商 ID（固定值 21577 = 0x5449 = 'TI'）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 无（仅读取）
        ==========================================
        Read manufacturer ID.
        Returns:
            int: Manufacturer ID (fixed 21577 = 0x5449 = 'TI')
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: None (read-only)
        """
        return self._read16(_REG_MANUFACTURER_ID)

    def device_id(self) -> int:
        """
        读取设备 ID
        Returns:
            int: 设备 ID（固定值 4176 = 0x1050）
        Raises:
            RuntimeError: I2C 通信 failed
        Notes:
            - ISR-safe: 否
            - 副作用: 无（仅读取）
        ==========================================
        Read device ID.
        Returns:
            int: Device ID (fixed 4176 = 0x1050)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: None (read-only)
        """
        return self._read16(_REG_DEVICE_ID)

    def deinit(self) -> None:
        """
        释放资源
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用: 释放 I2C 总线和缓冲区引用
        ==========================================
        Release resources.
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Releases I2C bus and buffer references
        """
        self._i2c = None
        self._buf1 = None
        self._buf2 = None

    # --- 私有方法 ---

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Returns:
            None
        ==========================================
        Output debug log.
        Args:
            msg (str): Log message
        Returns:
            None
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[HDC1080] %s" % msg)

    def _read16(self, reg: int) -> int:
        """
        读取 16 位寄存器值
        先发送寄存器地址，等待转换完成后读取 2 字节数据
        Args:
            reg (int): 寄存器地址
        Returns:
            int: 16 位寄存器值（大端序）
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Read 16-bit register value.
        Send register address, wait for conversion, then read 2 bytes.
        Args:
            reg (int): Register address
        Returns:
            int: 16-bit register value (big-endian)
        Raises:
            RuntimeError: I2C communication failed
        """
        if not isinstance(reg, int) or not 0 <= reg <= 0xFF:
            raise ValueError("reg must be a register from 0x00 to 0xFF")
        try:
            # 发送寄存器地址
            self._buf1[0] = reg
            self._i2c.writeto(self._addr, self._buf1)
            # 等待转换完成
            sleep_ms(20)
            # 读取 2 字节数据
            self._i2c.readfrom_into(self._addr, self._buf2)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from e
        # 大端序组合为 16 位整数
        return (self._buf2[0] << 8) | self._buf2[1]

    def _write_config(self) -> None:
        """
        写入配置寄存器
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Write configuration register.
        Raises:
            RuntimeError: I2C communication failed
        """
        try:
            # 寄存器地址 + 配置值
            self._buf2[0] = _REG_CONFIG
            self._buf2[1] = self._config
            self._i2c.writeto(self._addr, self._buf2)
        except OSError as e:
            raise RuntimeError("I2C write config failed") from e

    def _read_config(self) -> None:
        """
        读取配置寄存器并更新内部缓存
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用: 更新 self._config 内部缓存
        ==========================================
        Read configuration register and update internal cache.
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effects: Updates self._config internal cache
        """
        # 配置寄存器高 8 位为保留位，右移 8 位获取有效配置
        self._config = self._read16(_REG_CONFIG) >> 8


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
