# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/26 14:13
# @Author  : 2black0
# @File    : sht11.py
# @Description : SHT11 温湿度传感器驱动（GPIO 位拆协议）
# @License : MIT

__version__ = "1.0.0"
__author__ = "2black0"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

from machine import Pin
from micropython import const
import utime


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# SHT1x 协议 CRC-8 查找表（256 字节）
_CRC_TABLE = [
    0,
    49,
    98,
    83,
    196,
    245,
    166,
    151,
    185,
    136,
    219,
    234,
    125,
    76,
    31,
    46,
    67,
    114,
    33,
    16,
    135,
    182,
    229,
    212,
    250,
    203,
    152,
    169,
    62,
    15,
    92,
    109,
    134,
    183,
    228,
    213,
    66,
    115,
    32,
    17,
    63,
    14,
    93,
    108,
    251,
    202,
    153,
    168,
    197,
    244,
    167,
    150,
    1,
    48,
    99,
    82,
    124,
    77,
    30,
    47,
    184,
    137,
    218,
    235,
    61,
    12,
    95,
    110,
    249,
    200,
    155,
    170,
    132,
    181,
    230,
    215,
    64,
    113,
    34,
    19,
    126,
    79,
    28,
    45,
    186,
    139,
    216,
    233,
    199,
    246,
    165,
    148,
    3,
    50,
    97,
    80,
    187,
    138,
    217,
    232,
    127,
    78,
    29,
    44,
    2,
    51,
    96,
    81,
    198,
    247,
    164,
    149,
    248,
    201,
    154,
    171,
    60,
    13,
    94,
    111,
    65,
    112,
    35,
    18,
    133,
    180,
    231,
    214,
    122,
    75,
    24,
    41,
    190,
    143,
    220,
    237,
    195,
    242,
    161,
    144,
    7,
    54,
    101,
    84,
    57,
    8,
    91,
    106,
    253,
    204,
    159,
    174,
    128,
    177,
    226,
    211,
    68,
    117,
    38,
    23,
    252,
    205,
    158,
    175,
    56,
    9,
    90,
    107,
    69,
    116,
    39,
    22,
    129,
    176,
    227,
    210,
    191,
    142,
    221,
    236,
    123,
    74,
    25,
    40,
    6,
    55,
    100,
    85,
    194,
    243,
    160,
    145,
    71,
    118,
    37,
    20,
    131,
    178,
    225,
    208,
    254,
    207,
    156,
    173,
    58,
    11,
    88,
    105,
    4,
    53,
    102,
    87,
    192,
    241,
    162,
    147,
    189,
    140,
    223,
    238,
    121,
    72,
    27,
    42,
    193,
    240,
    163,
    146,
    5,
    52,
    103,
    86,
    120,
    73,
    26,
    43,
    188,
    141,
    222,
    239,
    130,
    179,
    224,
    209,
    70,
    119,
    36,
    21,
    59,
    10,
    89,
    104,
    255,
    206,
    157,
    172,
]


class SHT11Error(Exception):
    """SHT11 驱动库通用异常基类 / Base exception for SHT11 driver."""

    pass


class SHT11AckError(SHT11Error):
    """SHT11 ACK 通信失败异常 / Raised when sensor ACK check fails."""

    pass


class SHT11CRCError(SHT11Error):
    """SHT11 CRC 校验失败异常 / Raised when CRC validation fails."""

    pass


def _calc_crc(command: int, msb: int, lsb: int) -> int:
    """
    计算 SHT1x 协议 CRC-8 校验值（位反转输出）
    Args:
        command: 命令字节
        msb: 数据高字节
        lsb: 数据低字节（仅验证命令+MSB 时传 None）
    Returns:
        int: LSB-first 反转后的 CRC-8 值
    ==========================================
    Calculate SHT1x protocol CRC-8 with bit-reversed output.
    Args:
        command: Command byte
        msb: Data MSB
        lsb: Data LSB (pass None when only validating command+MSB)
    Returns:
        int: Bit-reversed CRC-8 value (LSB-first)
    """
    # 从查找表取值并异或
    crc = _CRC_TABLE[command]
    crc ^= msb
    crc = _CRC_TABLE[crc]
    if lsb is not None:
        crc ^= lsb
        crc = _CRC_TABLE[crc]
    # SHT1x 协议要求 CRC 位反转（LSB-first 输出）
    reversed_crc = 0
    for pos in range(8):
        if crc & (1 << pos):
            reversed_crc |= 1 << (7 - pos)
    return reversed_crc


