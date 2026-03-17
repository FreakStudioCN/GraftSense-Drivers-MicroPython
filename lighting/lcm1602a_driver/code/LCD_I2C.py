# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午5:00
# @Author  : bhavi-thiran
# @File    : lcd_i2c.py
# @Description : I2C接口LCD1602显示屏驱动 实现显示控制、光标管理、字符输出等核心功能
# @License : MIT
__version__ = "1.0.0"
__author__ = "bhavi-thiran"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入硬件控制模块，用于I2C通信和引脚配置
import machine

# 导入时间模块，用于驱动操作中的延时控制
import time

# ======================================== 全局变量 ============================================

# LCD1602显示屏固定列数，取值16
COLUMNS = 16
# LCD1602显示屏固定行数，取值2
ROWS = 2

# 清屏指令码：清除显示屏所有内容，光标返回初始位置(0,0)
CLEARDISPLAY = 0x01

# 输入模式设置指令基础码：用于配置光标移动方向和显示移位规则
ENTRYMODESET = 0x04
# 光标左移配置位：写入字符后光标向左侧移动
ENTRYLEFT = 0x02
# 光标右移配置位：写入字符后光标向右侧移动
ENTRYRIGHT = 0x00
# 显示移位增量配置位：写入字符后整个显示内容向左移位
ENTRYSHIFTINCREMENT = 0x01
# 显示移位减量配置位：写入字符后整个显示内容向右移位
ENTRYSHIFTDECREMENT = 0x00

# 显示控制指令基础码：用于控制显示开关、光标显示、光标闪烁状态
DISPLAYCONTROL = 0x08
# 显示开启配置位：启用显示屏内容显示
DISPLAYON = 0x04
# 显示关闭配置位：关闭显示屏显示（数据仍保留）
DISPLAYOFF = 0x00
# 光标开启配置位：显示下划线样式光标
CURSORON = 0x02
# 光标关闭配置位：隐藏光标
CURSOROFF = 0x00
# 光标闪烁开启配置位：光标所在位置字符闪烁
BLINKON = 0x01
# 光标闪烁关闭配置位：停止光标闪烁
BLINKOFF = 0x00

