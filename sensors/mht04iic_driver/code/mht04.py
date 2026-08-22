# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:44
# @Author  : December
# @File    : mht04.py
# @Description : 敏源 MHT04-IIC 温湿度传感器驱动，支持 CRC 校验与出厂参数补偿
# @License : MIT

__version__ = "1.0.0"
__author__ = "December"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import micropython
import time
from machine import I2C

# ======================================== 全局变量 ============================================

_COS_WEIGHTS = (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 40.0)
_CFB_WEIGHTS = (2.0, 4.0, 8.0, 16.0, 32.0, 46.0)
_CFB_BASE = 2.0
_CFB_TO_RANGE = 0.507 / 3.6

# ======================================== 功能函数 ============================================


def calculate_crc8(data: object, start: int = 0, length: int = -1) -> int:
    """
    计算 MDC04 CRC-8 校验值
    Args:
        data (object): bytes、bytearray 或 memoryview 数据
        start (int): 起始索引
        length (int): 参与计算的字节数，-1 表示计算至末尾
    Returns:
        int: CRC-8 校验值
    Raises:
        ValueError: data、start 或 length 的类型或范围无效
    Notes:
        - 多项式为 0x31，初始值为 0xFF
        - ISR-safe: 是
    ==========================================
    Calculate the MDC04 CRC-8 checksum.
    Args:
        data (object): bytes, bytearray, or memoryview data
        start (int): Start index
        length (int): Number of bytes; -1 processes to the end
    Returns:
        int: CRC-8 checksum
    Raises:
        ValueError: Invalid data, start, or length type or range
    Notes:
        - Polynomial is 0x31 and initial value is 0xFF
        - ISR-safe: Yes
    """
    if data is None or not isinstance(data, (bytes, bytearray, memoryview)):
        raise ValueError("data must be bytes-like")
    if not isinstance(start, int):
        raise ValueError("start must be int")
    if not isinstance(length, int):
        raise ValueError("length must be int")

    data_length = len(data)
    if start < 0 or start > data_length:
        raise ValueError("start is out of range")
    if length < -1:
        raise ValueError("length must be -1 or greater")
    if length == -1:
        length = data_length - start
    if start + length > data_length:
        raise ValueError("start and length exceed data size")

    crc = 0xFF
    for index in range(start, start + length):
        crc ^= data[index]
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def decode_cap_offset(cos_register: int) -> float:
    """将 COS 寄存器值转换为电容偏置，单位为 pF。"""
    offset = 0.0
    for bit, weight in enumerate(_COS_WEIGHTS):
        if cos_register & (1 << bit):
            offset += weight
    return offset


def decode_cap_range(cfb_register: int) -> float:
    """将 CFB 寄存器值转换为电容量程，单位为 pF。"""
    feedback = _CFB_BASE
    for bit, weight in enumerate(_CFB_WEIGHTS):
        if cfb_register & (1 << bit):
            feedback += weight
    return _CFB_TO_RANGE * feedback


# ======================================== 自定义类 ============================================


class MHT04Error(Exception):
    """MHT04 驱动基础异常 / Base exception for the MHT04 driver."""


class MHT04CommunicationError(MHT04Error):
    """MHT04 通信异常 / MHT04 communication error."""


class MHT04CRCError(MHT04Error):
    """MHT04 CRC 校验异常 / MHT04 CRC validation error."""


