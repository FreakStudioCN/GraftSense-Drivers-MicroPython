# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午5:00
# @Author  : bhavi-thiran
# @File    : lcd_i2c.py
# @Description : I2C接口LCD1602显示屏驱动 实现显示控制、光标管理、字符输出等核心功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "bhavi-thiran"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入硬件控制模块，用于I2C和引脚配置
import machine

# 导入时间模块，用于延时操作
import time

# ======================================== 全局变量 ============================================
# LCD显示屏列数
COLUMNS = 16
# LCD显示屏行数
ROWS = 2

# Instruction set - LCD指令集定义
# 清屏指令
CLEARDISPLAY = 0x01

# 输入模式设置指令
ENTRYMODESET = 0x04
# 光标左移
ENTRYLEFT = 0x02
# 光标右移
ENTRYRIGHT = 0x00
# 显示移位增量
ENTRYSHIFTINCREMENT = 0x01
# 显示移位减量
ENTRYSHIFTDECREMENT = 0x00

# 显示控制指令
DISPLAYCONTROL = 0x08
# 显示开启
DISPLAYON = 0x04
# 显示关闭
DISPLAYOFF = 0x00
# 光标开启
CURSORON = 0x02
# 光标关闭
CURSOROFF = 0x00
# 闪烁开启
BLINKON = 0x01
# 闪烁关闭
BLINKOFF = 0x00

