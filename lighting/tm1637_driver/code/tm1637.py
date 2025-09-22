# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/01/16 10:21
# @Author  : 侯钧瀚
# @File    : tm1637.py
# @Description : tm1637驱动for micropython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入MicroPython内置模块
from micropython import const
# 导入Pin类以控制GPIO引脚
from machine import Pin
# 导入时间相关函数
from time import sleep_us, sleep_ms

# ======================================== 全局变量 ============================================

TM1637_CMD1 = const(64)  # 0x40 数据命令
TM1637_CMD2 = const(192) # 0xC0 地址命令
TM1637_CMD3 = const(128) # 0x80 显示控制命令
TM1637_DSP_ON = const(8) # 0x08 开启显示
TM1637_DELAY = const(10) # 10us 时钟延迟
TM1637_MSB = const(128)  # MSB（最高有效位）表示小数点或冒号

# 0-9, a-z, blank, dash, star
# 这是七段显示的编码表，包含了数字、字母、空格、破折号、星号等字符
_SEGMENTS = bytearray(b'\x3F\x06\x5B\x4F\x66\x6D\x7D\x07\x7F\x6F\x77\x7C\x39\x5E\x79\x71\x3D\x76\x06\x1E\x76\x38\x55\x54\x3F\x73\x67\x50\x6D\x78\x3E\x1C\x2A\x76\x6E\x5B\x00\x40\x63')

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TM1637(object):
    """
       基于 TM1637 的四位七段数码管显示驱动类（MicroPython）。
       提供位/段写入、亮度调节、数字/字符串/十六进制/温度显示与滚动显示等高层 API；
       底层严格按 TM1637 时序实现（START/STOP、自动地址递增、显示控制）。

       Attributes:
           clk (Pin): 时钟引脚（输出模式）
           dio (Pin): 数据引脚（输出模式）
           _brightness (int): 当前亮度（0–7）

       Methods:
           __init__(clk, dio, brightness=7): 初始化引脚与默认亮度；写入数据与显示控制命令以启用显示。
           brightness(val): 设置并应用亮度（0–7）；越大越亮；非法值抛 `ValueError`。
           write(segments, pos=0): 从给定起始位写入原始段码（自动地址递增）；pos 超界抛 `ValueError`。
           encode_digit(digit): 将 0–9 编码为七段段码；返回单字节。
           encode_string(string): 将字符串（≤4 字符）批量编码为段码数组。
           encode_char(char): 编码单字符（0–9、a–z/A–Z、空格、破折号、星号）；不支持则抛 `ValueError`。
           hex(val): 以 4 位十六进制显示（小写）。
           number(num): 显示整数（-999..9999），自动裁剪到范围。
           numbers(num1, num2, colon=True): 显示两个 2 位整数（-9..99），可选显示冒号。
           temperature(num): 显示温度（-9..99），越界显示 “lo/hi”，并追加 ℃ 符号。
           show(string, colon=False): 直接显示字符串（≤4），可选点亮冒号位。
           scroll(string, delay=250): 左移滚动显示字符串；`delay` 为步进毫秒。

       Notes:
           - 使用 TM1637 的时序控制，避免在 ISR 或中断上下文中直接操作。
           - 显示亮度范围为 0–7，设置过高可能导致功耗增加。
           - 本类设计用于支持常见的 4 位显示模块，并支持可选冒号。

       ==========================================

       TM1637-based driver for 4-digit 7-segment displays (MicroPython).
       Provides high-level APIs for segment writes, brightness control, numeric/string/hex/temperature
       rendering, and text scrolling, while implementing low-level TM1637 timing
       (START/STOP, auto address increment, display control).

       Attributes:
           clk (Pin): Clock pin (output).
           dio (Pin): Data pin (output).
           _brightness (int): Current brightness level (0–7).

       Methods:
           __init__(clk, dio, brightness=7): Initialize pins/brightness and send init commands.
           brightness(val): Set and apply display brightness in [0..7]; out-of-range values raise `ValueError`.
           write(segments, pos=0): Write raw segment bytes starting at position; validates `pos`.
           encode_digit(digit): Encode a decimal digit (0–9) to a segment byte.
           encode_string(string): Encode a short string (≤4 chars) into segment bytes.
           encode_char(char): Encode a single char; unsupported chars raise `ValueError`.
           hex(val): Display a 16-bit value as 4-digit hex (lowercase).
           number(num): Display an integer within [-999, 9999] (clamped).
           numbers(num1, num2, colon=True): Display two 2-digit integers with optional colon.
           temperature(num): Show temperature value with ℃ indicator and out-of-range handling.
           show(string, colon=False): Show a short string with optional colon.
           scroll(string, delay=250): Scroll text left with step delay (ms).

       Notes:
           - Operates with TM1637 timing control; avoid direct calls from ISR or interrupt contexts.
           - Brightness range is 0–7; excessive settings may increase power consumption.
           - Designed for common 4-digit displays with optional colon support.
   """

    def __init__(self, clk, dio, brightness=7):
        """
        初始化 TM1637 显示模块。

        Args:
            clk (Pin): 时钟引脚
            dio (Pin): 数据引脚
            brightness (int): 显示亮度，范围 0-7

        Raises:
            ValueError: 如果亮度不在有效范围内

        ==========================================

        Initialize TM1637 display module.

        Args:
            clk (Pin): Clock pin
            dio (Pin): Data pin
            brightness (int): Display brightness, range from 0 to 7

        Raises:
            ValueError: If brightness is out of range
        """
        self.clk = clk
        self.dio = dio
        if not 0 <= brightness <= 7:
            raise ValueError("Brightness out of range")
        self._brightness = brightness
        self.clk.init(Pin.OUT, value=0)
        self.dio.init(Pin.OUT, value=0)
        sleep_us(TM1637_DELAY)
        self._write_data_cmd()
        self._write_dsp_ctrl()

    def _start(self):
        """
        启动信号，准备数据传输。

        ==========================================

        Start signal to prepare for data transfer.
        """
        self.dio(0)
        sleep_us(TM1637_DELAY)
        self.clk(0)
        sleep_us(TM1637_DELAY)

    def _stop(self):
        """
        停止信号，结束数据传输。

        ==========================================

        Stop signal to end data transfer.
        """
        self.dio(0)
        sleep_us(TM1637_DELAY)
        self.clk(1)
        sleep_us(TM1637_DELAY)
        self.dio(1)

    def _write_data_cmd(self):
        """
        发送数据命令，启用自动地址递增模式。

        ==========================================

        Send data command to enable auto address increment mode.
        """
        self._start()
        self._write_byte(TM1637_CMD1)
        self._stop()

    def _write_dsp_ctrl(self):
        """
        发送显示控制命令，开启显示并设置亮度。

        ==========================================

        Send display control command to turn on display and set brightness.
        """
        self._start()
        self._write_byte(TM1637_CMD3 | TM1637_DSP_ON | self._brightness)
        self._stop()

    def _write_byte(self, b):
        """
        向显示器写入一个字节。

        Args:
            b (int): 要写入的字节数据

        ==========================================

        Write a byte of data to the display.

        Args:
            b (int): Byte data to write
        """
        for i in range(8):
            self.dio((b >> i) & 1)
            sleep_us(TM1637_DELAY)
            self.clk(1)
            sleep_us(TM1637_DELAY)
            self.clk(0)
            sleep_us(TM1637_DELAY)
        self.clk(0)
        sleep_us(TM1637_DELAY)
        self.clk(1)
        sleep_us(TM1637_DELAY)
        self.clk(0)
        sleep_us(TM1637_DELAY)

    def brightness(self, val):
        """
        设置显示亮度。

        Args:
            val (int, optional): 亮度值，范围 0-7

        Returns:
            int: 当前亮度值

        Raises:
            ValueError: 如果亮度不在有效范围内

        ==========================================

        Set display brightness.

        Args:
            val (int, optional): Brightness value, range from 0 to 7

        Returns:
            int: Current brightness value

        Raises:
            ValueError: If brightness is out of range
        """
        if not 0 <= val <= 7:
            raise ValueError("Brightness out of range")

        self._brightness = val
        self._write_data_cmd()
        self._write_dsp_ctrl()

    def write(self, segments, pos=0):
        """
        从指定位置开始写入多个 7 段显示字符。

        Args:
            segments (list): 7 段显示字符的字节列表
            pos (int): 起始位置，0-5

        Raises:
            ValueError: 如果位置超出范围

        ==========================================

        Write multiple 7-segment display characters starting from the specified position.

        Args:
            segments (list): List of 7-segment characters in byte format
            pos (int): Starting position, 0-5

        Raises:
            ValueError: If position is out of range
        """
        if not 0 <= pos <= 5:
            raise ValueError("Position out of range")
        self._write_data_cmd()
        self._start()

        self._write_byte(TM1637_CMD2 | pos)
        for seg in segments:
            self._write_byte(seg)
        self._stop()
        self._write_dsp_ctrl()

    def encode_digit(self, digit):
        """
        将数字字符转换为对应的七段显示编码。

        Args:
            digit (int): 数字字符 0-9

        Returns:
            byte: 对应的七段显示编码

        ==========================================

        Convert a digit character to corresponding 7-segment display encoding.

        Args:
            digit (int): Digit character 0-9

        Returns:
            byte: Corresponding 7-segment display encoding
        """
        return _SEGMENTS[digit & 0x0f]

    def encode_string(self, string):
        """
        将字符串转换为七段显示编码。

        Args:
            string (str): 字符串，最多 4 个字符

        Returns:
            bytearray: 转换后的七段显示编码数组

        ==========================================

        Convert a string to 7-segment display encoding.

        Args:
            string (str): String, up to 4 characters

        Returns:
            bytearray: Array of converted 7-segment display encodings
        """
        segments = bytearray(len(string))
        for i in range(len(string)):
            segments[i] = self.encode_char(string[i])
        return segments

    def encode_char(self, char):
        """
        将单个字符转换为七段显示编码。

        Args:
            char (str): 字符，0-9，a-z，空格，破折号，星号

        Returns:
            byte: 对应的七段显示编码

        Raises:
            ValueError: 不支持的字符

        ==========================================

        Convert a single character to 7-segment display encoding.

        Args:
            char (str): Character, 0-9, a-z, space, dash, star

        Returns:
            byte: Corresponding 7-segment display encoding

        Raises:
            ValueError: Unsupported characters
        """
        o = ord(char)
        # 空格
        if o == 32:
            return _SEGMENTS[36]
        if o == 42:
        # 星号
            return _SEGMENTS[38]
        if o == 45:
        # 破折号
            return _SEGMENTS[37]
        # 大写字母 A-Z
        if o >= 65 and o <= 90:
            return _SEGMENTS[o-55]
        # 小写字母 a-z
        if o >= 97 and o <= 122:
            return _SEGMENTS[o-87]
        # 数字 0-9
        if o >= 48 and o <= 57:
            return _SEGMENTS[o-48]
        raise ValueError("Character out of range: {:d} '{:s}'".format(o, chr(o)))

    def hex(self, val):
        """
        显示十六进制数值。

        Args:
            val (int): 十六进制数值

        ==========================================

        Display hexadecimal value.

        Args:
            val (int): Hexadecimal value
        """
        string = '{:04x}'.format(val & 0xffff)
        self.write(self.encode_string(string))

    def number(self, num):
        """
        显示数字值，范围从 -999 到 9999。

        Args:
            num (int): 数字值

        ==========================================

        Display numeric value, range from -999 to 9999.

        Args:
            num (int): Numeric value
        """
        num = max(-999, min(num, 9999))
        string = '{0: >4d}'.format(num)
        self.write(self.encode_string(string))

    def numbers(self, num1, num2, colon=True):
        """
        显示两个数字值，范围从 -9 到 99，用冒号分隔。

        Args:
            num1 (int): 第一个数字值
            num2 (int): 第二个数字值
            colon (bool): 是否显示冒号

        ==========================================

        Display two numeric values, range from -9 to 99, separated by a colon.

        Args:
            num1 (int): First numeric value
            num2 (int): Second numeric value
            colon (bool): Whether to display colon
        """
        num1 = max(-9, min(num1, 99))
        num2 = max(-9, min(num2, 99))
        segments = self.encode_string('{0:0>2d}{1:0>2d}'.format(num1, num2))
        if colon:
            segments[1] |= 0x80 # 显示冒号
        self.write(segments)

    def temperature(self, num):
        """
        显示温度值，范围从 -9 到 99。

        Args:
            num (int): 温度值

        ==========================================

        Display temperature value, range from -9 to 99.

        Args:
            num (int): Temperature value
        """
        if num < -9:
            self.show('lo') # 显示 "低温"
        elif num > 99:
            self.show('hi') # 显示 "高温"
        else:
            string = '{0: >2d}'.format(num)
            self.write(self.encode_string(string))
        self.write([_SEGMENTS[38], _SEGMENTS[12]], 2) # 显示摄氏度符号

    def show(self, string, colon=False):
        """
        显示字符串，最多 4 个字符。

        Args:
            string (str): 显示的字符串
            colon (bool): 是否显示冒号

        ==========================================

        Show string, up to 4 characters.

        Args:
            string (str): String to display
            colon (bool): Whether to display colon
        """
        segments = self.encode_string(string)
        if len(segments) > 1 and colon:
            segments[1] |= 128
        self.write(segments[:4])

    def scroll(self, string, delay=250):
        """
        滚动显示字符串。

        Args:
            string (str): 要滚动显示的字符串
            delay (int): 每次滚动的延迟时间（毫秒）

        ==========================================

        Scroll string on the display.

        Args:
            string (str): String to scroll
            delay (int): Delay time for each scroll (ms)
        """
        segments = string if isinstance(string, list) else self.encode_string(string)
        data = [0] * 8
        data[4:0] = list(segments)
        for i in range(len(segments) + 5):
            self.write(data[0+i:4+i])
            sleep_ms(delay)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================