class MHT04:
    """
    敏源 MHT04-IIC 温湿度传感器驱动类
    Attributes:
        i2c (I2C): 外部传入的 I2C 总线实例
        address (int): 7 位 I2C 地址
        conversion_time_ms (int): 测量转换等待时间
        clamp_humidity (bool): 是否将湿度限制在 0~100 %RH
    Methods:
        crc8(data): 计算协议 CRC-8
        refresh_configuration(): 读取出厂校准参数
        read_raw(): 读取原始温度和电容值
        read(): 读取温度和相对湿度
        read_detailed(): 读取包含电容值的完整结果
        set_conversion_time_ms(value): 设置转换等待时间
        set_clamp_humidity(enable): 设置湿度限幅状态
        deinit(): 释放驱动缓存资源
    Notes:
        - I2C 总线由调用者创建并传入，驱动不会释放总线
        - 首次 read() 会自动读取并缓存 EEPROM 校准参数
    ==========================================
    Mysentech MHT04-IIC temperature and humidity sensor driver.
    Attributes:
        i2c (I2C): Externally provided I2C bus instance
        address (int): 7-bit I2C address
        conversion_time_ms (int): Measurement conversion delay
        clamp_humidity (bool): Clamp humidity to 0..100 %RH
    Methods:
        crc8(data): Calculate protocol CRC-8
        refresh_configuration(): Read factory calibration parameters
        read_raw(): Read raw temperature and capacitance
        read(): Read temperature and relative humidity
        read_detailed(): Read complete results including capacitance
        set_conversion_time_ms(value): Set conversion delay
        set_clamp_humidity(enable): Set humidity clamping
        deinit(): Release driver cache resources
    Notes:
        - The caller owns the injected I2C bus; the driver does not deinitialize it
        - The first read() caches factory calibration data from EEPROM
    """

    DEFAULT_ADDRESS = micropython.const(0x44)
    MIN_CONVERSION_TIME_MS = micropython.const(30)
    DEFAULT_RETRIES = micropython.const(2)
    DEFAULT_RETRY_DELAY_MS = micropython.const(5)

    _CMD_READ_REGISTER = micropython.const(0xD200)
    _CONVERT_COMMAND = b"\x2c\x10"

    _REG_HUM_A_H = micropython.const(0x08)
    _REG_HUM_B_L = micropython.const(0x0B)
    _REG_COS = micropython.const(0x1D)
    _REG_CFB = micropython.const(0x22)

    __slots__ = (
        "_i2c",
        "_addr",
        "_conversion_time_ms",
        "_clamp_humidity",
        "_retries",
        "_retry_delay_ms",
        "_debug",
        "_hum_a",
        "_hum_b",
        "_cap_offset",
        "_cap_range",
        "_register_buffer",
        "_measurement_buffer",
    )

    def __init__(
        self,
        i2c: I2C,
        address: int = DEFAULT_ADDRESS,
        conversion_time_ms: int = MIN_CONVERSION_TIME_MS,
        clamp_humidity: bool = True,
        retries: int = DEFAULT_RETRIES,
        retry_delay_ms: int = DEFAULT_RETRY_DELAY_MS,
        debug: bool = False,
    ) -> None:
        """
        初始化 MHT04-IIC 驱动
        Args:
            i2c (I2C): 外部传入的 I2C 总线实例
            address (int): 7 位 I2C 地址，默认 0x44
            conversion_time_ms (int): 转换等待时间，最小 30 ms
            clamp_humidity (bool): 是否限制湿度为 0~100 %RH
            retries (int): I2C 瞬态错误重试次数，范围 0~3
            retry_delay_ms (int): 重试间隔，范围 0~1000 ms
            debug (bool): 是否输出调试日志
        Returns:
            None
        Raises:
            ValueError: 参数类型、能力或范围无效
        Notes:
            - 副作用：保存 I2C 引用并分配两个复用缓冲区，不访问硬件
            - ISR-safe: 否
        ==========================================
        Initialize the MHT04-IIC driver.
        Args:
            i2c (I2C): Externally provided I2C bus instance
            address (int): 7-bit I2C address, default 0x44
            conversion_time_ms (int): Conversion delay, minimum 30 ms
            clamp_humidity (bool): Clamp humidity to 0..100 %RH
            retries (int): I2C transient-error retries, range 0..3
            retry_delay_ms (int): Retry delay, range 0..1000 ms
            debug (bool): Enable debug output
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type, capability, or range
        Notes:
            - Side effect: stores the I2C reference and allocates two reusable buffers
            - ISR-safe: No
        """
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise ValueError("i2c must provide writeto and readfrom_into")
        if address is None or not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be a 7-bit I2C address")
        if conversion_time_ms is None or not isinstance(conversion_time_ms, int):
            raise ValueError("conversion_time_ms must be int")
        if conversion_time_ms < self.MIN_CONVERSION_TIME_MS:
            raise ValueError("conversion_time_ms must be at least 30")
        if clamp_humidity is None or not isinstance(clamp_humidity, bool):
            raise ValueError("clamp_humidity must be bool")
        if retries is None or not isinstance(retries, int):
            raise ValueError("retries must be int")
        if retries < 0 or retries > 3:
            raise ValueError("retries must be in range 0..3")
        if retry_delay_ms is None or not isinstance(retry_delay_ms, int):
            raise ValueError("retry_delay_ms must be int")
        if retry_delay_ms < 0 or retry_delay_ms > 1000:
            raise ValueError("retry_delay_ms must be in range 0..1000")
        if debug is None or not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._addr = address
        self._conversion_time_ms = conversion_time_ms
        self._clamp_humidity = clamp_humidity
        self._retries = retries
        self._retry_delay_ms = retry_delay_ms
        self._debug = debug
        self._hum_a = None
        self._hum_b = None
        self._cap_offset = None
        self._cap_range = None
        self._register_buffer = bytearray(3)
        self._measurement_buffer = bytearray(6)

    @staticmethod
    def crc8(data: object) -> int:
        """
        计算完整数据的 MDC04 CRC-8 校验值
        Args:
            data (object): bytes、bytearray 或 memoryview
        Returns:
            int: CRC-8 校验值
        Raises:
            ValueError: data 类型无效
        Notes:
            - 无硬件副作用
            - ISR-safe: 是
        ==========================================
        Calculate the MDC04 CRC-8 checksum for all data.
        Args:
            data (object): bytes, bytearray, or memoryview
        Returns:
            int: CRC-8 checksum
        Raises:
            ValueError: Invalid data type
        Notes:
            - No hardware side effects
            - ISR-safe: Yes
        """
        if data is None:
            raise ValueError("data must not be None")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ValueError("data must be bytes-like")
        return calculate_crc8(data)

    def refresh_configuration(self) -> dict:
        """
        读取并缓存出厂湿度校准系数与电容配置
        Args:
            无
        Returns:
            dict: 湿度斜率、湿度偏置、电容偏置和电容量程
        Raises:
            MHT04CommunicationError: I2C 通信失败
            MHT04CRCError: 寄存器响应 CRC 无效
        Notes:
            - 副作用：执行 6 次寄存器读取并更新校准缓存
            - ISR-safe: 否
        ==========================================
        Read and cache factory humidity and capacitance configuration.
        Args:
            None
        Returns:
            dict: Humidity slope/offset and capacitance offset/range
        Raises:
            MHT04CommunicationError: I2C communication failed
            MHT04CRCError: Invalid register-response CRC
        Notes:
            - Side effect: performs six register reads and updates cached calibration
            - ISR-safe: No
        """
        calibration = bytearray(4)
        for index in range(4):
            calibration[index] = self._read_register(self._REG_HUM_A_H + index)

        hum_a_raw = (calibration[0] << 8) | calibration[1]
        hum_b_raw = (calibration[2] << 8) | calibration[3]
        cos_register = self._read_register(self._REG_COS)
        cfb_register = self._read_register(self._REG_CFB)

        self._hum_a = hum_a_raw / 100.0
        self._hum_b = hum_b_raw / 10.0
        self._cap_offset = decode_cap_offset(cos_register)
        self._cap_range = decode_cap_range(cfb_register)

        self._log("factory configuration refreshed")
        return {
            "humidity_slope": self._hum_a,
            "humidity_offset": self._hum_b,
            "cap_offset_pf": self._cap_offset,
            "cap_range_pf": self._cap_range,
        }

    def read_raw(self) -> tuple:
        """
        启动一次转换并读取原始温度、电容值
        Args:
            无
        Returns:
            tuple: (有符号温度原始值, 无符号电容原始值)
        Raises:
            MHT04CommunicationError: I2C 通信失败
            MHT04CRCError: 测量数据 CRC 无效
        Notes:
            - 副作用：发送 0x2C10，阻塞至少 30 ms，然后读取 6 字节
            - ISR-safe: 否
        ==========================================
        Start one conversion and read raw temperature and capacitance.
        Args:
            None
        Returns:
            tuple: (signed temperature raw value, unsigned capacitance raw value)
        Raises:
            MHT04CommunicationError: I2C communication failed
            MHT04CRCError: Invalid measurement CRC
        Notes:
            - Side effect: sends 0x2C10, blocks at least 30 ms, then reads six bytes
            - ISR-safe: No
        """
        self._write_convert_command()
        time.sleep_ms(self._conversion_time_ms)
        self._read_measurement_response()

        response = self._measurement_buffer
        self._check_crc(response, 0, 2, response[2], "temperature")
        self._check_crc(response, 3, 2, response[5], "capacitance")

        temperature_raw = (response[0] << 8) | response[1]
        if temperature_raw & 0x8000:
            temperature_raw -= 0x10000
        capacitance_raw = (response[3] << 8) | response[4]
        return temperature_raw, capacitance_raw

    def read(self) -> tuple:
        """
        读取摄氏温度与相对湿度
        Args:
            无
        Returns:
            tuple: (温度 ℃, 相对湿度 %RH)
        Raises:
            MHT04CommunicationError: I2C 通信失败
            MHT04CRCError: 响应 CRC 无效
        Notes:
            - 副作用：首次调用会先读取出厂参数，每次调用执行一次测量
            - ISR-safe: 否
        ==========================================
        Read temperature in Celsius and relative humidity.
        Args:
            None
        Returns:
            tuple: (temperature in C, relative humidity in %RH)
        Raises:
            MHT04CommunicationError: I2C communication failed
            MHT04CRCError: Invalid response CRC
        Notes:
            - Side effect: the first call reads factory data; every call measures once
            - ISR-safe: No
        """
        values = self._read_values()
        return values[0], values[1]

    def read_detailed(self) -> dict:
        """
        读取温度、湿度、电容和原始数据
        Args:
            无
        Returns:
            dict: 完整测量结果
        Raises:
            MHT04CommunicationError: I2C 通信失败
            MHT04CRCError: 响应 CRC 无效
        Notes:
            - 副作用：首次调用会先读取出厂参数，每次调用执行一次测量
            - ISR-safe: 否
        ==========================================
        Read temperature, humidity, capacitance, and raw values.
        Args:
            None
        Returns:
            dict: Complete measurement result
        Raises:
            MHT04CommunicationError: I2C communication failed
            MHT04CRCError: Invalid response CRC
        Notes:
            - Side effect: the first call reads factory data; every call measures once
            - ISR-safe: No
        """
        values = self._read_values()
        return {
            "temperature_c": values[0],
            "humidity_rh": values[1],
            "capacitance_pf": values[2],
            "temperature_raw": values[3],
            "capacitance_raw": values[4],
        }

    def set_conversion_time_ms(self, value: int) -> None:
        """
        设置测量转换等待时间
        Args:
            value (int): 毫秒数，必须不小于 30
        Returns:
            None
        Raises:
            ValueError: value 类型或范围无效
        Notes:
            - 副作用：修改后续 read_raw() 的阻塞时间
            - ISR-safe: 否
        ==========================================
        Set the measurement conversion delay.
        Args:
            value (int): Milliseconds, at least 30
        Returns:
            None
        Raises:
            ValueError: Invalid value type or range
        Notes:
            - Side effect: changes future read_raw() blocking time
            - ISR-safe: No
        """
        if value is None or not isinstance(value, int):
            raise ValueError("value must be int")
        if value < self.MIN_CONVERSION_TIME_MS:
            raise ValueError("value must be at least 30")
        self._conversion_time_ms = value

    def set_clamp_humidity(self, enable: bool) -> None:
        """
        设置湿度结果是否限制在 0~100 %RH
        Args:
            enable (bool): True 启用限幅，False 返回未限幅计算值
        Returns:
            None
        Raises:
            ValueError: enable 不是 bool
        Notes:
            - 副作用：修改后续湿度结果处理方式
            - ISR-safe: 否
        ==========================================
        Enable or disable humidity clamping to 0..100 %RH.
        Args:
            enable (bool): True to clamp, False for the unclamped result
        Returns:
            None
        Raises:
            ValueError: enable is not bool
        Notes:
            - Side effect: changes future humidity result processing
            - ISR-safe: No
        """
        if enable is None or not isinstance(enable, bool):
            raise ValueError("enable must be bool")
        self._clamp_humidity = enable

    @property
    def i2c(self) -> I2C:
        """返回外部 I2C 实例 / Return the external I2C instance."""
        return self._i2c

    @property
    def address(self) -> int:
        """返回 7 位 I2C 地址 / Return the 7-bit I2C address."""
        return self._addr

    @property
    def conversion_time_ms(self) -> int:
        """返回转换等待时间 / Return the conversion delay."""
        return self._conversion_time_ms

    @conversion_time_ms.setter
    def conversion_time_ms(self, value: int) -> None:
        if value is None or not isinstance(value, int):
            raise ValueError("value must be int")
        if value < self.MIN_CONVERSION_TIME_MS:
            raise ValueError("value must be at least 30")
        self.set_conversion_time_ms(value)

    @property
    def clamp_humidity(self) -> bool:
        """返回湿度限幅状态 / Return the humidity clamp state."""
        return self._clamp_humidity

    @clamp_humidity.setter
    def clamp_humidity(self, value: bool) -> None:
        if value is None or not isinstance(value, bool):
            raise ValueError("value must be bool")
        self.set_clamp_humidity(value)

    def _read_register(self, register: int) -> int:
        """读取一个带 CRC 的 MDC04 寄存器。"""
        if not isinstance(register, int) or register < 0x00 or register > 0xFF:
            raise ValueError("register must be an 8-bit int")
        command = self._CMD_READ_REGISTER | register
        command_bytes = bytes((command >> 8, command & 0xFF))

        last_error = None
        for attempt in range(self._retries + 1):
            try:
                # 使用重复起始条件衔接命令写入和数据读取
                self._i2c.writeto(self._addr, command_bytes, False)
                self._i2c.readfrom_into(self._addr, self._register_buffer)
                break
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    time.sleep_ms(self._retry_delay_ms)
        else:
            raise MHT04CommunicationError("I2C register read failed at 0x%02X" % register) from last_error

        response = self._register_buffer
        self._check_crc(response, 0, 2, response[2], "register 0x%02X" % register)
        return response[0]

    def _write_convert_command(self) -> None:
        """发送温度与电容通道 1 联合转换命令。"""
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                self._i2c.writeto(self._addr, self._CONVERT_COMMAND)
                return
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    time.sleep_ms(self._retry_delay_ms)
        raise MHT04CommunicationError("I2C conversion command failed") from last_error

    def _read_measurement_response(self) -> None:
        """读取 6 字节温度与电容响应。"""
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                self._i2c.readfrom_into(self._addr, self._measurement_buffer)
                return
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    time.sleep_ms(self._retry_delay_ms)
        raise MHT04CommunicationError("I2C measurement read failed") from last_error

    def _check_crc(
        self,
        data: object,
        start: int,
        length: int,
        expected: int,
        label: str,
    ) -> None:
        """校验响应数据的 CRC-8。"""
        actual = calculate_crc8(data, start, length)
        if actual != expected:
            raise MHT04CRCError("%s CRC mismatch: received 0x%02X, calculated 0x%02X" % (label, expected, actual))

    def _read_values(self) -> tuple:
        """读取并换算温度、湿度、电容和原始数据。"""
        if self._hum_a is None:
            self.refresh_configuration()

        temperature_raw, capacitance_raw = self.read_raw()
        temperature = temperature_raw / 256.0 + 40.0
        capacitance = 2.0 * (capacitance_raw / 65535.0 - 0.5) * self._cap_range + self._cap_offset

        # 使用出厂斜率、偏置以及手册规定的温度补偿系数
        humidity = self._hum_a * capacitance - self._hum_b
        humidity -= 0.2 * (30.0 - temperature)
        if self._clamp_humidity:
            humidity = min(100.0, max(0.0, humidity))

        return temperature, humidity, capacitance, temperature_raw, capacitance_raw

    def _log(self, message: str) -> None:
        """按 debug 开关输出调试信息。"""
        if isinstance(message, str) is False:
            raise ValueError("message must be str")
        if self._debug:
            print("[MHT04] %s" % message)

    def deinit(self) -> None:
        """
        释放驱动内部缓存状态
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - 副作用：清除出厂参数缓存，但不释放调用者拥有的 I2C 总线
            - ISR-safe: 否
        ==========================================
        Release internal driver cache state.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - Side effect: clears cached factory data but keeps the caller-owned I2C bus
            - ISR-safe: No
        """
        self._hum_a = None
        self._hum_b = None
        self._cap_offset = None
        self._cap_range = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
