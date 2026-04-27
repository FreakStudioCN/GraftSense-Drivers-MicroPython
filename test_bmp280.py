# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/24 15:30
# @Author  : leezisheng
# @File    : test_bmp280.py
# @Description : BMP280 temperature and pressure sensor driver for MicroPython
# @License : MIT

__version__ = "1.0.0"
__author__   = "leezisheng"
__license__  = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import micropython
import time
from machine import I2C

micropython.alloc_emergency_exception_buf(100)

# ======================================== 全局变量 ============================================
BMP280_ADDR   = micropython.const(0x76)
REG_TEMP_MSB  = micropython.const(0xFA)
REG_PRESS_MSB = micropython.const(0xF7)
REG_CTRL_MEAS = micropython.const(0xF4)
REG_CALIB     = micropython.const(0x88)
REG_RESET     = micropython.const(0xE0)
_RESET_CMD    = micropython.const(0xB6)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BMP280:
    """
    BMP280 温度/气压传感器驱动类
    Attributes:
        _i2c   (I2C) : I2C 总线实例
        _addr  (int) : 设备 I2C 地址
        _debug (bool): 调试日志开关
        _dig_T1/_dig_T2/_dig_T3 (int): 温度补偿系数
        _dig_P1/_dig_P2         (int): 气压补偿系数
    Methods:
        read_raw()     : 读取原始 ADC 温度和气压值
        get_temp()     : 读取补偿后温度（℃）
        get_pressure() : 读取补偿后气压（Pa）
        reset()        : 软复位传感器
        deinit()       : 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 初始化时自动加载校准系数并配置测量模式
    ==========================================
    BMP280 temperature and pressure sensor driver.
    Attributes:
        _i2c   (I2C) : I2C bus instance
        _addr  (int) : Device I2C address
        _debug (bool): Debug log switch
        _dig_T1/_dig_T2/_dig_T3 (int): Temperature compensation coefficients
        _dig_P1/_dig_P2         (int): Pressure compensation coefficients
    Methods:
        read_raw()     : Read raw ADC temperature and pressure values
        get_temp()     : Read compensated temperature in Celsius
        get_pressure() : Read compensated pressure in Pa
        reset()        : Soft reset the sensor
        deinit()       : Release resources
    Notes:
        - Requires externally provided I2C instance
        - Automatically loads calibration data and configures measurement mode on init
    """

    I2C_DEFAULT_ADDR = micropython.const(0x76)

    def __init__(self, i2c: I2C, addr: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 BMP280 驱动
        Args:
            i2c   (I2C) : 外部传入的 I2C 总线实例
            addr  (int) : 设备 I2C 地址，默认 0x76
            debug (bool): 是否开启调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError  : 参数类型或范围不合法
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：向传感器写入测量控制寄存器 0xF4
        ==========================================
        Initialize BMP280 driver.
        Args:
            i2c   (I2C) : Externally provided I2C bus instance
            addr  (int) : Device I2C address, default 0x76
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError  : Invalid parameter type or range
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes measurement control register 0xF4
        """
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(addr, int):
            raise ValueError("addr must be int, got %s" % type(addr))
        if addr < 0x00 or addr > 0x7F:
            raise ValueError("addr must be 0x00~0x7F, got 0x%02X" % addr)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c    = i2c
        self._addr   = addr
        self._debug  = debug
        self._dig_T1 = 0
        self._dig_T2 = 0
        self._dig_T3 = 0
        self._dig_P1 = 0
        self._dig_P2 = 0

        self._load_calibration()
        self._write_reg(REG_CTRL_MEAS, 0x27)  # 正常模式，过采样 x1
        self._log("BMP280 initialized at addr 0x%02X" % addr)

    def _log(self, msg: str) -> None:
        if self._debug:
            print("[BMP280] %s" % msg)

    def _read_reg(self, reg: int, nbytes: int) -> bytearray:
        """
        读取寄存器数据
        Args:
            reg    (int): 寄存器地址
            nbytes (int): 读取字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read register data.
        Args:
            reg    (int): Register address
            nbytes (int): Number of bytes to read
        Returns:
            bytearray: Data read
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        buf = bytearray(nbytes)
        try:
            self._i2c.readfrom_mem_into(self._addr, reg, buf)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from e
        return buf

    def _write_reg(self, reg: int, data: int) -> None:
        """
        写入寄存器
        Args:
            reg  (int): 寄存器地址
            data (int): 写入值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write register.
        Args:
            reg  (int): Register address
            data (int): Value to write
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([data]))
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % reg) from e

    def _load_calibration(self) -> None:
        """
        从传感器加载出厂校准系数
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：更新实例校准系数属性
        ==========================================
        Load factory calibration coefficients from sensor.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Updates instance calibration attributes
        """
        data = self._read_reg(REG_CALIB, 24)
        self._dig_T1 = data[1] << 8 | data[0]
        self._dig_T2 = data[3] << 8 | data[2]
        if self._dig_T2 > 32767:
            self._dig_T2 -= 65536
        self._dig_T3 = data[5] << 8 | data[4]
        if self._dig_T3 > 32767:
            self._dig_T3 -= 65536
        self._dig_P1 = data[7] << 8 | data[6]
        self._dig_P2 = data[9] << 8 | data[8]
        if self._dig_P2 > 32767:
            self._dig_P2 -= 65536
        self._log("Calibration loaded")

    def read_raw(self) -> tuple:
        """
        读取原始 ADC 温度和气压值
        Args:
            无
        Returns:
            tuple: (raw_temp: int, raw_press: int)
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC temperature and pressure values.
        Args:
            None
        Returns:
            tuple: (raw_temp: int, raw_press: int)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        data = self._read_reg(REG_PRESS_MSB, 6)
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp  = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return raw_temp, raw_press

    def get_temp(self) -> float:
        """
        读取补偿后温度值
        Args:
            无
        Returns:
            float: 温度（℃）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read compensated temperature.
        Args:
            None
        Returns:
            float: Temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        raw_temp, _ = self.read_raw()
        v1 = (raw_temp / 16384.0 - self._dig_T1 / 1024.0) * self._dig_T2
        v2 = (raw_temp / 131072.0 - self._dig_T1 / 8192.0) ** 2 * self._dig_T3
        t_fine = v1 + v2
        return t_fine / 5120.0

    def get_pressure(self) -> float:
        """
        读取补偿后气压值
        Args:
            无
        Returns:
            float: 气压（Pa）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read compensated pressure.
        Args:
            None
        Returns:
            float: Pressure in Pa
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        raw_temp, raw_press = self.read_raw()
        v1 = (raw_temp / 16384.0 - self._dig_T1 / 1024.0) * self._dig_T2
        v2 = (raw_temp / 131072.0 - self._dig_T1 / 8192.0) ** 2 * self._dig_T3
        t_fine = v1 + v2
        p  = t_fine / 2.0 - 64000.0
        v2 = p * p * self._dig_P2 / 32768.0
        p  = p + (v2 + p * self._dig_P2 + 102400.0) / 16.0
        if p == 0:
            return 0.0
        return 100.0 / p

    def reset(self) -> None:
        """
        软复位传感器
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：传感器重启，需重新初始化
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
            - Side effect: Sensor restarts, re-initialization required
        """
        self._write_reg(REG_RESET, _RESET_CMD)
        time.sleep_ms(10)
        self._log("BMP280 reset")

    def deinit(self) -> None:
        """
        释放驱动资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：将传感器置于睡眠模式
        ==========================================
        Release driver resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Puts sensor into sleep mode
        """
        try:
            self._write_reg(REG_CTRL_MEAS, 0x00)  # 睡眠模式
        except RuntimeError:
            pass
        self._log("BMP280 deinitialized")

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
