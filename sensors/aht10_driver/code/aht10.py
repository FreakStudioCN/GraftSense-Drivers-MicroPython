# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 16:21
# @Author  : Andreas Bühl
# @File    : aht10.py
# @Description : AHT10 数字温湿度传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Andreas Bühl"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import utime
from micropython import const

# ======================================== 全局变量 ============================================

# I2C 读写复用缓冲区，减少内存分配
_BUF6 = bytearray(6)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class AHT10:
    """
    AHT10 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        reset(): 软复位传感器
        initialize(): 初始化传感器并返回校准状态
        status: 读取传感器状态字节（属性）
        relative_humidity: 读取相对湿度百分比（属性）
        temperature: 读取温度值（属性）
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 上电后需等待至少 20ms 再进行初始化
        - 所有读写操作基于 I2C 标准模式
    ==========================================
    AHT10 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log flag
    Methods:
        reset(): Soft reset the sensor
        initialize(): Initialize sensor and return calibration status
        status: Read sensor status byte (property)
        relative_humidity: Read relative humidity percentage (property)
        temperature: Read temperature value (property)
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance
        - Wait at least 20ms after power-on before initialization
        - All read/write operations use standard I2C mode
    """

    AHT10_I2CADDR_DEFAULT = const(0x38)
    AHT10_CMD_INITIALIZE = const(0xE1)
    AHT10_CMD_TRIGGER = const(0xAC)
    AHT10_CMD_SOFTRESET = const(0xBA)
    AHT10_STATUS_BUSY = const(0x80)
    AHT10_STATUS_CALIBRATED = const(0x08)

    __slots__ = ("_i2c", "_address", "_debug")

    def __init__(self, i2c: object, address: int = AHT10_I2CADDR_DEFAULT, debug: bool = False) -> None:
        """
        初始化 AHT10 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x38
            debug (bool): 是否开启调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 参数无效或 address 类型错误
            RuntimeError: 传感器初始化失败
        Notes:
            - 执行软复位和初始化流程
            - 上电后首次调用需等待至少 20ms
            - ISR-safe: 否
        ==========================================
        Initialize AHT10 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x38
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: Invalid i2c parameter or wrong address type
            RuntimeError: Sensor initialization failed
        Notes:
            - Performs soft reset and initialization sequence
            - Wait at least 20ms after power-on for first call
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        # 参数校验：i2c 必须具有 I2C 总线写方法
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 类型检查
        if isinstance(address, int) is False:
            raise ValueError("address must be int, got %s" % type(address))
        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 上电稳定延时
        utime.sleep_ms(20)
        self.reset()
        if not self.initialize():
            raise RuntimeError("Could not initialize AHT10")

    def reset(self) -> None:
        """
        软复位传感器
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 复位后需等待 20ms 再进行后续操作
            - ISR-safe: 否
        ==========================================
        Soft reset the sensor.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Must wait 20ms after reset before further operations
            - ISR-safe: No
        """
        # 构造复位命令并写入
        _BUF6[0] = self.AHT10_CMD_SOFTRESET
        try:
            self._i2c.writeto(self._address, _BUF6[0:1])
        except OSError as e:
            raise RuntimeError("I2C write failed during reset") from e
        # 等待复位完成
        utime.sleep_ms(20)

    def initialize(self) -> bool:
        """
        初始化传感器并返回校准状态
        Returns:
            bool: True 表示传感器已校准
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 发送初始化命令 0xE1 后等待空闲
            - ISR-safe: 否
        ==========================================
        Initialize sensor and return calibration status.
        Returns:
            bool: True if sensor is calibrated
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Sends init command 0xE1 then waits for idle
            - ISR-safe: No
        """
        # 构造初始化命令：0xE1, 0x08, 0x00
        _BUF6[0] = self.AHT10_CMD_INITIALIZE
        _BUF6[1] = 0x08
        _BUF6[2] = 0x00
        try:
            self._i2c.writeto(self._address, _BUF6[0:3])
        except OSError as e:
            raise RuntimeError("I2C write failed during initialize") from e
        # 等待传感器完成初始化
        self._wait_for_idle()
        # 返回校准状态位
        return bool(self.status & self.AHT10_STATUS_CALIBRATED)

    @property
    def status(self) -> int:
        """
        读取传感器状态字节
        Returns:
            int: 状态寄存器值，bit7=忙碌，bit3=已校准
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：触发 I2C 读取操作
        ==========================================
        Read sensor status byte.
        Returns:
            int: Status register value, bit7=busy, bit3=calibrated
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Triggers I2C read operation
        """
        self._read_to_buffer()
        return _BUF6[0]

    @property
    def relative_humidity(self) -> float:
        """
        读取相对湿度
        Returns:
            float: 相对湿度百分比（0~100%）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：触发测量并等待完成
        ==========================================
        Read relative humidity.
        Returns:
            float: Relative humidity percentage (0~100%)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Triggers measurement and waits for completion
        """
        # 触发测量并等待完成，读取 6 字节数据到缓冲区
        self._perform_measurement()
        # 提取湿度原始值：buf[1]<<12 | buf[2]<<4 | buf[3]>>4（高 20 位）
        raw_humidity = (_BUF6[1] << 12) | (_BUF6[2] << 4) | (_BUF6[3] >> 4)
        # 转换为相对湿度百分比
        return (raw_humidity * 100) / 0x100000

    @property
    def temperature(self) -> float:
        """
        读取温度值
        Returns:
            float: 温度值（℃）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：触发测量并等待完成
        ==========================================
        Read temperature value.
        Returns:
            float: Temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Triggers measurement and waits for completion
        """
        # 触发测量并等待完成，读取 6 字节数据到缓冲区
        self._perform_measurement()
        # 提取温度原始值：buf[3]低4位<<16 | buf[4]<<8 | buf[5]（低 20 位）
        raw_temperature = ((_BUF6[3] & 0x0F) << 16) | (_BUF6[4] << 8) | _BUF6[5]
        # 转换为摄氏度
        return ((raw_temperature * 200.0) / 0x100000) - 50

    def deinit(self) -> None:
        """
        释放硬件资源
        Returns:
            None
        Notes:
            - 清除 I2C 总线引用
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Returns:
            None
        Notes:
            - Clears I2C bus reference
            - ISR-safe: No
        """
        self._i2c = None
        self._debug = False

    # -------------------------------------------------------------------
    # 私有方法
    # -------------------------------------------------------------------

    def _read_to_buffer(self) -> None:
        """
        从传感器读取 6 字节数据到全局缓冲区 _BUF6
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：修改全局缓冲区 _BUF6 的内容
        ==========================================
        Read 6 bytes from sensor into global buffer _BUF6.
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Modifies global buffer _BUF6 content
        """
        try:
            self._i2c.readfrom_into(self._address, _BUF6)
        except OSError as e:
            raise RuntimeError("I2C read failed") from e

    def _trigger_measurement(self) -> None:
        """
        发送测量触发命令
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 副作用：写入测量命令到传感器
        ==========================================
        Send measurement trigger command.
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Side effect: Writes measurement command to sensor
        """
        # 构造触发测量命令：0xAC, 0x33, 0x00
        _BUF6[0] = self.AHT10_CMD_TRIGGER
        _BUF6[1] = 0x33
        _BUF6[2] = 0x00
        try:
            self._i2c.writeto(self._address, _BUF6[0:3])
        except OSError as e:
            raise RuntimeError("I2C write failed during trigger") from e

    def _wait_for_idle(self) -> None:
        """
        轮询等待传感器空闲（忙碌位清零）
        Notes:
            - 每次检查间隔 5ms
            - 副作用：反复读取状态寄存器
        ==========================================
        Poll until sensor is idle (busy bit cleared).
        Notes:
            - Polling interval: 5ms
            - Side effect: Repeatedly reads status register
        """
        # 轮询状态寄存器，等待忙碌位清零
        while self.status & self.AHT10_STATUS_BUSY:
            utime.sleep_ms(5)

    def _perform_measurement(self) -> None:
        """
        执行完整测量流程：触发 → 等待空闲 → 读取数据
        Notes:
            - 副作用：触发硬件测量并更新缓冲区
        ==========================================
        Execute complete measurement: trigger → wait idle → read data.
        Notes:
            - Side effect: Triggers hardware measurement and updates buffer
        """
        self._trigger_measurement()
        self._wait_for_idle()
        self._read_to_buffer()

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug 为 True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug is True
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[AHT10] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