# ======================================== 自定义类 ============================================


class SHT11:
    """
    SHT11 温湿度传感器驱动类（GPIO 位拆协议）
    Attributes:
        _sck (Pin): 时钟引脚
        _data (Pin): 数据引脚（开漏模式）
        _debug (bool): 调试日志开关
    Methods:
        temperature(): 读取温度（℃）
        humidity(temperature=25): 读取相对湿度（%RH）
        read_register(): 读取状态寄存器
        deinit(): 释放引脚资源
    Notes:
        - 依赖外部传入 Pin 实例，不在类内创建引脚对象
        - 通信时序基于 10µs 时钟周期，不可随意调整
    ==========================================
    SHT11 temperature and humidity sensor driver (GPIO bit-bang protocol).
    Attributes:
        _sck (Pin): Clock pin
        _data (Pin): Data pin (open-drain mode)
        _debug (bool): Debug log switch
    Methods:
        temperature(): Read temperature in Celsius
        humidity(temperature=25): Read relative humidity in %RH
        read_register(): Read status register
        deinit(): Release pin resources
    Notes:
        - Requires externally provided Pin instances
        - Communication timing based on 10µs clock period
    """

    # 类级常量 / Class-level constants
    MEASURE_T = const(0b00000011)
    MEASURE_RH = const(0b00000101)
    SOFT_RESET = const(0b00011110)
    READ_STATUS_REGISTER = const(0b00000111)
    WRITE_STATUS_REGISTER = const(0b00000110)
    CLOCK_TIME_US = const(10)

    __slots__ = ("_sck", "_data", "_debug")

    def __init__(self, sck: Pin, data: Pin, debug: bool = False) -> None:
        """
        初始化 SHT11 传感器驱动
        Args:
            sck (Pin): 时钟引脚（需已初始化为输出模式）
            data (Pin): 数据引脚（需已初始化为开漏模式）
            debug (bool): 是否开启调试日志
        Returns:
            None
        Raises:
            ValueError: 参数类型错误
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize SHT11 sensor driver.
        Args:
            sck (Pin): Clock pin (should be pre-configured as output)
            data (Pin): Data pin (should be pre-configured as open-drain)
            debug (bool): Enable debug logging
        Returns:
            None
        Raises:
            ValueError: Invalid parameter type
        Notes:
            - ISR-safe: No
        """
        # 参数校验
        if isinstance(sck, Pin) is False:
            raise ValueError("sck must be a Pin instance, got %s" % type(sck))
        if isinstance(data, Pin) is False:
            raise ValueError("data must be a Pin instance, got %s" % type(data))
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._sck = sck
        self._data = data
        self._debug = debug

        # 初始化引脚模式
        self._sck.init(Pin.OUT, Pin.PULL_UP)
        self._data.init(Pin.OPEN_DRAIN, Pin.PULL_UP)

    def _log(self, msg: str) -> None:
        """输出调试日志 / Emit debug log."""
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")

        if self._debug:
            print("[SHT11] %s" % msg)

    # ============================================================
    # 公共方法 / Public methods
    # ============================================================

    def temperature(self) -> float:
        """
        读取温度值
        Args:
            无
        Returns:
            float: 温度值（℃）
        Raises:
            SHT11AckError: ACK 通信失败
            SHT11CRCError: CRC 校验失败
        Notes:
            - ISR-safe: 否
            - 副作用：持有 GPIO 约 330ms
        ==========================================
        Read temperature value.
        Args:
            None
        Returns:
            float: Temperature in Celsius
        Raises:
            SHT11AckError: ACK communication failed
            SHT11CRCError: CRC validation failed
        Notes:
            - ISR-safe: No
            - Side effect: holds GPIO for ~330ms
        """
        # 重新确保引脚模式正确
        self._sck.init(Pin.OUT, Pin.PULL_UP)
        self._data.init(Pin.OPEN_DRAIN, Pin.PULL_UP)
        # 发送测温命令并读取原始值
        readout = self._send_command(self.MEASURE_T)
        # SHT11 温度转换公式：(SO_T - 3965) / 100
        return (readout - 3965) / 100.0

    def humidity(self, temperature: float = 25) -> float:
        """
        读取相对湿度值（含温度补偿）
        Args:
            temperature (float): 当前温度（℃），默认 25℃，用于温度补偿
        Returns:
            float: 相对湿度（%RH），上限 100%
        Raises:
            SHT11AckError: ACK 通信失败
            SHT11CRCError: CRC 校验失败
        Notes:
            - ISR-safe: 否
            - 副作用：持有 GPIO 约 330ms
        ==========================================
        Read relative humidity value with temperature compensation.
        Args:
            temperature (float): Current temperature in Celsius (default 25)
        Returns:
            float: Relative humidity in %RH (capped at 100%)
        Raises:
            SHT11AckError: ACK communication failed
            SHT11CRCError: CRC validation failed
        Notes:
            - ISR-safe: No
            - Side effect: holds GPIO for ~330ms
        """
        if isinstance(temperature, (int, float)) is False:
            raise ValueError("temperature must be int or float")

        # 重新确保引脚模式正确
        self._sck.init(Pin.OUT, Pin.PULL_UP)
        self._data.init(Pin.OPEN_DRAIN, Pin.PULL_UP)
        # 发送测湿命令并读取原始值
        readout = self._send_command(self.MEASURE_RH)
        # SHT11 湿度转换公式（Sensirion 官方公式）
        humidity = -2.0468 + 0.0367 * readout - 1.5955e-6 * readout**2
        # 非 25℃ 时进行温度补偿
        if temperature != 25:
            humidity += (temperature - 25) * (0.01 + 8e-5 * readout)
        return min(humidity, 100)

    def read_register(self) -> int:
        """
        读取 SHT11 状态寄存器
        Args:
            无
        Returns:
            int: 状态寄存器值（8 位）
        Raises:
            SHT11AckError: ACK 通信失败
            SHT11CRCError: CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read SHT11 status register.
        Args:
            None
        Returns:
            int: Status register value (8 bits)
        Raises:
            SHT11AckError: ACK communication failed
            SHT11CRCError: CRC validation failed
        Notes:
            - ISR-safe: No
        """
        command = self.READ_STATUS_REGISTER
        # 发送传输开始序列
        self._start_transmission()
        # 写入读寄存器命令
        self._write_byte(command)
        # 释放 DATA，由传感器在第 9 个时钟输出 ACK
        self._data(True)
        # 检查 ACK（DATA 应拉低）
        self._ack_bit(False)

        # 等待传感器就绪（DATA 应为低电平）
        if self._data():
            raise SHT11AckError("sensor not ready for register read")

        # 读取寄存器值
        readout = self._read_byte()

        # CRC 校验
        crc = self._read_byte(acknowledge=False)
        computed_crc = _calc_crc(command, readout, None)
        if crc != computed_crc:
            self._log("CRC mismatch: got=%d, computed=%d" % (crc, computed_crc))
            raise SHT11CRCError("CRC check failed for register read")

        return readout

    def deinit(self) -> None:
        """
        释放引脚资源，将引脚恢复为输入模式
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 调用后需重新创建实例才能恢复通信
        ==========================================
        Release pin resources, restore pins to input mode.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - A new instance is required to resume communication
        """
        self._sck.init(Pin.IN, Pin.PULL_UP)
        self._data.init(Pin.IN, Pin.PULL_UP)

    # ============================================================
    # 私有方法 / Private methods
    # ============================================================

    def _send_command(self, command: int) -> int:
        """
        发送测量命令并读取 16 位原始数据
        Args:
            command: 命令字节
        Returns:
            int: 16 位原始测量值
        Raises:
            SHT11AckError: ACK 失败或传感器测量超时
            SHT11CRCError: CRC 校验失败
        """
        if not isinstance(command, int) or not 0 <= command <= 0xFF:
            raise ValueError("command must be an 8-bit integer")

        # 发送传输开始序列
        self._start_transmission()
        # 写入命令字节
        self._write_byte(command)
        # 释放 DATA，由传感器在第 9 个时钟输出 ACK
        self._data(True)
        # 检查传感器 ACK（DATA 应拉低）
        self._ack_bit(False)
        # 等待测量完成（典型值 320ms，加 10ms 余量）
        utime.sleep_ms(330)

        # 传感器就绪检查（DATA 应为低电平）
        if self._data():
            raise SHT11AckError("sensor measurement timeout")

        # 读取高字节（MSB）
        msb = self._read_byte()
        # 读取低字节（LSB）
        lsb = self._read_byte()
        readout = (msb << 8) + lsb

        # CRC 校验
        crc = self._read_byte(acknowledge=False)
        computed_crc = _calc_crc(command, msb, lsb)
        if crc != computed_crc:
            self._log("CRC mismatch: got=%d, computed=%d" % (crc, computed_crc))
            raise SHT11CRCError("CRC check failed for measurement")

        return readout

    def _read_byte(self, acknowledge: bool = True) -> int:
        """
        从传感器读取一个字节（MSB-first）
        Args:
            acknowledge (bool): 是否在读取后发送 ACK
        Returns:
            int: 8 位字节值
        """
        if isinstance(acknowledge, bool) is False:
            raise ValueError("acknowledge must be bool")

        byte = 0
        # MSB-first 逐位读取
        for pos in range(8, 0, -1):
            bit = self._read_bit()
            byte |= bit << (pos - 1)

        # 数据字节后发送 ACK，CRC 字节后释放 DATA 发送 NACK
        if acknowledge:
            self._data(False)
            self._ack_bit(False)
        else:
            self._data(True)
            self._sck(False)
            self._noop()
            self._sck(True)
            self._noop()
            self._sck(False)
            self._noop()
        self._data(True)
        return byte

    def _read_bit(self) -> int:
        """
        读取单个数据位（在 SCK 高电平期间采样）
        Returns:
            int: 0 或 1
        """
        # SCK 下降沿准备数据
        self._sck(False)
        self._noop()
        # SCK 上升沿采样 DATA
        self._sck(True)
        self._noop()
        data = self._data()
        # SCK 恢复低电平
        self._sck(False)
        self._noop()
        return data

    def _write_byte(self, byte: int) -> None:
        """
        向传感器写入一个字节（MSB-first）
        Args:
            byte: 待写入的 8 位字节
        """
        if not isinstance(byte, int) or not 0 <= byte <= 0xFF:
            raise ValueError("byte must be an 8-bit integer")

        # MSB-first 逐位写入
        for pos in range(8, 0, -1):
            bit = 1 if (byte & (1 << (pos - 1))) else 0
            self._write_bit(bit)

    def _write_bit(self, value: int) -> None:
        """
        写入单个数据位
        Args:
            value: 0 或 1
        """
        if not isinstance(value, int) or value not in (0, 1):
            raise ValueError("value must be 0 or 1")

        # SCK 低电平时设置 DATA
        self._sck(False)
        self._data(value)
        self._noop()
        # SCK 上升沿锁存数据
        self._sck(True)
        self._noop()
        # SCK 恢复低电平
        self._sck(False)
        self._noop()

    def _ack_bit(self, value: bool = True) -> None:
        """
        检查或发送 ACK 位。

        必须在第 9 个 SCK 为高电平时采样 DATA。SHT1x 会在第 9 个
        SCK 的下降沿之后释放 DATA，因此不能等 SCK 拉低后再读取。
        """
        if not isinstance(value, bool):
            raise ValueError("value must be bool")

        self._sck(False)
        self._noop()
        self._sck(True)
        self._noop()

        # ACK 在 SCK 高电平期间有效，必须在下降沿前读取。
        actual = bool(self._data())

        self._sck(False)
        self._noop()

        if actual != value:
            raise SHT11AckError("ACK check failed: expected %s, got %s" % (value, actual))

    def _start_transmission(self) -> None:
        """
        发送 SHT1x 传输开始序列（Transmission Start）
        时序：DATA↑→SCK↑→DATA↓→SCK↓→SCK↑→DATA↑→SCK↓
        """
        self._data(True)
        self._sck(True)
        self._noop()
        self._data(False)
        self._noop()
        self._sck(False)
        self._noop()
        self._sck(True)
        self._noop()
        self._data(True)
        self._noop()
        self._sck(False)
        self._noop()

    def _noop(self) -> None:
        """时钟周期延时（10µs）/ Clock cycle delay (10µs)."""
        utime.sleep_us(self.CLOCK_TIME_US)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
