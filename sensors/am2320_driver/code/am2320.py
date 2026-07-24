# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Mike Causer
# @File    : am2320.py
# @Description : Aosong AM2320 温湿度传感器 I2C 驱动
# @License : MIT

__version__ = "1.1.0"
__author__ = "Mike Causer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import micropython
from time import sleep_ms
from micropython import const

# 预留 ISR 调试异常缓冲区
micropython.alloc_emergency_exception_buf(100)

# ======================================== 导入相关模块 =========================================
# （模块导入已在文件头部完成，此处保留分区标注）

# ======================================== 全局变量 ============================================

# 模块级复用 I/O 缓冲区，减少运行时内存分配
_BUF = bytearray(8)

# ======================================== 功能函数 ============================================


def _crc16(buf):
    """
    计算 Modbus CRC-16 校验值
    Args:
        buf: 待校验的字节缓冲区
    Returns:
        int: 16 位 CRC 校验值
    ==========================================
    Calculate Modbus CRC-16 checksum.
    Args:
        buf: Byte buffer to checksum
    Returns:
        int: 16-bit CRC value
    """
    crc = 0xFFFF
    for c in buf:
        crc ^= c
        for _ in range(8):
            if crc & 0x01:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


# ======================================== 自定义类 ============================================


class AM2320:
    """
    AM2320 温湿度传感器 I2C 驱动类
    Attributes:
        _i2c: I2C 总线实例（外部注入）
        _addr (int): 设备 I2C 地址
        _buf: 传感器数据缓冲区（引用模块级 _BUF）
        _debug (bool): 调试日志开关
    Methods:
        check(): 检测传感器是否存在
        measure(): 触发一次温湿度测量
        temperature(): 获取最近一次测量的温度值（℃）
        humidity(): 获取最近一次测量的相对湿度值（%）
        deinit(): 释放驱动资源
    Notes:
        - I2C 总线实例由调用方创建并传入，不在类内创建总线对象
        - 传感器每次 measure() 后自动进入休眠模式，下次测量前自动唤醒
        - temperature() 和 humidity() 读取的是最近一次 measure() 的结果
    ==========================================
    Aosong AM2320 temperature and humidity sensor I2C driver.
    Attributes:
        _i2c: I2C bus instance (externally injected)
        _addr (int): Device I2C address
        _buf: Sensor data buffer (references module-level _BUF)
        _debug (bool): Debug log toggle
    Methods:
        check(): Check if sensor is present on the I2C bus
        measure(): Trigger a temperature/humidity measurement
        temperature(): Get temperature from last measurement (°C)
        humidity(): Get relative humidity from last measurement (%)
        deinit(): Release driver resources
    Notes:
        - I2C bus instance is created externally and injected; never created inside the class
        - Sensor auto-sleeps after each measure(); auto-wakes before next measurement
        - temperature() and humidity() return data from the most recent measure() call
    """

    # 类级常量：传感器固定 I2C 地址
    I2C_ADDRESS = const(0x5C)

    # 实例属性槽位声明，节省 MicroPython 内存
    __slots__ = ("_i2c", "_addr", "_buf", "_debug")

    def __init__(self, i2c, debug: bool = False) -> None:
        """
        初始化 AM2320 传感器驱动实例
        Args:
            i2c: I2C 总线实例（须具备 writeto 和 readfrom_mem_into 方法）
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: i2c 参数为 None 或不具备 I2C 总线方法
        Notes:
            - 副作用：无
        ==========================================
        Initialize AM2320 sensor driver instance.
        Args:
            i2c: I2C bus instance (must have writeto and readfrom_mem_into methods)
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: i2c is None or lacks I2C bus methods
        Notes:
            - Side effects: None
        """
        # i2c 参数校验：None 检查
        if i2c is None:
            raise ValueError("i2c must not be None")
        # i2c 参数校验：鸭子类型检查，确保传入对象具备 I2C 总线方法
        if hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_mem_into") is False:
            raise ValueError("i2c must be an I2C instance with writeto/readfrom_mem_into")
        self._i2c = i2c
        self._addr = self.I2C_ADDRESS
        # 复用模块级缓冲区，避免每次测量分配新内存
        self._buf = _BUF
        self._debug = debug

    def _log(self, msg):
        """
        调试日志输出（受 _debug 开关控制）
        ==========================================
        Debug log output (controlled by _debug flag).
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[AM2320] %s" % msg)

    def check(self):
        """
        检测传感器是否在 I2C 总线上存在
        Returns:
            bool: 传感器存在则返回 True
        Raises:
            RuntimeError: 在 I2C 总线上未检测到传感器
        Notes:
            - ISR-safe: 否
            - 副作用：发送唤醒信号，扫描 I2C 总线
        ==========================================
        Check if the sensor is present on the I2C bus.
        Returns:
            bool: True if sensor is found
        Raises:
            RuntimeError: Sensor not detected on I2C bus
        Notes:
            - ISR-safe: No
            - Side effects: Sends wake signal, scans I2C bus
        """
        # 先发送唤醒信号
        self._wake()
        # 扫描 I2C 总线，检查设备地址是否存在
        scan_result = self._i2c.scan()
        if scan_result.count(self._addr) == 0:
            raise RuntimeError("AM2320 not found at I2C address 0x%02X" % self._addr)
        self._log("sensor found at 0x%02X" % self._addr)
        return True

    def measure(self, retries=1, delay_ms=5):
        """
        触发一次温湿度测量，结果存入内部缓冲区
        Args:
            retries (int): I2C 通信失败重试次数，默认 1（不重试）
            delay_ms (int): 重试间隔（毫秒），默认 5
        Raises:
            RuntimeError: I2C 通信失败（包含重试后仍然失败）
            ValueError: CRC 校验失败，数据可能损坏
        Notes:
            - ISR-safe: 否
            - 副作用：唤醒传感器，通过 I2C 读取 8 字节寄存器数据并更新内部缓冲区
            - 测量结果需通过 temperature() 和 humidity() 分别获取
        ==========================================
        Trigger a temperature and humidity measurement.
        Results are stored in internal buffer.
        Args:
            retries (int): Retry count on I2C failure, default 1 (no retry)
            delay_ms (int): Delay between retries in milliseconds, default 5
        Raises:
            RuntimeError: I2C communication failed (including after retries)
            ValueError: CRC checksum error, data may be corrupted
        Notes:
            - ISR-safe: No
            - Side effects: Wakes sensor, reads 8 bytes via I2C, updates internal buffer
            - Access results via temperature() and humidity()
        """
        buf = self._buf
        # 唤醒处于休眠状态的传感器
        self._wake()
        # 向传感器发送读寄存器命令：功能码 0x03，从地址 0x00 读 4 个寄存器
        for attempt in range(retries + 1):
            try:
                self._i2c.writeto(self._addr, b"\x03\x00\x04")
                # 等待传感器完成数据采集（至少 1.5ms，取 2ms 留有余量）
                sleep_ms(2)
                # 读取 8 字节原始数据到缓冲区
                self._i2c.readfrom_mem_into(self._addr, 0, buf)
                break
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("AM2320 I2C read failed after %d retries" % retries) from e
                # 重试前等待
                sleep_ms(delay_ms)
        # 计算 CRC-16 校验值并与传感器返回的校验值比对
        crc = buf[6] | (buf[7] << 8)
        if crc != _crc16(buf[:-2]):
            raise ValueError("AM2320 CRC checksum error")
        self._log("measure OK: raw=%s" % buf.hex())

    def temperature(self):
        """
        获取最近一次测量的温度值
        Returns:
            float: 温度值（℃），负值表示零下温度
        Notes:
            - ISR-safe: 否
            - 副作用：无（仅读取内部缓冲区，不访问硬件）
            - 调用前须先调用 measure() 获取最新数据
        ==========================================
        Get temperature from the most recent measurement.
        Returns:
            float: Temperature in Celsius, negative for sub-zero
        Notes:
            - ISR-safe: No
            - Side effects: None (reads internal buffer only, no hardware access)
            - Must call measure() first to obtain fresh data
        """
        buf = self._buf
        # 解析温度：bit14 为符号位（0=正温，1=负温），分辨率 0.1℃
        t = ((buf[4] & 0x7F) << 8 | buf[5]) * 0.1
        if buf[4] & 0x80:
            t = -t
        return t

    def humidity(self):
        """
        获取最近一次测量的相对湿度值
        Returns:
            float: 相对湿度百分比（%）
        Notes:
            - ISR-safe: 否
            - 副作用：无（仅读取内部缓冲区，不访问硬件）
            - 调用前须先调用 measure() 获取最新数据
        ==========================================
        Get relative humidity from the most recent measurement.
        Returns:
            float: Relative humidity percentage (%)
        Notes:
            - ISR-safe: No
            - Side effects: None (reads internal buffer only, no hardware access)
            - Must call measure() first to obtain fresh data
        """
        buf = self._buf
        # 解析湿度：高字节 + 低字节组合，分辨率 0.1%
        return (buf[2] << 8 | buf[3]) * 0.1

    def _wake(self):
        """
        唤醒处于休眠状态的传感器
        Notes:
            - 传感器空闲时自动进入休眠以减少自热影响读数
            - 空写入会触发 OSError（传感器在休眠状态下不响应），这是预期行为，应当忽略
        ==========================================
        Wake the sensor from sleep mode.
        Notes:
            - Sensor auto-sleeps when idle to minimize self-heating
            - Empty write triggers OSError (no response while sleeping), which is expected and ignored
        """
        try:
            # 发送一个空写入来唤醒传感器
            self._i2c.writeto(self._addr, b"")
        except OSError:
            # 空写入唤醒传感器时必然触发 OSError，这是硬件设计行为，正常忽略
            pass
        # 等待传感器完全唤醒（至少 0.8ms，取 10ms 确保稳定）
        sleep_ms(10)

    def deinit(self):
        """
        释放传感器驱动资源
        Notes:
            - 副作用：断开 I2C 总线引用，清空数据缓冲区
            - 调用后该实例不可继续使用
        ==========================================
        Release sensor driver resources.
        Notes:
            - Side effects: Clears I2C bus reference and data buffer
            - Instance is unusable after this call
        """
        self._i2c = None
        self._buf = None
        self._log("deinit done")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
