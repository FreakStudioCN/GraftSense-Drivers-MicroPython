# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:52
# @Author  : mcauser
# @File    : ht16k33_seg.py
# @Description : HT16K33驱动 14段/7段4位数码管显示控制 参考自:https://github.com/mcauser/deshipu-micropython-ht16k33
# @License : MIT
__version__ = "0.1.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from ht16k33_matrix import HT16K33

# ======================================== 全局变量 ============================================

# 14段数码管字符编码表，每个字符对应两个字节的显示编码
# 覆盖ASCII 32(空格)到126(~)的字符，格式：(高字节, 低字节)
CHARS = (
    0b00000000,
    0b00000000,  # 空格
    0b01000000,
    0b00000110,  # !
    0b00000010,
    0b00100000,  # "
    0b00010010,
    0b11001110,  # #
    0b00010010,
    0b11101101,  # $
    0b00001100,
    0b00100100,  # %
    0b00100011,
    0b01011101,  # &
    0b00000100,
    0b00000000,  # '
    0b00100100,
    0b00000000,  # (
    0b00001001,
    0b00000000,  # )
    0b00111111,
    0b11000000,  # *
    0b00010010,
    0b11000000,  # +
    0b00001000,
    0b00000000,  # ,
    0b00000000,
    0b11000000,  # -
    0b00000000,
    0b00000000,  # .
    0b00001100,
    0b00000000,  # /
    0b00001100,
    0b00111111,  # 0
    0b00000000,
    0b00000110,  # 1
    0b00000000,
    0b11011011,  # 2
    0b00000000,
    0b10001111,  # 3
    0b00000000,
    0b11100110,  # 4
    0b00100000,
    0b01101001,  # 5
    0b00000000,
    0b11111101,  # 6
    0b00000000,
    0b00000111,  # 7
    0b00000000,
    0b11111111,  # 8
    0b00000000,
    0b11101111,  # 9
    0b00010010,
    0b00000000,  # :
    0b00001010,
    0b00000000,  # ;
    0b00100100,
    0b01000000,  # <
    0b00000000,
    0b11001000,  # =
    0b00001001,
    0b10000000,  # >
    0b01100000,
    0b10100011,  # ?
    0b00000010,
    0b10111011,  # @
    0b00000000,
    0b11110111,  # A
    0b00010010,
    0b10001111,  # B
    0b00000000,
    0b00111001,  # C
    0b00010010,
    0b00001111,  # D
    0b00000000,
    0b11111001,  # E
    0b00000000,
    0b01110001,  # F
    0b00000000,
    0b10111101,  # G
    0b00000000,
    0b11110110,  # H
    0b00010010,
    0b00000000,  # I
    0b00000000,
    0b00011110,  # J
    0b00100100,
    0b01110000,  # K
    0b00000000,
    0b00111000,  # L
    0b00000101,
    0b00110110,  # M
    0b00100001,
    0b00110110,  # N
    0b00000000,
    0b00111111,  # O
    0b00000000,
    0b11110011,  # P
    0b00100000,
    0b00111111,  # Q
    0b00100000,
    0b11110011,  # R
    0b00000000,
    0b11101101,  # S
    0b00010010,
    0b00000001,  # T
    0b00000000,
    0b00111110,  # U
    0b00001100,
    0b00110000,  # V
    0b00101000,
    0b00110110,  # W
    0b00101101,
    0b00000000,  # X
    0b00010101,
    0b00000000,  # Y
    0b00001100,
    0b00001001,  # Z
    0b00000000,
    0b00111001,  # [
    0b00100001,
    0b00000000,  # \
    0b00000000,
    0b00001111,  # ]
    0b00001100,
    0b00000011,  # ^
    0b00000000,
    0b00001000,  # _
    0b00000001,
    0b00000000,  # `
    0b00010000,
    0b01011000,  # a
    0b00100000,
    0b01111000,  # b
    0b00000000,
    0b11011000,  # c
    0b00001000,
    0b10001110,  # d
    0b00001000,
    0b01011000,  # e
    0b00000000,
    0b01110001,  # f
    0b00000100,
    0b10001110,  # g
    0b00010000,
    0b01110000,  # h
    0b00010000,
    0b00000000,  # i
    0b00000000,
    0b00001110,  # j
    0b00110110,
    0b00000000,  # k
    0b00000000,
    0b00110000,  # l
    0b00010000,
    0b11010100,  # m
    0b00010000,
    0b01010000,  # n
    0b00000000,
    0b11011100,  # o
    0b00000001,
    0b01110000,  # p
    0b00000100,
    0b10000110,  # q
    0b00000000,
    0b01010000,  # r
    0b00100000,
    0b10001000,  # s
    0b00000000,
    0b01111000,  # t
    0b00000000,
    0b00011100,  # u
    0b00100000,
    0b00000100,  # v
    0b00101000,
    0b00010100,  # w
    0b00101000,
    0b11000000,  # x
    0b00100000,
    0b00001100,  # y
    0b00001000,
    0b01001000,  # z
    0b00001001,
    0b01001001,  # {
    0b00010010,
    0b00000000,  # |
    0b00100100,
    0b10001001,  # }
    0b00000101,
    0b00100000,  # ~
    0b00111111,
    0b11111111,
)

