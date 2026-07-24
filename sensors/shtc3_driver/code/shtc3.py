# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/11 07:39
# @Author  : mimingxuan
# @File    : shtc3.py
# @Description : SHTC3 温湿度传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "mimingxuan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C
import time
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _crc8(data: bytes, polynomial: int = 0x31) -> int:
    """
    计算 CRC-8 校验值
    Args:
        data (bytes): 待校验数据
        polynomial (int): CRC 多项式，默认 0x31
    Returns:
        int: CRC-8 校验值
    ==========================================
    Calculate CRC-8 checksum.
    Args:
        data (bytes): Data to checksum
        polynomial (int): CRC polynomial, default 0x31
    Returns:
        int: CRC-8 checksum value
    """
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ polynomial) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


# ======================================== 自定义类 ============================================


class SHTC3:
    """
    SHTC3 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _delta_temp (float): 温度补偿值
        _delta_hum (float): 湿度补偿值
        _debug (bool): 调试日志开关
    Methods:
        is_present(): 检测传感器是否存在
        read_id(): 读取传感器 ID
        measure(): 测量温湿度
        measure_int(): 测量温湿度（整数+小数分离）
        set_delta(): 设置温湿度补偿值
        wakeup(): 唤醒传感器
        sleep(): 使传感器休眠
        reset(): 复位传感器
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 传感器默认处于休眠模式，测量前需唤醒
    ==========================================
    SHTC3 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _delta_temp (float): Temperature offset
        _delta_hum (float): Humidity offset
        _debug (bool): Debug log flag
    Methods:
        is_present(): Check if sensor is present
        read_id(): Read sensor ID
        measure(): Measure temperature and humidity
        measure_int(): Measure with integer/decimal separation
        set_delta(): Set temperature/humidity offsets
        wakeup(): Wake up sensor
        sleep(): Put sensor to sleep
        reset(): Reset sensor
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Sensor is in sleep mode by default; wake before measurement
    """

    # 类级常量
    I2C_DEFAULT_ADDR = micropython.const(0x70)
    POLYNOMIAL = micropython.const(0x31)

    # 命令常量
    WAKEUP_CMD = b"\x35\x17"
    SLEEP_CMD = b"\xB0\x98"
    RESET_CMD = b"\x80\x5D"
    READ_ID_CMD = b"\xEF\xC8"

    # 测量命令
    MEASURE_NORMAL_T_FIRST_CMD = b"\x78\x66"
    MEASURE_NORMAL_RH_FIRST_CMD = b"\x58\xE0"
    MEASURE_LOW_POWER_T_FIRST_CMD = b"\x60\x9C"
    MEASURE_LOW_POWER_RH_FIRST_CMD = b"\x40\x1A"

    # 时序常量（毫秒）
    WAKEUP_DELAY_US = micropython.const(240)
    RESET_DELAY_MS = micropython.const(1)
    READ_ID_DELAY_MS = micropython.const(1)
    NORMAL_MEASURE_DELAY_MS = micropython.const(13)
    LOW_POWER_MEASURE_DELAY_MS = micropython.const(1)
    INIT_DELAY_MS = micropython.const(2)

    # 数据转换常量
    TEMP_MIN_C = micropython.const(-45)
    TEMP_SCALE = micropython.const(175)
    RAW_MAX = micropython.const(65536)
    HUM_SCALE = micropython.const(100)

    def __init__(
        self,
        i2c: I2C,
        addr: int = I2C_DEFAULT_ADDR,
        delta_temp: float = 0.0,
        delta_hum: float = 0.0,
        debug: bool = False,
    ) -> None:
        """
        初始化 SHTC3 传感器
        Args:
            i2c (I2C): I2C 总线实例
            addr (int): 设备 I2C 地址，默认 0x70
            delta_temp (float): 温度补偿值（℃）
            delta_hum (float): 湿度补偿值（%）
            debug (bool): 是否开启调试日志
        Raises:
            ValueError: 参数校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize SHTC3 sensor.
        Args:
            i2c (I2C): I2C bus instance
            addr (int): Device I2C address, default 0x70
            delta_temp (float): Temperature offset in Celsius
            delta_hum (float): Humidity offset in percent
            debug (bool): Enable debug logging
        Raises:
            ValueError: Parameter validation failed
        Notes:
            - ISR-safe: No
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(addr, int) or not 0 <= addr <= 0x7F:
            raise ValueError("addr must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        # 参数校验：i2c 必须为 I2C 实例
        if isinstance(i2c, I2C) is False:
            raise ValueError("i2c must be I2C instance, got %s" % type(i2c))
        # 参数校验：addr 类型检查
        if isinstance(addr, int) is False:
            raise ValueError("addr must be int, got %s" % type(addr))
        # 参数校验：delta_temp 类型检查
        if isinstance(delta_temp, (int, float)) is False:
            raise ValueError("delta_temp must be int or float, got %s" % type(delta_temp))
        # 参数校验：delta_hum 类型检查
        if isinstance(delta_hum, (int, float)) is False:
            raise ValueError("delta_hum must be int or float, got %s" % type(delta_hum))
        # 参数校验：debug 类型检查
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = addr
        self._delta_temp = delta_temp
        self._delta_hum = delta_hum
        self._debug = debug

        # 上电后等待传感器稳定
        time.sleep_ms(SHTC3.INIT_DELAY_MS)

    @property
    def i2c(self) -> I2C:
        """获取 I2C 总线实例 / Get I2C bus instance"""
        return self._i2c

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        ==========================================
        Output debug log message.
        Args:
            msg (str): Log message
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[SHTC3] %s" % msg)

    def is_present(self) -> bool:
        """
        检测传感器是否存在
        Returns:
            bool: True 表示传感器存在
        Notes:
            - ISR-safe: 否
            - 通过尝试读取传感器 ID 来判断
        ==========================================
        Check if sensor is present on the bus.
        Returns:
            bool: True if sensor is detected
        Notes:
            - ISR-safe: No
            - Detects by attempting to read sensor ID
        """
        try:
            self.read_id()
            return True
        except SHTC3Error:
            return False

    def set_delta(self, delta_temp: float = 0.0, delta_hum: float = 0.0) -> None:
        """
        设置温湿度补偿值
        Args:
            delta_temp (float): 温度补偿值（℃）
            delta_hum (float): 湿度补偿值（%）
        Raises:
            ValueError: 参数类型错误
        Notes:
            - ISR-safe: 否
            - 补偿值直接累加到原始测量结果
        ==========================================
        Set temperature and humidity offsets.
        Args:
            delta_temp (float): Temperature offset in Celsius
            delta_hum (float): Humidity offset in percent
        Raises:
            ValueError: Invalid parameter type
        Notes:
            - ISR-safe: No
            - Offset is added directly to raw measurement result
        """
        # 参数校验
        if isinstance(delta_temp, (int, float)) is False:
            raise ValueError("delta_temp must be int or float, got %s" % type(delta_temp))
        if isinstance(delta_hum, (int, float)) is False:
            raise ValueError("delta_hum must be int or float, got %s" % type(delta_hum))

        self._delta_temp = delta_temp
        self._delta_hum = delta_hum

    def wakeup(self) -> None:
        """
        唤醒传感器（从休眠模式）
        Notes:
            - ISR-safe: 否
            - 发送唤醒命令后需等待 240μs
        ==========================================
        Wake up sensor from sleep mode.
        Notes:
            - ISR-safe: No
            - 240μs delay required after wakeup command
        """
        self._log("waking up")
        self._write_cmd(SHTC3.WAKEUP_CMD)
        time.sleep_us(SHTC3.WAKEUP_DELAY_US)

    def sleep(self) -> None:
        """
        使传感器进入休眠模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Put sensor into sleep mode.
        Notes:
            - ISR-safe: No
        """
        self._log("going to sleep")
        self._write_cmd(SHTC3.SLEEP_CMD)

    def reset(self) -> None:
        """
        复位传感器
        Notes:
            - ISR-safe: 否
            - 复位前先唤醒，复位后等待 1ms
        ==========================================
        Reset the sensor.
        Notes:
            - ISR-safe: No
            - Wake before reset, 1ms delay after reset
        """
        self._log("resetting")
        self.wakeup()
        self._write_cmd(SHTC3.RESET_CMD)
        time.sleep_ms(SHTC3.RESET_DELAY_MS)

    def read_id(self) -> int:
        """
        读取传感器 ID
        Returns:
            int: 传感器 ID（16 位）
        Raises:
            SHTC3Error: I2C 通信失败或 CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor identification number.
        Returns:
            int: Sensor ID (16-bit)
        Raises:
            SHTC3Error: I2C communication failure or CRC error
        Notes:
            - ISR-safe: No
        """
        self._log("reading ID")
        self.wakeup()
        # 读取 3 字节响应：ID_MSB, ID_LSB, CRC
        data = self._send_cmd(SHTC3.READ_ID_CMD, response_size=3, read_delay_ms=SHTC3.READ_ID_DELAY_MS)
        self.sleep()
        return (data[0] << 8) | data[1]

    def measure(self, raw: bool = False, low_power: bool = False, rh_first: bool = False) -> tuple:
        """
        测量温湿度
        Args:
            raw (bool): True 返回原始 6 字节数据，False 返回转换后的温湿度值
            low_power (bool): True 使用低功耗模式
            rh_first (bool): True 湿度优先，False 温度优先
        Returns:
            tuple: (temperature_celsius, relative_humidity_percent) 当 raw=False
                   bytearray: 6 字节原始数据 当 raw=True
        Raises:
            SHTC3Error: I2C 通信失败或 CRC 校验失败
        Notes:
            - ISR-safe: 否
            - 正常模式测量耗时约 13ms，低功耗模式约 1ms
            - 湿度值自动钳位到 0-100% 范围
        ==========================================
        Measure temperature and humidity.
        Args:
            raw (bool): If True return raw 6-byte response
            low_power (bool): If True use low-power mode
            rh_first (bool): If True humidity-first, else temperature-first
        Returns:
            tuple: (temperature_celsius, relative_humidity_percent) when raw=False
                   bytearray: 6-byte raw sensor response when raw=True
        Raises:
            SHTC3Error: I2C communication failure or CRC error
        Notes:
            - ISR-safe: No
            - Normal mode takes ~13ms, low-power ~1ms
            - Humidity is clamped to 0-100%
        """
        if isinstance(raw, bool) is False:
            raise ValueError("raw must be bool")
        if isinstance(low_power, bool) is False:
            raise ValueError("low_power must be bool")
        if isinstance(rh_first, bool) is False:
            raise ValueError("rh_first must be bool")
        # 根据模式和优先级选择测量命令和延时
        if low_power:
            cmd = SHTC3.MEASURE_LOW_POWER_RH_FIRST_CMD if rh_first else SHTC3.MEASURE_LOW_POWER_T_FIRST_CMD
            delay_ms = SHTC3.LOW_POWER_MEASURE_DELAY_MS
        else:
            cmd = SHTC3.MEASURE_NORMAL_RH_FIRST_CMD if rh_first else SHTC3.MEASURE_NORMAL_T_FIRST_CMD
            delay_ms = SHTC3.NORMAL_MEASURE_DELAY_MS

        self.wakeup()
        # 发送测量命令并读取 6 字节响应（T_MSB, T_LSB, T_CRC, RH_MSB, RH_LSB, RH_CRC）
        data = self._send_cmd(cmd, response_size=6, read_delay_ms=delay_ms)
        self.sleep()

        if raw:
            return data

        # 根据测量模式解析温湿度原始值
        if rh_first:
            raw_rh = (data[0] << 8) | data[1]
            raw_temp = (data[3] << 8) | data[4]
        else:
            raw_temp = (data[0] << 8) | data[1]
            raw_rh = (data[3] << 8) | data[4]

        # 转换为实际温湿度值（Sensirion 官方公式）
        temperature = SHTC3.TEMP_MIN_C + (SHTC3.TEMP_SCALE * raw_temp / SHTC3.RAW_MAX) + self._delta_temp
        humidity = (SHTC3.HUM_SCALE * raw_rh / SHTC3.RAW_MAX) + self._delta_hum
        # 湿度值钳位到 0-100%
        humidity = min(100, max(0, humidity))
        return temperature, humidity

    def measure_int(self, low_power: bool = False) -> tuple:
        """
        测量温湿度，返回整数和小数分离的值
        Args:
            low_power (bool): True 使用低功耗模式
        Returns:
            tuple: (t_int, t_dec, h_int, h_dec)
                   t_int: 温度整数部分
                   t_dec: 温度小数部分（×100）
                   h_int: 湿度整数部分
                   h_dec: 湿度小数部分（×100）
        Raises:
            SHTC3Error: I2C 通信失败或 CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Measure temperature and humidity with separated integer and decimal parts.
        Args:
            low_power (bool): If True use low-power mode
        Returns:
            tuple: (t_int, t_dec, h_int, h_dec)
                   t_int: Temperature integer part
                   t_dec: Temperature decimal part (×100)
                   h_int: Humidity integer part
                   h_dec: Humidity decimal part (×100)
        Raises:
            SHTC3Error: I2C communication failure or CRC error
        Notes:
            - ISR-safe: No
        """
        if isinstance(low_power, bool) is False:
            raise ValueError("low_power must be bool")
        temperature, humidity = self.measure(low_power=low_power)
        # 分离整数和小数部分
        t_int = int(temperature)
        t_dec = int(abs(temperature - t_int) * 100)
        h_int = int(humidity)
        h_dec = int((humidity - h_int) * 100)
        return t_int, t_dec, h_int, h_dec

    def deinit(self) -> None:
        """
        释放传感器资源
        Notes:
            - ISR-safe: 否
            - 使传感器进入休眠模式以降低功耗
        ==========================================
        Release sensor resources.
        Notes:
            - ISR-safe: No
            - Puts sensor into sleep mode to reduce power consumption
        """
        self._log("deinitializing")
        try:
            self.sleep()
        except SHTC3Error:
            pass

    def _write_cmd(self, cmd: bytes) -> None:
        """
        向传感器写入命令（I2C 底层操作）
        Args:
            cmd (bytes): 命令字节序列
        Raises:
            SHTC3Error: I2C 总线通信失败
        ==========================================
        Write command to sensor (low-level I2C operation).
        Args:
            cmd (bytes): Command byte sequence
        Raises:
            SHTC3Error: I2C bus communication failure
        """
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFFFF:
            raise ValueError("cmd must be an integer command value")
        try:
            self._i2c.writeto(self._addr, cmd)
        except OSError as e:
            raise SHTC3Error(SHTC3Error.BUS_ERROR) from e

    def _send_cmd(self, cmd: bytes, response_size: int = 6, read_delay_ms: int = 13) -> bytearray:
        """
        发送命令并读取响应，含 CRC 校验
        Args:
            cmd (bytes): 命令字节序列
            response_size (int): 预期的响应字节数
            read_delay_ms (int): 命令发送后等待时间（毫秒）
        Returns:
            bytearray: 传感器响应数据
        Raises:
            SHTC3Error: I2C 通信失败、返回空数据或 CRC 校验失败
        ==========================================
        Send command and read response with CRC verification.
        Args:
            cmd (bytes): Command byte sequence
            response_size (int): Expected response size in bytes
            read_delay_ms (int): Wait time after command in milliseconds
        Returns:
            bytearray: Sensor response data
        Raises:
            SHTC3Error: I2C error, empty data, or CRC mismatch
        """
        self._write_cmd(cmd)
        time.sleep_ms(read_delay_ms)

        try:
            data = self._i2c.readfrom(self._addr, response_size)
        except OSError as e:
            raise SHTC3Error(SHTC3Error.BUS_ERROR) from e

        # 检查是否收到全零数据（传感器未就绪或通信异常）
        if data == bytearray(response_size):
            raise SHTC3Error(SHTC3Error.DATA_ERROR)

        # 逐块校验 CRC（每 3 字节一组：MSB, LSB, CRC）
        for index in range(response_size // 3):
            chunk = data[index * 3 : (index + 1) * 3]
            if not self._check_crc(chunk):
                raise SHTC3Error(SHTC3Error.CRC_ERROR)

        return data

    def _check_crc(self, data: bytes) -> bool:
        """
        校验 CRC-8
        Args:
            data (bytes): 待校验数据（2 字节数据 + 1 字节 CRC）
        Returns:
            bool: CRC 校验通过返回 True
        ==========================================
        Verify CRC-8 checksum.
        Args:
            data (bytes): Data to verify (2 bytes data + 1 byte CRC)
        Returns:
            bool: True if CRC matches
        """
        if isinstance(data, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("data must be a buffer or sequence")
        crc = _crc8(data[:2], SHTC3.POLYNOMIAL)
        return crc == data[2]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not hasattr(exc_type, "__name__"):
            raise ValueError("exc_type must be an exception type or None")
        self.deinit()
        return False


class SHTC3Error(Exception):
    """SHTC3 传感器异常类 / SHTC3 sensor exception class"""

    BUS_ERROR = micropython.const(0x01)
    DATA_ERROR = micropython.const(0x02)
    CRC_ERROR = micropython.const(0x03)

    def __init__(self, error_code: int = None) -> None:
        """
        初始化异常实例
        Args:
            error_code (int): 错误码
        ==========================================
        Initialize exception instance.
        Args:
            error_code (int): Error code
        """
        if not isinstance(error_code, int) or not 0 <= error_code <= 0xFFFF:
            raise ValueError("error_code must be an integer command value")
        self.error_code = error_code
        super().__init__(self._get_message())

    def _get_message(self) -> str:
        """获取错误描述信息 / Get error description"""
        if self.error_code == SHTC3Error.BUS_ERROR:
            return "I2C bus error"
        if self.error_code == SHTC3Error.DATA_ERROR:
            return "Sensor returned empty data"
        if self.error_code == SHTC3Error.CRC_ERROR:
            return "CRC check failed"
        return "Unknown SHTC3 error"


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