# 功能设置指令基础码：配置接口位数、显示行数、字符点阵规格
FUNCTIONSET = 0x20
# 5x10点阵配置位：字符显示采用5x10像素点阵
_5x10DOTS = 0x04
# 5x8点阵配置位：字符显示采用5x8像素点阵（默认规格）
_5x8DOTS = 0x00
# 单行显示配置位：显示屏工作在单行显示模式
_1LINE = 0x00
# 双行显示配置位：显示屏工作在双行显示模式
_2LINE = 0x08
# 8位数据模式配置位：使用8位并行数据接口通信
_8BITMODE = 0x10
# 4位数据模式配置位：使用4位并行数据接口通信（I2C转接板实际采用此模式）
_4BITMODE = 0x00


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class LCD:
    """
    I2C接口LCD1602显示屏驱动类
    I2C Interface LCD1602 Display Driver Class

    实现基于I2C通信协议的LCD1602显示屏全功能控制，涵盖显示开关、光标管理、清屏操作、
    字符输出、光标定位等核心功能，适配Raspberry Pi Pico硬件I2C接口特性
    Implement full-function control of LCD1602 display based on I2C communication protocol, including core functions such as display on/off,
    cursor management, screen clearing, character output, cursor positioning, and adapt to the characteristics of Raspberry Pi Pico hardware I2C interface

    Attributes:
        column (int): 当前光标所在列位置，取值范围0-15
                      Current cursor column position, range 0-15
        row (int): 当前光标所在行位置，取值范围0-1
                   Current cursor row position, range 0-1
        address (int): LCD模块的I2C设备地址，默认值为62（十六进制0x3E）
                       I2C device address of LCD module, default value is 62 (hex 0x3E)
        command (bytearray): 2字节长度的指令缓冲区，用于存储待发送的指令数据
                             2-byte length command buffer for storing pending command data
        i2c (machine.I2C): 已初始化的I2C通信实例，用于与LCD模块进行数据交互
                           Initialized I2C communication instance for data interaction with LCD module

    Methods:
        __init__(i2c): 初始化LCD1602驱动，完成模块上电配置和初始状态设置
                      Initialize LCD1602 driver, complete module power-on configuration and initial state setting
        on(cursor, blink): 开启显示屏，可自定义光标显示和闪烁状态
                           Turn on the display, customizable cursor display and blink state
        off(): 关闭显示屏（数据保留）
               Turn off the display (data retained)
        clear(): 清除屏幕所有内容并将光标复位到(0,0)位置
                 Clear all content on the screen and reset the cursor to (0,0) position
        set_cursor(column, row): 设置光标到指定的行列位置
                                 Set the cursor to the specified column and row position
        write(s): 将字符串输出到显示屏当前光标位置
                  Output the string to the current cursor position of the display
        _command(value): 向LCD模块发送控制指令（私有方法）
                         Send control commands to the LCD module (private method)

    Notes:
        1. 使用前需确认LCD模块实际I2C地址，常见地址为0x3E（62）或0x27（39）
        2. 行列参数会自动进行取模运算，避免越界访问导致的显示异常
        3. 字符串输出时自动处理换行，列位置超过15时切换到下一行开头
        4. 所有指令发送后均有延时，确保模块有足够时间完成指令执行
    ==========================================
    I2C Interface LCD1602 Display Driver Class

    Implement full-function control of LCD1602 display based on I2C communication protocol, including core functions such as display on/off,
    cursor management, screen clearing, character output, cursor positioning, and adapt to the characteristics of Raspberry Pi Pico hardware I2C interface

    Attributes:
        column (int): Current cursor column position, range 0-15
        row (int): Current cursor row position, range 0-1
        address (int): I2C device address of LCD module, default value is 62 (hex 0x3E)
        command (bytearray): 2-byte length command buffer for storing pending command data
        i2c (machine.I2C): Initialized I2C communication instance for data interaction with LCD module

    Methods:
        __init__(i2c): Initialize LCD1602 driver, complete module power-on configuration and initial state setting
        on(cursor, blink): Turn on the display, customizable cursor display and blink state
        off(): Turn off the display (data retained)
        clear(): Clear all content on the screen and reset the cursor to (0,0) position
        set_cursor(column, row): Set the cursor to the specified column and row position
        write(s): Output the string to the current cursor position of the display
        _command(value): Send control commands to the LCD module (private method)

    Notes:
        1. Confirm the actual I2C address of the LCD module before use, common addresses are 0x3E (62) or 0x27 (39)
        2. Column and row parameters are automatically modulo calculated to avoid display abnormalities caused by out-of-bounds access
        3. Line breaks are automatically handled during string output, switch to the beginning of the next line when column position exceeds 15
        4. There is a delay after all commands are sent to ensure the module has enough time to complete command execution
    """

    def __init__(self, i2c: machine.I2C) -> None:
        """
        初始化LCD1602显示屏驱动
        Initialize LCD1602 Display Driver

        Args:
            i2c (machine.I2C): 已完成引脚和速率配置的I2C通信实例
                               Pre-configured I2C communication instance with pins and baud rate set

        Raises:
            ValueError: I2C实例为None时触发
            TypeError: I2C实例类型错误时触发

        Notes:
            初始化流程：
            1. 初始化类属性，设置默认I2C地址和指令缓冲区
            2. 延时50ms等待模块上电稳定
            3. 三次发送功能设置指令确保模块正确识别配置
            4. 开启显示（默认关闭光标和闪烁）
            5. 清屏并设置输入模式为光标左移、显示不移位
            6. 将光标复位到初始位置(0,0)
        ==========================================
        Initialize LCD1602 Display Driver

        Args:
            i2c (machine.I2C): Pre-configured I2C communication instance with pins and baud rate set

        Raises:
            ValueError: Triggered when I2C instance is None
            TypeError: Triggered when I2C instance type is incorrect

        Notes:
            Initialization process:
            1. Initialize class attributes, set default I2C address and command buffer
            2. Delay 50ms to wait for module power-on stabilization
            3. Send function set command three times to ensure the module correctly identifies the configuration
            4. Turn on the display (cursor and blink off by default)
            5. Clear the screen and set entry mode to cursor left move, display no shift
            6. Reset cursor to initial position (0,0)
        """
        # 检查I2C实例是否为None
        if i2c is None:
            raise ValueError("I2C instance cannot be None")
        # 检查I2C实例类型是否正确
        if not isinstance(i2c, machine.I2C):
            raise TypeError(f"I2C instance expected, got {type(i2c).__name__}")

        # 初始化光标列位置为0
        self.column: int = 0
        # 初始化光标行位置为0
        self.row: int = 0
        # 设置LCD模块默认I2C地址（十进制62对应十六进制0x3E）
        self.address: int = 62
        # 创建2字节的指令缓冲区，用于存储指令标志位和指令数据
        self.command: bytearray = bytearray(2)
        # 保存传入的I2C通信实例
        self.i2c: machine.I2C = i2c

        # 延时50毫秒，等待LCD模块上电完成并稳定
        time.sleep_ms(50)

        # 循环发送3次功能设置指令，确保模块正确初始化（适配不同批次模块兼容性）
        for i in range(3):
            self._command(FUNCTIONSET | _2LINE)
            # 每次发送后延时10ms，保证指令执行完成
            time.sleep_ms(10)

        # 开启显示屏，默认关闭光标和闪烁功能
        self.on()
        # 清除屏幕所有显示内容
        self.clear()

        # 设置输入模式：光标左移，显示内容不移位
        self._command(ENTRYMODESET | ENTRYLEFT | ENTRYSHIFTDECREMENT)
        # 将光标定位到显示屏左上角初始位置(0,0)
        self.set_cursor(0, 0)

    def on(self, cursor: bool = False, blink: bool = False) -> None:
        """
        开启显示屏，可配置光标显示和闪烁状态
        Turn on Display with Configurable Cursor and Blink State

        Args:
            cursor (bool, optional): 是否显示光标，默认False（不显示）
                                     Whether to display cursor, default False (not display)
            blink (bool, optional): 光标是否闪烁，默认False（不闪烁）
                                    Whether cursor blinks, default False (not blink)

        Raises:
            ValueError: cursor或blink参数为None时触发
            TypeError: cursor或blink参数类型非布尔值时触发

        Notes:
            支持四种显示模式组合：
            1. 仅显示内容（cursor=False, blink=False）
            2. 显示内容+光标闪烁（cursor=False, blink=True）
            3. 显示内容+显示光标（cursor=True, blink=False）
            4. 显示内容+显示光标+光标闪烁（cursor=True, blink=True）
        ==========================================
        Turn on Display with Configurable Cursor and Blink State

        Args:
            cursor (bool, optional): Whether to display cursor, default False (not display)
            blink (bool, optional): Whether cursor blinks, default False (not blink)

        Raises:
            ValueError: Triggered when cursor or blink parameter is None
            TypeError: Triggered when cursor or blink parameter is not boolean

        Notes:
            Support four display mode combinations:
            1. Display content only (cursor=False, blink=False)
            2. Display content + cursor blink (cursor=False, blink=True)
            3. Display content + show cursor (cursor=True, blink=False)
            4. Display content + show cursor + cursor blink (cursor=True, blink=True)
        """
        # 检查cursor参数是否为None
        if cursor is None:
            raise ValueError("Cursor parameter cannot be None")
        # 检查cursor参数类型是否为布尔值
        if not isinstance(cursor, bool):
            raise TypeError(f"Boolean expected for cursor, got {type(cursor).__name__}")
        # 检查blink参数是否为None
        if blink is None:
            raise ValueError("Blink parameter cannot be None")
        # 检查blink参数类型是否为布尔值
        if not isinstance(blink, bool):
            raise TypeError(f"Boolean expected for blink, got {type(blink).__name__}")

        # 模式1：仅显示内容，关闭光标和闪烁
        if cursor is False and blink is False:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSOROFF | BLINKOFF)
        # 模式2：显示内容+光标闪烁，关闭光标显示
        elif cursor is False and blink is True:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSOROFF | BLINKON)
        # 模式3：显示内容+显示光标，关闭光标闪烁
        elif cursor is True and blink is False:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSORON | BLINKOFF)
        # 模式4：显示内容+显示光标+光标闪烁
        elif cursor is True and blink is True:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSORON | BLINKON)

    def off(self) -> None:
        """
        关闭显示屏
        Turn off Display

        Args:
            无
            None

        Returns:
            None

        Notes:
            1. 关闭显示屏后，DDRAM中的显示数据不会丢失
            2. 同时关闭光标显示和闪烁功能
            3. 调用on()方法可恢复显示，无需重新初始化
        ==========================================
        Turn off Display

        Args:
            None

        Returns:
            None

        Notes:
            1. The display data in DDRAM will not be lost after turning off the display
            2. Turn off cursor display and blink function at the same time
            3. Call the on() method to resume display without reinitialization
        """
        # 发送显示关闭指令，同时关闭光标和闪烁
        self._command(DISPLAYCONTROL | DISPLAYOFF | CURSOROFF | BLINKOFF)

    def clear(self) -> None:
        """
        清屏并重置光标位置
        Clear Screen and Reset Cursor Position

        Args:
            无
            None

        Returns:
            None

        Notes:
            1. 清屏指令执行时间约1ms，需等待指令完成
            2. 光标会自动复位到显示屏左上角(0,0)位置
            3. 清屏后DDRAM中的数据会被清空
        ==========================================
        Clear Screen and Reset Cursor Position

        Args:
            None

        Returns:
            None

        Notes:
            1. The execution time of the clear screen command is about 1ms, need to wait for the command to complete
            2. The cursor will be automatically reset to the upper left corner (0,0) of the display
            3. The data in DDRAM will be cleared after screen clearing
        """
        # 发送清屏指令，清除所有显示内容
        self._command(CLEARDISPLAY)
        # 将光标复位到初始位置(0,0)
        self.set_cursor(0, 0)

    def set_cursor(self, column: int, row: int) -> None:
        """
        设置光标到指定的行列位置
        Set Cursor to Specified Column and Row Position

        Args:
            column (int): 目标列位置，取值范围0-15
                          Target column position, range 0-15
            row (int): 目标行位置，取值范围0-1
                       Target row position, range 0-1

        Raises:
            ValueError: column/row为None或取值超出0-15/0-1范围时触发
            TypeError: column/row参数类型非整数时触发

        Notes:
            1. 行列参数会自动取模处理，超出范围时自动循环（如column=17等效于column=1）
            2. 第一行DDRAM起始地址为0x80，第二行起始地址为0xC0
            3. 光标位置更新后会实时反映到显示屏上
        ==========================================
        Set Cursor to Specified Column and Row Position

        Args:
            column (int): Target column position, range 0-15
            row (int): Target row position, range 0-1

        Raises:
            ValueError: Triggered when column/row is None or out of 0-15/0-1 range
            TypeError: Triggered when column/row parameter is not integer

        Notes:
            1. Column and row parameters are automatically modulo processed, and loop automatically when out of range (e.g., column=17 is equivalent to column=1)
            2. The starting address of DDRAM in the first row is 0x80, and the starting address of the second row is 0xC0
            3. The cursor position will be reflected on the display in real time after update
        """
        # 检查column参数是否为None
        if column is None:
            raise ValueError("Column parameter cannot be None")
        # 检查column参数类型是否为整数
        if not isinstance(column, int):
            raise TypeError(f"Integer expected for column, got {type(column).__name__}")
        # 检查column参数取值范围
        if column < 0 or column > 15:
            raise ValueError(f"Column must be between 0 and 15, got {column}")
        # 检查row参数是否为None
        if row is None:
            raise ValueError("Row parameter cannot be None")
        # 检查row参数类型是否为整数
        if not isinstance(row, int):
            raise TypeError(f"Integer expected for row, got {type(row).__name__}")
        # 检查row参数取值范围
        if row < 0 or row > 1:
            raise ValueError(f"Row must be between 0 and 1, got {row}")

        # 列位置取模运算，确保取值在0-15范围内
        column = column % COLUMNS
        # 行位置取模运算，确保取值在0-1范围内
        row = row % ROWS
        # 计算光标定位指令码：第一行起始0x80，第二行起始0xC0
        if row == 0:
            command = column | 0x80
        else:
            command = column | 0xC0
        # 更新类属性中的当前行位置
        self.row = row
        # 更新类属性中的当前列位置
        self.column = column
        # 发送光标定位指令
        self._command(command)

    def write(self, s: str) -> None:
        """
        输出字符串到显示屏当前光标位置
        Output String to Current Cursor Position of Display

        Args:
            s (str): 要显示的字符串，支持ASCII字符
                     String to be displayed, supporting ASCII characters

        Raises:
            ValueError: 字符串参数为None时触发
            TypeError: 字符串参数类型非字符串时触发

        Notes:
            1. 每个字符输出前延时10ms，确保显示稳定无乱码
            2. 字符输出后自动更新光标列位置
            3. 列位置超过15时自动切换到下一行开头
            4. 第二行列位置超过15时会循环回到第二行开头
        ==========================================
        Output String to Current Cursor Position of Display

        Args:
            s (str): String to be displayed, supporting ASCII characters

        Raises:
            ValueError: Triggered when string parameter is None
            TypeError: Triggered when string parameter is not string type

        Notes:
            1. Delay 10ms before each character output to ensure stable display without garbled characters
            2. Automatically update cursor column position after character output
            3. Automatically switch to the beginning of the next row when column position exceeds 15
            4. When the column position of the second row exceeds 15, it will loop back to the beginning of the second row
        """
        # 检查字符串参数是否为None
        if s is None:
            raise ValueError("String parameter cannot be None")
        # 检查字符串参数类型是否为字符串
        if not isinstance(s, str):
            raise TypeError(f"String expected, got {type(s).__name__}")

        # 遍历字符串中的每个字符
        for i in range(len(s)):
            # 字符输出前延时10ms，避免模块处理不及时导致乱码
            time.sleep_ms(10)
            # 发送字符数据：0x40为数据写入标志位，后跟字符ASCII码
            self.i2c.writeto(self.address, b"\x40" + s[i].encode())
            # 更新当前光标列位置
            self.column = self.column + 1
            # 检查列位置是否超出显示屏列数
            if self.column >= COLUMNS:
                # 切换到下一行开头位置
                self.set_cursor(0, self.row + 1)

    def _command(self, value: int) -> None:
        """
        向LCD模块发送控制指令（私有方法）
        Send Control Command to LCD Module (Private Method)

        Args:
            value (int): 指令字节码，取值范围0-255
                         Command byte code, range 0-255

        Raises:
            ValueError: 指令值为None或取值超出0-255范围时触发
            TypeError: 指令值参数类型非整数时触发

        Notes:
            1. 私有方法，仅在类内部调用
            2. 指令缓冲区第一个字节为0x80（指令写入标志），第二个字节为指令码
            3. 指令发送后延时1ms，确保模块完成指令执行
            4. 所有LCD模块的控制指令均通过此方法发送
        ==========================================
        Send Control Command to LCD Module (Private Method)

        Args:
            value (int): Command byte code, range 0-255

        Raises:
            ValueError: Triggered when command value is None or out of 0-255 range
            TypeError: Triggered when command value parameter is not integer

        Notes:
            1. Private method, only called inside the class
            2. The first byte of the command buffer is 0x80 (command write flag), the second byte is the command code
            3. Delay 1ms after command sending to ensure the module completes command execution
            4. All control commands of the LCD module are sent through this method
        """
        # 检查指令值参数是否为None
        if value is None:
            raise ValueError("Command value cannot be None")
        # 检查指令值参数类型是否为整数
        if not isinstance(value, int):
            raise TypeError(f"Integer expected for command value, got {type(value).__name__}")
        # 检查指令值取值范围（0-255，单字节）
        if value < 0 or value > 255:
            raise ValueError(f"Command value must be between 0 and 255, got {value}")

        # 设置指令写入标志位：0x80表示后续字节为控制指令
        self.command[0] = 0x80
        # 设置要发送的指令字节码
        self.command[1] = value
        # 通过I2C总线向LCD模块发送指令
        self.i2c.writeto(self.address, self.command)
        # 延时1ms，确保指令执行完成
        time.sleep_ms(1)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