# 功能设置指令
FUNCTIONSET = 0x20
# 5x10点阵字符
_5x10DOTS = 0x04
# 5x8点阵字符
_5x8DOTS = 0x00
# 单行显示
_1LINE = 0x00
# 双行显示
_2LINE = 0x08
# 8位数据模式
_8BITMODE = 0x10
# 4位数据模式
_4BITMODE = 0x00


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class LCD:
    """
    I2C接口LCD1602显示屏驱动类
    I2C Interface LCD1602 Display Driver Class

    实现基于I2C通信协议的LCD1602显示屏完整控制功能，包括显示开关、光标管理、清屏、
    字符输出、光标定位等核心功能，适配Raspberry Pi Pico的硬件I2C接口
    Implement complete control functions of LCD1602 display based on I2C communication protocol, including core functions such as display on/off,
    cursor management, screen clearing, character output, cursor positioning, and adapt to hardware I2C interface of Raspberry Pi Pico

    Attributes:
        column (int): 当前光标列位置(0-15)
                      Current cursor column position (0-15)
        row (int): 当前光标行位置(0-1)
                   Current cursor row position (0-1)
        address (int): LCD模块I2C设备地址，默认62(0x3E)
                       LCD module I2C device address, default 62(0x3E)
        command (bytearray): 2字节指令缓冲区，用于存储指令数据
                             2-byte command buffer for storing command data
        i2c (machine.I2C): I2C通信对象，用于与LCD模块进行数据交互
                           I2C communication object for data interaction with LCD module

    Methods:
        __init__(sda, scl): 初始化LCD1602显示屏驱动
                            Initialize LCD1602 display driver
        on(cursor=False, blink=False): 开启显示屏
                                       Turn on display
        off(): 关闭显示屏
               Turn off display
        clear(): 清屏并重置光标位置
                 Clear screen and reset cursor position
        set_cursor(column, row): 设置光标位置
                                 Set cursor position
        write(s): 输出字符串到显示屏
                  Output string to display
        _command(value): 发送指令到LCD模块（私有方法）
                         Send command to LCD module (private method)
    """

    def __init__(self, sda, scl):
        """
        初始化LCD1602显示屏驱动
        Initialize LCD1602 display driver

        Args:
            sda (int): SDA引脚编号
                       SDA pin number
            scl (int): SCL引脚编号
                       SCL pin number

        Returns:
            None

        Notes:
            根据SCL引脚编号自动选择I2C0或I2C1接口，初始化后默认开启显示、关闭光标和闪烁，
            光标定位在(0,0)位置，输入模式为左移、不移位
            Automatically select I2C0 or I2C1 interface according to SCL pin number, after initialization, display is turned on by default,
            cursor and blink are turned off, cursor is positioned at (0,0), input mode is left shift and no shift
        """
        # 初始化光标列位置
        self.column = 0
        # 初始化光标行位置
        self.row = 0

        # 设置LCD模块I2C地址（十进制62 = 十六进制0x3E）
        self.address = 62

        # 初始化2字节指令缓冲区
        self.command = bytearray(2)

        # 配置SDA引脚
        _sda = machine.Pin(sda)
        # 配置SCL引脚
        _scl = machine.Pin(scl)

        # 根据SCL引脚编号选择I2C接口（3/7/11/15/19/27使用I2C1，其他使用I2C0）
        if scl == 3 or scl == 7 or scl == 11 or scl == 15 or scl == 19 or scl == 27:
            self.i2c = machine.I2C(1, sda=_sda, scl=_scl, freq=400000)
        else:
            self.i2c = machine.I2C(0, sda=_sda, scl=_scl, freq=400000)

        # 延时50ms等待模块上电稳定
        time.sleep_ms(50)

        # 发送3次功能设置指令，确保模块正确初始化
        for i in range(3):
            self._command(FUNCTIONSET | _2LINE)
            time.sleep_ms(10)

        # 开启显示（默认关闭光标和闪烁）
        self.on()
        # 清屏
        self.clear()

        # 设置输入模式：光标左移，显示不移位
        self._command(ENTRYMODESET | ENTRYLEFT | ENTRYSHIFTDECREMENT)

        # 将光标定位到初始位置(0,0)
        self.set_cursor(0, 0)

    def on(self, cursor=False, blink=False):
        """
        开启显示屏
        Turn on display

        Args:
            cursor (bool, optional): 光标显示状态，默认False(关闭)
                                     Cursor display status, default False(off)
            blink (bool, optional): 光标闪烁状态，默认False(关闭)
                                    Cursor blink status, default False(off)

        Returns:
            None

        Notes:
            支持四种显示模式组合：仅显示、显示+闪烁、显示+光标、显示+光标+闪烁
            Support four display mode combinations: display only, display+blink, display+cursor, display+cursor+blink
        """
        # 仅显示，关闭光标和闪烁
        if cursor == False and blink == False:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSOROFF | BLINKOFF)
        # 显示+闪烁，关闭光标
        elif cursor == False and blink == True:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSOROFF | BLINKON)
        # 显示+光标，关闭闪烁
        elif cursor == True and blink == False:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSORON | BLINKOFF)
        # 显示+光标+闪烁
        elif cursor == True and blink == True:
            self._command(DISPLAYCONTROL | DISPLAYON | CURSORON | BLINKON)

    def off(self):
        """
        关闭显示屏
        Turn off display

        Args:
            None

        Returns:
            None

        Notes:
            关闭显示的同时关闭光标和闪烁，数据仍保存在DDRAM中，重新开启后恢复显示
            Turn off display and also turn off cursor and blink, data is still stored in DDRAM, display resumes after re-enabling
        """
        self._command(DISPLAYCONTROL | DISPLAYOFF | CURSOROFF | BLINKOFF)

    def clear(self):
        """
        清屏并重置光标位置
        Clear screen and reset cursor position

        Args:
            None

        Returns:
            None

        Notes:
            发送清屏指令后自动将光标重置到(0,0)位置，清屏操作需要约1ms完成
            After sending clear screen command, cursor is automatically reset to (0,0) position, clear screen operation takes about 1ms to complete
        """
        # 发送清屏指令
        self._command(CLEARDISPLAY)
        # 重置光标位置到(0,0)
        self.set_cursor(0, 0)

    def set_cursor(self, column, row):
        """
        设置光标位置
        Set cursor position

        Args:
            column (int): 目标列位置(0-15)
                          Target column position (0-15)
            row (int): 目标行位置(0-1)
                       Target row position (0-1)

        Returns:
            None

        Notes:
            列和行参数会自动取模处理（column%16, row%2），确保位置有效，
            第一行起始地址0x80，第二行起始地址0xC0
            Column and row parameters are automatically modulo processed (column%16, row%2) to ensure valid position,
            first row start address 0x80, second row start address 0xC0
        """
        # 列位置取模，确保在0-15范围内
        column = column % COLUMNS
        # 行位置取模，确保在0-1范围内
        row = row % ROWS
        # 计算光标位置指令
        if row == 0:
            command = column | 0x80
        else:
            command = column | 0xC0
        # 更新当前行位置
        self.row = row
        # 更新当前列位置
        self.column = column
        # 发送光标定位指令
        self._command(command)

    def write(self, s):
        """
        输出字符串到显示屏
        Output string to display

        Args:
            s (str/bytes): 要显示的字符串/字节数据
                           String/byte data to display

        Returns:
            None

        Notes:
            自动处理换行：当列位置超过15时，自动切换到下一行开头，
            每个字符输出间隔10ms确保显示稳定
            Automatically handle line breaks: when column position exceeds 15, automatically switch to next row start,
            10ms interval between each character output to ensure stable display
        """
        # 遍历字符串每个字符
        for i in range(len(s)):
            # 字符输出间隔延时
            time.sleep_ms(10)
            # 发送字符数据（0x40为数据写入标志）
            self.i2c.writeto(self.address, b"\x40" + s[i])
            # 更新当前列位置
            self.column = self.column + 1
            # 检查是否需要换行
            if self.column >= COLUMNS:
                # 切换到下一行开头
                self.set_cursor(0, self.row + 1)

    def _command(self, value):
        """
        发送指令到LCD模块（私有方法）
        Send command to LCD module (private method)

        Args:
            value (int): 要发送的指令字节(0-255)
                         Command byte to send (0-255)

        Returns:
            None

        Notes:
            内部使用方法，0x80为指令写入标志，指令发送后延时1ms确保执行完成
            Internal use method, 0x80 is command write flag, 1ms delay after command sending to ensure execution completion
        """
        # 设置指令标志位（0x80表示写入指令）
        self.command[0] = 0x80
        # 设置指令数据
        self.command[1] = value
        # 通过I2C发送指令
        self.i2c.writeto(self.address, self.command)
        # 指令执行延时
        time.sleep_ms(1)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