# 7段数码管字符编码表，包含0-9、a-f、-等字符的显示编码
NUMBERS = (
    0x3F,  # 0
    0x06,  # 1
    0x5B,  # 2
    0x4F,  # 3
    0x66,  # 4
    0x6D,  # 5
    0x7D,  # 6
    0x07,  # 7
    0x7F,  # 8
    0x6F,  # 9
    0x77,  # a
    0x7C,  # b
    0x39,  # C
    0x5E,  # d
    0x79,  # E
    0x71,  # F
    0x40,  # -
)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Seg14x4(HT16K33):
    """
        14段4位数码管显示控制类，继承自HT16K33驱动类，支持字符显示、滚动、数字和十六进制数显示
        Attributes:
            无额外属性，继承自HT16K33基类
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            scroll: 按指定位数滚动显示内容
            put: 在指定位置显示单个字符
            push: 滚动显示并在末尾添加字符
            text: 显示指定文本内容
            number: 显示指定十进制数字
            hex: 显示指定十六进制数字

        Notes:
            1. 支持ASCII 32(空格)到126(~)范围内的字符显示
            2. 小数点显示需单独处理，会叠加在对应位置的字符编码上
            3. 数字显示超出4位（含小数点则5位）会抛出Overflow异常

    ==========================================
    14-segment 4-digit display control class, inherited from HT16K33 driver class, supports character display, scrolling, number and hexadecimal number display
    Attributes:
            No additional attributes, inherited from HT16K33 base class
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            scroll: Scroll the display content by the specified number of positions
            put: Display a single character at the specified position
            push: Scroll the display and add a character at the end
            text: Display the specified text content
            number: Display the specified decimal number
            hex: Display the specified hexadecimal number

    Notes:
            1. Supports character display in the range of ASCII 32 (space) to 126 (~)
            2. Decimal point display needs to be processed separately and will be superimposed on the character code of the corresponding position
            3. An Overflow exception will be thrown if the number display exceeds 4 digits (5 digits including decimal point)
    """

    def scroll(self, count: int = 1) -> None:
        """
                按指定位数滚动显示缓冲区内容
                Args:
                    count (int): 滚动位数，正数向右滚动，负数向左滚动，默认值为1

                Raises:
                    ValueError: count参数为None时触发
                    TypeError: count非整数类型时触发

                Notes:
                    滚动操作直接修改显示缓冲区，不会立即刷新显示


        ==========================================
        Scroll the display buffer content by the specified number of positions
        Args:
            count (int): Number of scrolling positions, positive numbers scroll to the right, negative numbers scroll to the left, default value is 1

        Raises:
            ValueError: Triggered when count parameter is None
            TypeError: Triggered when count is not integer type

        Notes:
            The scrolling operation directly modifies the display buffer and does not refresh the display immediately
        """
        # 检查count参数是否为None
        if count is None:
            raise ValueError("Scroll count cannot be None")
        # 检查count参数类型是否为整数
        if not isinstance(count, int):
            raise TypeError(f"Integer expected for scroll count, got {type(count).__name__}")

        if count >= 0:
            offset = 0
        else:
            offset = 2
        for i in range(6):
            self.buffer[i + offset] = self.buffer[i + 2 * count]

    def put(self, char: str, index: int = 0) -> None:
        """
                在指定位置显示单个字符
                Args:
                    char (str): 要显示的字符，需在ASCII 32-127范围内，长度为1
                    index (int): 显示位置索引，范围0-3，默认值为0

                Raises:
                    ValueError: char为None/空字符串/ASCII超出32-127范围，或index为None/超出0-3范围时触发
                    TypeError: char非字符串类型，或index非整数类型时触发

                Notes:
                    1. 小数点字符('.')会叠加在指定位置的现有字符编码上
                    2. 超出范围的索引或字符会被忽略


        ==========================================
        Display a single character at the specified position
        Args:
            char (str): The character to be displayed, must be in the range of ASCII 32-127, length 1
            index (int): Display position index, range 0-3, default value is 0

        Raises:
            ValueError: Triggered when char is None/empty string/ASCII out of 32-127 range, or index is None/out of 0-3 range
            TypeError: Triggered when char is not string type, or index is not integer type

        Notes:
            1. The decimal point character ('.') will be superimposed on the existing character code of the specified position
            2. Indexes or characters out of range will be ignored
        """
        # 检查char参数是否为None
        if char is None:
            raise ValueError("Display character cannot be None")
        # 检查char参数类型是否为字符串
        if not isinstance(char, str):
            raise TypeError(f"String expected for display character, got {type(char).__name__}")
        # 检查char参数长度是否为1
        if len(char) != 1:
            raise ValueError(f"Single character expected, got string of length {len(char)}")
        # 检查index参数是否为None
        if index is None:
            raise ValueError("Display index cannot be None")
        # 检查index参数类型是否为整数
        if not isinstance(index, int):
            raise TypeError(f"Integer expected for display index, got {type(index).__name__}")
        # 检查index参数取值范围（0-3）
        if not 0 <= index <= 3:
            raise ValueError(f"Display index must be between 0 and 3, got {index}")

        if not 32 <= ord(char) <= 127:
            raise ValueError(f"Character ASCII must be between 32 and 127, got {ord(char)}")

        if char == ".":
            self.buffer[index * 2 + 1] |= 0b01000000
            return
        c = ord(char) * 2 - 64
        self.buffer[index * 2] = CHARS[1 + c]
        self.buffer[index * 2 + 1] = CHARS[c]

    def push(self, char: str) -> None:
        """
                滚动显示缓冲区并在末尾添加指定字符
                Args:
                    char (str): 要添加的字符，长度为1

                Raises:
                    ValueError: char为None/空字符串时触发
                    TypeError: char非字符串类型时触发

                Notes:
                    1. 若添加的是小数点且最后一位已有小数点，先执行滚动并清空最后一位
                    2. 滚动后在最后一个位置显示新字符


        ==========================================
        Scroll the display buffer and add the specified character at the end
        Args:
            char (str): The character to be added, length 1

        Raises:
            ValueError: Triggered when char is None/empty string
            TypeError: Triggered when char is not string type

        Notes:
            1. If the added character is a decimal point and the last digit already has a decimal point, scroll first and clear the last digit
            2. Display the new character at the last position after scrolling
        """
        # 检查char参数是否为None
        if char is None:
            raise ValueError("Push character cannot be None")
        # 检查char参数类型是否为字符串
        if not isinstance(char, str):
            raise TypeError(f"String expected for push character, got {type(char).__name__}")
        # 检查char参数长度是否为1
        if len(char) != 1:
            raise ValueError(f"Single character expected for push, got string of length {len(char)}")

        if char != "." or self.buffer[7] & 0b01000000:
            self.scroll()
            self.put(" ", 3)
        self.put(char, 3)

    def text(self, text: str) -> None:
        """
                显示指定文本内容，自动处理字符滚动
                Args:
                    text (str): 要显示的文本字符串

                Raises:
                    ValueError: text参数为None时触发
                    TypeError: text非字符串类型时触发

                Notes:
                    文本会逐字符添加到显示缓冲区，超出4位的部分会自动滚动显示


        ==========================================
        Display the specified text content and automatically handle character scrolling
        Args:
            text (str): The text string to be displayed

        Raises:
            ValueError: Triggered when text parameter is None
            TypeError: Triggered when text is not string type

        Notes:
            The text will be added to the display buffer character by character, and parts exceeding 4 digits will be automatically scrolled and displayed
        """
        # 检查text参数是否为None
        if text is None:
            raise ValueError("Display text cannot be None")
        # 检查text参数类型是否为字符串
        if not isinstance(text, str):
            raise TypeError(f"String expected for display text, got {type(text).__name__}")

        for c in text:
            self.push(c)

    def number(self, number: float | int) -> None:
        """
                显示指定十进制数字
                Args:
                    number (float | int): 要显示的十进制数字（整数或浮点数）

                Raises:
                    ValueError: number为None，或转换为字符串后长度超过4位（含小数点则5位）时触发
                    TypeError: number非整数/浮点数类型时触发

                Notes:
                    1. 显示前会清空显示缓冲区
                    2. 仅显示前4位（含小数点则5位）内容


        ==========================================
        Display the specified decimal number
        Args:
            number (float | int): The decimal number (integer or float) to be displayed

        Raises:
            ValueError: Triggered when number is None, or the length of the number converted to a string exceeds 4 digits (5 digits including decimal point)
            TypeError: Triggered when number is not integer/float type

        Notes:
            1. The display buffer will be cleared before display
            2. Only the first 4 digits (5 digits including decimal point) are displayed
        """
        # 检查number参数是否为None
        if number is None:
            raise ValueError("Display number cannot be None")
        # 检查number参数类型是否为整数/浮点数
        if not isinstance(number, (int, float)):
            raise TypeError(f"Integer or float expected for display number, got {type(number).__name__}")

        s = "{:f}".format(number)
        if len(s) > 4:
            if s.find(".") > 4:
                raise ValueError("Overflow: Number exceeds 4-digit display limit")
        self.fill(False)
        places = 4
        if "." in s:
            places += 1
        self.text(s[:places])

    def hex(self, number: int) -> None:
        """
                显示指定十六进制数字
                Args:
                    number (int): 要显示的整数，会转换为十六进制字符串

                Raises:
                    ValueError: number为None，或十六进制字符串长度超过4位时触发
                    TypeError: number非整数类型时触发

                Notes:
                    1. 显示前会清空显示缓冲区
                    2. 支持0-9、a-f字符显示，字母自动转为小写


        ==========================================
        Display the specified hexadecimal number
        Args:
            number (int): The integer to be displayed, which will be converted to a hexadecimal string

        Raises:
            ValueError: Triggered when number is None, or the length of the hexadecimal string exceeds 4 digits
            TypeError: Triggered when number is not integer type

        Notes:
            1. The display buffer will be cleared before display
            2. Supports display of 0-9, a-f characters, letters are automatically converted to lowercase
        """
        # 检查number参数是否为None
        if number is None:
            raise ValueError("Hex number cannot be None")
        # 检查number参数类型是否为整数
        if not isinstance(number, int):
            raise TypeError(f"Integer expected for hex number, got {type(number).__name__}")

        s = "{:x}".format(number)
        if len(s) > 4:
            raise ValueError("Overflow: Hex number exceeds 4-digit display limit")
        self.fill(False)
        self.text(s)


class Seg7x4(Seg14x4):
    """
        7段4位数码管显示控制类，继承自Seg14x4类，适配7段数码管的显示特性
        Attributes:
            P (List[int]): 7段数码管字符在缓冲区中的位置索引，默认值为[0, 2, 6, 8]
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            scroll: 重写滚动方法，适配7段数码管的缓冲区位置
            push: 重写添加字符方法，支持冒号(:)和分号(;)的特殊显示
            put: 重写显示字符方法，适配7段数码管的编码表

        Notes:
            1. 仅支持数字、a-f、-、空格、冒号、分号等字符显示
            2. 小数点显示位为编码的最高位(0b10000000)
            3. 冒号和分号显示在缓冲区第4位，分别对应编码0x02和0x00

    ==========================================
    7-segment 4-digit display control class, inherited from Seg14x4 class, adapted to the display characteristics of 7-segment display
    Attributes:
            P (List[int]): List, position index of 7-segment display characters in the buffer, default value is [0, 2, 6, 8]
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            scroll: Override the scroll method to adapt to the buffer position of the 7-segment display
            push: Override the add character method to support special display of colon (:) and semicolon (;)
            put: Override the display character method to adapt to the encoding table of the 7-segment display

    Notes:
            1. Only supports display of numbers, a-f, -, space, colon, semicolon and other characters
            2. The decimal point display bit is the highest bit of the code (0b10000000)
            3. Colon and semicolon are displayed at the 4th position of the buffer, corresponding to codes 0x02 and 0x00 respectively
    """

    # 7段数码管字符在显示缓冲区中的位置索引
    P: list[int] = [0, 2, 6, 8]  # The positions of characters.

    def scroll(self, count: int = 1) -> None:
        """
                按指定位数滚动7段数码管显示缓冲区内容
                Args:
                    count (int): 滚动位数，正数向右滚动，负数向左滚动，默认值为1

                Raises:
                    ValueError: count参数为None时触发
                    TypeError: count非整数类型时触发

                Notes:
                    滚动操作仅针对7段数码管的有效字符位置(P列表)，适配7段显示特性


        ==========================================
        Scroll the 7-segment display buffer content by the specified number of positions
        Args:
            count (int): Number of scrolling positions, positive numbers scroll to the right, negative numbers scroll to the left, default value is 1

        Raises:
            ValueError: Triggered when count parameter is None
            TypeError: Triggered when count is not integer type

        Notes:
            The scrolling operation is only for the valid character positions (P list) of the 7-segment display, adapting to the 7-segment display characteristics
        """
        # 检查count参数是否为None
        if count is None:
            raise ValueError("Scroll count cannot be None")
        # 检查count参数类型是否为整数
        if not isinstance(count, int):
            raise TypeError(f"Integer expected for scroll count, got {type(count).__name__}")

        if count >= 0:
            offset = 0
        else:
            offset = 1
        for i in range(3):
            self.buffer[self.P[i + offset]] = self.buffer[self.P[i + count]]

    def push(self, char: str) -> None:
        """
                滚动7段数码管显示缓冲区并在末尾添加指定字符，支持冒号和分号的特殊处理
                Args:
                    char (str): 要添加的字符，长度为1

                Raises:
                    ValueError: char为None/空字符串时触发
                    TypeError: char非字符串类型时触发

                Notes:
                    1. 若字符为:或;，直接调用put方法显示，不执行滚动
                    2. 其他字符调用父类的push方法处理


        ==========================================
        Scroll the 7-segment display buffer and add the specified character at the end, supporting special processing of colon and semicolon
        Args:
            char (str): The character to be added, length 1

        Raises:
            ValueError: Triggered when char is None/empty string
            TypeError: Triggered when char is not string type

        Notes:
            1. If the character is : or ;, call the put method directly to display, without scrolling
            2. Other characters call the push method of the parent class for processing
        """
        # 检查char参数是否为None
        if char is None:
            raise ValueError("Push character cannot be None")
        # 检查char参数类型是否为字符串
        if not isinstance(char, str):
            raise TypeError(f"String expected for push character, got {type(char).__name__}")
        # 检查char参数长度是否为1
        if len(char) != 1:
            raise ValueError(f"Single character expected for push, got string of length {len(char)}")

        if char in ":;":
            self.put(char)
        else:
            super().push(char)

    def put(self, char: str, index: int = 0) -> None:
        """
                在指定位置显示适配7段数码管的字符
                Args:
                    char (str): 要显示的字符，支持0-9、a-f、-、空格、:、;、.等，长度为1
                    index (int): 显示位置索引，范围0-3，默认值为0

                Raises:
                    ValueError: char为None/空字符串，或index为None/超出0-3范围时触发
                    TypeError: char非字符串类型，或index非整数类型时触发

                Notes:
                    1. 字符会自动转为小写处理
                    2. 小数点('.')会将对应位置编码的最高位置1
                    3. 冒号(':')显示在缓冲区第4位，编码为0x02；分号(';')清空冒号显示
                    4. 不支持的字符会被忽略


        ==========================================
        Display characters adapted to 7-segment display at the specified position
        Args:
            char (str): The character to be displayed, supporting 0-9, a-f, -, space, :, ;, . etc., length 1
            index (int): Display position index, range 0-3, default value is 0

        Raises:
            ValueError: Triggered when char is None/empty string, or index is None/out of 0-3 range
            TypeError: Triggered when char is not string type, or index is not integer type

        Notes:
            1. Characters are automatically converted to lowercase for processing
            2. The decimal point ('.') will set the highest bit of the code at the corresponding position to 1
            3. Colon (':') is displayed at the 4th position of the buffer with code 0x02; semicolon (';') clears the colon display
            4. Unsupported characters will be ignored
        """
        # 检查char参数是否为None
        if char is None:
            raise ValueError("Display character cannot be None")
        # 检查char参数类型是否为字符串
        if not isinstance(char, str):
            raise TypeError(f"String expected for display character, got {type(char).__name__}")
        # 检查char参数长度是否为1
        if len(char) != 1:
            raise ValueError(f"Single character expected, got string of length {len(char)}")
        # 检查index参数是否为None
        if index is None:
            raise ValueError("Display index cannot be None")
        # 检查index参数类型是否为整数
        if not isinstance(index, int):
            raise TypeError(f"Integer expected for display index, got {type(index).__name__}")
        # 检查index参数取值范围（0-3）
        if not 0 <= index <= 3:
            raise ValueError(f"Display index must be between 0 and 3, got {index}")

        char = char.lower()
        if char == ".":
            self.buffer[self.P[index]] |= 0b10000000
            return
        elif char in "abcdef":
            c = ord(char) - 97 + 10
        elif char == "-":
            c = 16
        elif char in "0123456789":
            c = ord(char) - 48
        elif char == " ":
            c = 0x00
        elif char == ":":
            self.buffer[4] = 0x02
            return
        elif char == ";":
            self.buffer[4] = 0x00
            return
        else:
            return
        self.buffer[self.P[index]] = NUMBERS[c]


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
