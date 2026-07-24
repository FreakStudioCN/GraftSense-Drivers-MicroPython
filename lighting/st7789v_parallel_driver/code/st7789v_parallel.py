# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Russ Hughes, FreakStudio
# @File    : st7789v_parallel.py
# @Description : ST7789/ST7789V 8-bit parallel/I8080接口LCD屏幕驱动
# @License : MIT

__version__ = "0.1.1"
__author__ = "Russ Hughes, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

import time

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


try:
    import ustruct as struct
except ImportError:
    import struct

# ======================================== 全局变量 ============================================

# 颜色编码格式
_ENCODE_PIXEL = ">H"
_ENCODE_POS = ">HH"
_DECODE_PIXEL = ">BBB"

# 缓冲区大小
_BUFFER_SIZE = const(256)

# 位定义常量
_BIT7 = const(0x80)
_BIT6 = const(0x40)
_BIT5 = const(0x20)
_BIT4 = const(0x10)
_BIT3 = const(0x08)
_BIT2 = const(0x04)
_BIT1 = const(0x02)
_BIT0 = const(0x01)

# ======================================== 功能函数 ============================================


def _encode_pos(x, y):
    """Encode a position into bytes."""
    return struct.pack(_ENCODE_POS, x, y)


def _encode_pixel(color):
    """Encode a pixel color into bytes."""
    return struct.pack(_ENCODE_PIXEL, color)


def color565(red, green=0, blue=0):
    """
    将红、绿、蓝通道值（0-255）转换为 16 位 RGB565 编码
    Args:
        red: 红色通道值或包含 (r, g, b) 的元组/列表
        green: 绿色通道值，默认 0
        blue: 蓝色通道值，默认 0
    Returns:
        int: 16 位 RGB565 编码值
    ==========================================
    Convert red, green and blue values (0-255) into a 16-bit 565 encoding.
    Args:
        red: Red channel value or (r, g, b) tuple/list
        green: Green channel value, default 0
        blue: Blue channel value, default 0
    Returns:
        int: 16-bit RGB565 encoded color value
    """
    try:
        # 如果第一个参数是元组/列表，解包
        red, green, blue = red
    except TypeError:
        pass
    return (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3


# ======================================== 自定义类 ============================================


class ST7789:
    """
    ST7789/ST7789V 8-bit 并行接口 (I8080) LCD 显示驱动类

    通过 8-bit 并行总线控制 ST7789/ST7789V 系列 TFT LCD 显示器，支持基本图形绘制、
    文本渲染、位图显示和硬件垂直滚动等功能。

    Attributes:
        width (int): 当前逻辑宽度（像素），随 rotation 变化
        height (int): 当前逻辑高度（像素），随 rotation 变化
        xstart (int): 列偏移量
        ystart (int): 行偏移量
        _display_width (int): 物理显示宽度（像素）
        _display_height (int): 物理显示高度（像素）
        _rotation (int): 当前旋转索引（0-3）

    Methods:
        __init__(): 初始化显示器，配置并行引脚并发送初始化序列
        hard_reset(): 通过 RST 引脚执行硬件复位
        soft_reset(): 发送软复位命令
        sleep_mode(): 进入/退出睡眠模式
        inversion_mode(): 开启/关闭显示反转
        rotation(): 设置显示旋转方向
        pixel(): 绘制单个像素点
        hline(): 绘制水平线
        vline(): 绘制垂直线
        rect(): 绘制矩形边框
        fill_rect(): 绘制填充矩形
        fill(): 使用指定颜色填充整个屏幕
        line(): 使用 Bresenham 算法绘制直线
        blit_buffer(): 将像素缓冲区写入指定区域
        text(): 使用位图字体绘制文本
        bitmap(): 绘制位图图像
        write(): 使用 TrueType 转换字体绘制字符串
        write_width(): 计算字符串绘制宽度
        vscrdef(): 设置垂直滚动区域
        vscsad(): 设置垂直滚动起始地址
        deinit(): 释放硬件资源

    Notes:
        - 此驱动专用于 8-bit 并行/I8080 接口，不可与 SPI 版本混用
        - 通过构造函数注入所有 Pin 对象，不在内部创建引脚实例
    ==========================================
    ST7789/ST7789V 8-bit parallel (I8080) LCD display driver.

    Controls ST7789/ST7789V series TFT LCD displays via 8-bit parallel bus,
    supporting basic graphics drawing, text rendering, bitmap display and
    hardware vertical scrolling.

    Attributes:
        width (int): Current logical width in pixels, changes with rotation
        height (int): Current logical height in pixels, changes with rotation
        xstart (int): Column offset
        ystart (int): Row offset
        _display_width (int): Physical display width in pixels
        _display_height (int): Physical display height in pixels
        _rotation (int): Current rotation index (0-3)

    Methods:
        __init__(): Initialize display, configure parallel pins and send init sequence
        hard_reset(): Hardware reset via RST pin
        soft_reset(): Send soft reset command
        sleep_mode(): Enter/exit sleep mode
        inversion_mode(): Enable/disable display inversion
        rotation(): Set display rotation
        pixel(): Draw a single pixel
        hline(): Draw horizontal line
        vline(): Draw vertical line
        rect(): Draw rectangle outline
        fill_rect(): Draw filled rectangle
        fill(): Fill entire screen with color
        line(): Draw a line using Bresenham algorithm
        blit_buffer(): Write pixel buffer to specified area
        text(): Draw text using bitmap font
        bitmap(): Draw bitmap image
        write(): Draw string using converted TrueType font
        write_width(): Calculate pixel width of a string
        vscrdef(): Set vertical scroll definition
        vscsad(): Set vertical scroll start address
        deinit(): Release hardware resources

    Notes:
        - This driver is for 8-bit parallel/I8080 interface only, not compatible with SPI version
        - All Pin objects injected via constructor, no internal pin creation
    """

    # 类级常量 - ST7789 命令
    NOP = const(0x00)
    SWRESET = const(0x01)
    RDDID = const(0x04)
    RDDST = const(0x09)

    SLPIN = const(0x10)
    SLPOUT = const(0x11)
    PTLON = const(0x12)
    NORON = const(0x13)

    INVOFF = const(0x20)
    INVON = const(0x21)
    DISPOFF = const(0x28)
    DISPON = const(0x29)
    CASET = const(0x2A)
    RASET = const(0x2B)
    RAMWR = const(0x2C)
    RAMRD = const(0x2E)

    PTLAR = const(0x30)
    VSCRDEF = const(0x33)
    COLMOD = const(0x3A)
    MADCTL = const(0x36)
    VSCSAD = const(0x37)

    # MADCTL 位定义
    MADCTL_MY = const(0x80)
    MADCTL_MX = const(0x40)
    MADCTL_MV = const(0x20)
    MADCTL_ML = const(0x10)
    MADCTL_BGR = const(0x08)
    MADCTL_MH = const(0x04)
    MADCTL_RGB = const(0x00)

    RDID1 = const(0xDA)
    RDID2 = const(0xDB)
    RDID3 = const(0xDC)
    RDID4 = const(0xDD)

    # 颜色模式常量
    COLOR_MODE_65K = const(0x50)
    COLOR_MODE_262K = const(0x60)
    COLOR_MODE_12BIT = const(0x03)
    COLOR_MODE_16BIT = const(0x05)
    COLOR_MODE_18BIT = const(0x06)
    COLOR_MODE_16M = const(0x07)

    # 默认颜色定义
    BLACK = const(0x0000)
    BLUE = const(0x001F)
    RED = const(0xF800)
    GREEN = const(0x07E0)
    CYAN = const(0x07FF)
    MAGENTA = const(0xF81F)
    YELLOW = const(0xFFE0)
    WHITE = const(0xFFFF)

    # 旋转表 - (width, height, xstart, ystart)[rotation % 4]
    _WIDTH_320 = [
        (240, 320, 0, 0),
        (320, 240, 0, 0),
        (240, 320, 0, 0),
        (320, 240, 0, 0),
    ]

    _WIDTH_240 = [
        (240, 240, 0, 0),
        (240, 240, 0, 0),
        (240, 240, 0, 80),
        (240, 240, 80, 0),
    ]

    _WIDTH_170 = [
        (170, 320, 35, 0),
        (320, 170, 0, 35),
        (170, 320, 35, 0),
        (320, 170, 0, 35),
    ]

    _WIDTH_135 = [
        (135, 240, 52, 40),
        (240, 135, 40, 53),
        (135, 240, 53, 40),
        (240, 135, 40, 52),
    ]

    # MADCTL 旋转值 [rotation % 4]
    _ROTATIONS = [0x00, 0x60, 0xC0, 0xA0]

    # 支持的显示分辨率
    _SUPPORTED_HEIGHTS = [320, 240]
    _SUPPORTED_WIDTHS = [320, 240, 170, 135]

    # 通信超时时间（毫秒）
    _WRITE_TIMEOUT_MS = const(500)

    def __init__(
        self,
        d7,
        d6,
        d5,
        d4,
        d3,
        d2,
        d1,
        d0,
        wr,
        rd,
        width,
        height,
        reset=None,
        dc=None,
        cs=None,
        backlight=None,
        rotation=0,
        debug=False,
    ):
        """
        初始化 ST7789/ST7789V 8-bit 并行接口显示器

        Args:
            d7~d0: 8 位并行数据总线引脚 (D7 为 MSB, D0 为 LSB)，需为 machine.Pin 实例
            wr: 写选通引脚 (WR)
            rd: 读选通引脚 (RD)
            width (int): 显示物理宽度（像素）
            height (int): 显示物理高度（像素）
            reset: 复位引脚 (RST)，可选
            dc: 数据/命令选择引脚 (DC/RS)，必需
            cs: 片选引脚 (CS)，可选
            backlight: 背光控制引脚，可选
            rotation (int): 显示旋转方向：
                - 0: 竖屏 (Portrait)
                - 1: 横屏 (Landscape)
                - 2: 倒竖屏 (Inverted Portrait)
                - 3: 倒横屏 (Inverted Landscape)
            debug (bool): 是否启用调试日志输出

        Returns:
            None

        Raises:
            ValueError: 分辨率不支持或 dc 引脚未提供时抛出

        Notes:
            - 所有引脚参数必须为 machine.Pin 实例，不在内部创建引脚对象
            - 初始化时会执行硬件复位并发送初始化序列
            - ISR-safe: 否
        ==========================================
        Initialize ST7789/ST7789V 8-bit parallel interface display.

        Args:
            d7~d0: 8-bit parallel data bus pins (D7=MSB, D0=LSB), must be machine.Pin instances
            wr: Write strobe pin (WR)
            rd: Read strobe pin (RD)
            width (int): Display physical width in pixels
            height (int): Display physical height in pixels
            reset: Reset pin (RST), optional
            dc: Data/command select pin (DC/RS), required
            cs: Chip select pin (CS), optional
            backlight: Backlight control pin, optional
            rotation (int): Display rotation:
                - 0: Portrait
                - 1: Landscape
                - 2: Inverted Portrait
                - 3: Inverted Landscape
            debug (bool): Enable debug log output

        Returns:
            None

        Raises:
            ValueError: If resolution unsupported or dc pin not provided

        Notes:
            - All pin parameters must be machine.Pin instances, no internal pin creation
            - Hardware reset and initialization sequence executed during init
            - ISR-safe: No
        """
        # 参数校验 - 检查分辨率
        if height not in self._SUPPORTED_HEIGHTS or width not in self._SUPPORTED_WIDTHS:
            raise ValueError("Unsupported display. 320x240, 170x320, 240x240 and 135x240 are supported.")
        # 参数校验 - dc 引脚为必需
        if dc is None:
            raise ValueError("dc pin is required.")

        # 配置 DEBUG 模式和物理尺寸
        self._debug = debug
        self._display_width = self.width = width
        self._display_height = self.height = height
        self.xstart = 0
        self.ystart = 0

        # 初始化数据引脚引用和写缓存
        self.last = None
        self.d7 = d7
        self.d6 = d6
        self.d5 = d5
        self.d4 = d4
        self.d3 = d3
        self.d2 = d2
        self.d1 = d1
        self.d0 = d0
        self.wr = wr
        self.rd = rd

        # 初始化控制引脚引用
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self._rotation = rotation % 4

        # 设置控制引脚初始电平
        if self.cs:
            self.cs.on()
        self.dc.on()
        self.wr.on()
        self.rd.on()

        # 执行硬件复位
        self.hard_reset()
        # 退出睡眠模式
        self.sleep_mode(False)

        # 设置颜色模式并等待稳定
        self._set_color_mode(self.COLOR_MODE_65K | self.COLOR_MODE_16BIT)
        time.sleep_ms(50)
        # 应用旋转设置
        self.rotation(self._rotation)
        # 开启显示反转
        self.inversion_mode(True)
        time.sleep_ms(10)
        # 设置正常显示模式
        self._write(self.NORON)
        time.sleep_ms(10)
        # 开启背光（如果有）
        if backlight is not None:
            backlight.value(1)
        # 开启显示
        self._write(self.DISPON)
        time.sleep_ms(125)

        self._log("ST7789V parallel display initialized")

    def _log(self, msg):
        """
        输出调试日志
        Args:
            msg (str): 日志消息
        Returns:
            None
        ==========================================
        Output debug log message.
        Args:
            msg (str): Log message
        Returns:
            None
        """
        if self._debug:
            print("[ST7789V] %s" % msg)

    def _write_byte(self, b):
        """
        通过 8-bit 并行接口写入单个字节
        设置 8 条数据线电平后，通过 WR 引脚产生写脉冲。
        若当前值与上次相同则跳过数据线设置以优化 speed。

        Args:
            b (int): 要写入的字节值

        Notes:
            - 对数据线使用值缓存优化，避免重复设置已置位的引脚
            - ISR-safe: 否
        ==========================================
        Write a single byte via 8-bit parallel interface.
        Sets 8 data line levels then generates write pulse via WR pin.
        Skips data line setup if value unchanged from last write.

        Args:
            b (int): Byte value to write

        Notes:
            - Uses value caching to optimize data line writes
            - ISR-safe: No
        """
        # 仅当字节值改变时才更新数据线
        if b != self.last:
            self.d7.value(1 if (b & _BIT7) else 0)
            self.d6.value(1 if (b & _BIT6) else 0)
            self.d5.value(1 if (b & _BIT5) else 0)
            self.d4.value(1 if (b & _BIT4) else 0)
            self.d3.value(1 if (b & _BIT3) else 0)
            self.d2.value(1 if (b & _BIT2) else 0)
            self.d1.value(1 if (b & _BIT1) else 0)
            self.d0.value(1 if (b & _BIT0) else 0)
            self.last = b

        # 产生 WR 写脉冲
        self.wr.value(0)
        self.wr.value(1)

    def _write(self, command=None, data=None):
        """
        通过 8-bit 并行接口向显示器写入命令和/或数据
        拉低 CS 选中设备，通过 DC 引脚区分命令/数据。

        Args:
            command (int): 命令字节，可选
            data (bytes): 数据字节序列，可选

        Notes:
            - 调用方需确保 command 和 data 的类型正确
            - ISR-safe: 否
        ==========================================
        Write command and/or data to display via 8-bit parallel bus.
        Pulls CS low to select device, uses DC pin for command/data selection.

        Args:
            command (int): Command byte, optional
            data (bytes): Data byte sequence, optional

        Notes:
            - Caller must ensure correct types for command and data
            - ISR-safe: No
        """
        # 选中设备
        if self.cs:
            self.cs.off()

        # 发送命令字节
        if command is not None:
            self.dc.off()
            for b in bytes([command]):
                self._write_byte(b)
        # 发送数据字节
        if data is not None:
            self.dc.on()
            for b in data:
                self._write_byte(b)

        # 释放设备选择
        if self.cs:
            self.cs.on()

    def hard_reset(self):
        """
        通过 RST 引脚执行硬件复位
        按照芯片手册的复位时序产生脉冲并等待芯片稳定。

        Notes:
            - 会影响显示器状态，复位后需重新初始化
            - ISR-safe: 否
        ==========================================
        Hardware reset via RST pin.
        Generates reset pulse per chip datasheet timing and waits for stabilization.

        Notes:
            - Affects display state; re-initialization required afterwards
            - ISR-safe: No
        """
        if self.cs:
            self.cs.off()
        if self.reset:
            self.reset.on()
        time.sleep_ms(5)
        if self.reset:
            self.reset.off()
        time.sleep_ms(20)
        if self.reset:
            self.reset.on()
        time.sleep_ms(150)
        if self.cs:
            self.cs.on()

    def soft_reset(self):
        """
        通过发送 SWRESET 命令执行软件复位

        Notes:
            - 复位后需等待约 150ms 稳定
            - ISR-safe: 否
        ==========================================
        Software reset by sending SWRESET command.

        Notes:
            - Wait approximately 150ms after reset for stabilization
            - ISR-safe: No
        """
        self._write(self.SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value):
        """
        启用或禁用显示睡眠模式

        Args:
            value (bool): True 进入睡眠，False 退出睡眠

        Notes:
            - 睡眠模式下显示器关闭以节省功耗
            - ISR-safe: 否
        ==========================================
        Enable or disable display sleep mode.

        Args:
            value (bool): True to enter sleep, False to exit sleep

        Notes:
            - Display turns off in sleep mode to save power
            - ISR-safe: No
        """
        if value:
            self._write(self.SLPIN)
        else:
            self._write(self.SLPOUT)

    def inversion_mode(self, value):
        """
        启用或禁用显示反转模式

        Args:
            value (bool): True 开启反转，False 关闭反转

        Notes:
            - 修改显示颜色表现，常用于减少闪烁
            - ISR-safe: 否
        ==========================================
        Enable or disable display inversion mode.

        Args:
            value (bool): True to enable inversion, False to disable

        Notes:
            - Modifies display color appearance, often used to reduce flicker
            - ISR-safe: No
        """
        if value:
            self._write(self.INVON)
        else:
            self._write(self.INVOFF)

    def _set_color_mode(self, mode):
        """
        设置显示颜色模式

        Args:
            mode (int): 颜色模式
                - COLOR_MODE_65K (0x50)
                - COLOR_MODE_262K (0x60)
                - COLOR_MODE_12BIT (0x03)
                - COLOR_MODE_16BIT (0x05)
                - COLOR_MODE_18BIT (0x06)
                - COLOR_MODE_16M (0x07)

        Notes:
            - ISR-safe: 否
        ==========================================
        Set display color mode.

        Args:
            mode (int): Color mode
                - COLOR_MODE_65K (0x50)
                - COLOR_MODE_262K (0x60)
                - COLOR_MODE_12BIT (0x03)
                - COLOR_MODE_16BIT (0x05)
                - COLOR_MODE_18BIT (0x06)
                - COLOR_MODE_16M (0x07)

        Notes:
            - ISR-safe: No
        """
        self._write(self.COLMOD, bytes([mode & 0x77]))

    def rotation(self, rotation):
        """
        设置显示旋转方向
        同时更新逻辑宽高和行列偏移量。

        Args:
            rotation (int): 旋转索引：
                - 0: 竖屏 (Portrait)
                - 1: 横屏 (Landscape)
                - 2: 倒竖屏 (Inverted Portrait)
                - 3: 倒横屏 (Inverted Landscape)

        Raises:
            ValueError: 若当前分辨率未在旋转表中找到对应项

        Notes:
            - 修改 MADCTL 寄存器并更新 self.width/self.height
            - ISR-safe: 否
        ==========================================
        Set display rotation.
        Simultaneously updates logical width/height and row/column offsets.

        Args:
            rotation (int): Rotation index:
                - 0: Portrait
                - 1: Landscape
                - 2: Inverted Portrait
                - 3: Inverted Landscape

        Raises:
            ValueError: If current resolution has no matching rotation table entry

        Notes:
            - Modifies MADCTL register and updates self.width/self.height
            - ISR-safe: No
        """
        rotation %= 4
        self._rotation = rotation
        madctl = self._ROTATIONS[rotation]

        # 根据物理宽度选择旋转表
        if self._display_width == 320:
            table = self._WIDTH_320
        elif self._display_width == 240:
            table = self._WIDTH_240
        elif self._display_width == 170:
            table = self._WIDTH_170
        elif self._display_width == 135:
            table = self._WIDTH_135
        else:
            raise ValueError("Unsupported display. 320x240, 170x320, 240x240, and 135x240 are supported.")

        self.width, self.height, self.xstart, self.ystart = table[rotation]
        self._write(self.MADCTL, bytes([madctl]))

    def _set_columns(self, start, end):
        """
        设置列地址范围 (CASET)

        Args:
            start (int): 起始列地址
            end (int): 结束列地址

        Notes:
            - 仅在坐标范围有效时发送命令
            - ISR-safe: 否
        ==========================================
        Set column address range (CASET).

        Args:
            start (int): Start column address
            end (int): End column address

        Notes:
            - Only sends command when coordinates are valid
            - ISR-safe: No
        """
        if start <= end <= self.width:
            self._write(
                self.CASET,
                _encode_pos(start + self.xstart, end + self.xstart),
            )

    def _set_rows(self, start, end):
        """
        设置行地址范围 (RASET)

        Args:
            start (int): 起始行地址
            end (int): 结束行地址

        Notes:
            - 仅在坐标范围有效时发送命令
            - ISR-safe: 否
        ==========================================
        Set row address range (RASET).

        Args:
            start (int): Start row address
            end (int): End row address

        Notes:
            - Only sends command when coordinates are valid
            - ISR-safe: No
        """
        if start <= end <= self.height:
            self._write(
                self.RASET,
                _encode_pos(start + self.ystart, end + self.ystart),
            )

    def _set_window(self, x0, y0, x1, y1):
        """
        设置像素写入窗口区域
        依次发送 CASET、RASET 和 RAMWR 命令。

        Args:
            x0 (int): 窗口左上角列地址
            y0 (int): 窗口左上角行地址
            x1 (int): 窗口右下角列地址
            y1 (int): 窗口右下角行地址

        Notes:
            - ISR-safe: 否
        ==========================================
        Set pixel write window area.
        Sends CASET, RASET, and RAMWR commands in sequence.

        Args:
            x0 (int): Window top-left column address
            y0 (int): Window top-left row address
            x1 (int): Window bottom-right column address
            y1 (int): Window bottom-right row address

        Notes:
            - ISR-safe: No
        """
        self._set_columns(x0, x1)
        self._set_rows(y0, y1)
        self._write(self.RAMWR)

    def vline(self, x, y, length, color):
        """
        在指定位置绘制垂直线

        Args:
            x (int): 起始 X 坐标
            y (int): 起始 Y 坐标
            length (int): 线长度（像素）
            color (int): 565 编码颜色值

        Notes:
            - ISR-safe: 否
        ==========================================
        Draw vertical line at given location and color.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            length (int): Line length in pixels
            color (int): 565 encoded color

        Notes:
            - ISR-safe: No
        """
        self.fill_rect(x, y, 1, length, color)

    def hline(self, x, y, length, color):
        """
        在指定位置绘制水平线

        Args:
            x (int): 起始 X 坐标
            y (int): 起始 Y 坐标
            length (int): 线长度（像素）
            color (int): 565 编码颜色值

        Notes:
            - ISR-safe: 否
        ==========================================
        Draw horizontal line at given location and color.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            length (int): Line length in pixels
            color (int): 565 encoded color

        Notes:
            - ISR-safe: No
        """
        self.fill_rect(x, y, length, 1, color)

    def pixel(self, x, y, color):
        """
        在指定位置绘制单个像素点

        Args:
            x (int): X 坐标
            y (int): Y 坐标
            color (int): 565 编码颜色值

        Notes:
            - ISR-safe: 否
        ==========================================
        Draw a pixel at given location and color.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            color (int): 565 encoded color

        Notes:
            - ISR-safe: No
        """
        self._set_window(x, y, x, y)
        self._write(None, _encode_pixel(color))

    def blit_buffer(self, buffer, x, y, width, height):
        """
        将像素缓冲区内容绘制到指定区域

        Args:
            buffer (bytes): 像素数据缓冲区（已按 565 编码排列）
            x (int): 区域左上角 X 坐标
            y (int): 区域左上角 Y 坐标
            width (int): 区域宽度（像素）
            height (int): 区域高度（像素）

        Notes:
            - 缓冲区大小需与 width*height*2 字节匹配
            - ISR-safe: 否
        ==========================================
        Copy pixel buffer to display at given location.

        Args:
            buffer (bytes): Pixel data buffer (already 565-encoded)
            x (int): Top-left X coordinate
            y (int): Top-left Y coordinate
            width (int): Width in pixels
            height (int): Height in pixels

        Notes:
            - Buffer must match width*height*2 bytes
            - ISR-safe: No
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._write(None, buffer)

    def rect(self, x, y, w, h, color):
        """
        绘制矩形边框

        Args:
            x (int): 矩形左上角 X 坐标
            y (int): 矩形左上角 Y 坐标
            w (int): 矩形宽度（像素）
            h (int): 矩形高度（像素）
            color (int): 565 编码颜色值

        Notes:
            - ISR-safe: 否
        ==========================================
        Draw rectangle outline at given location and size.

        Args:
            x (int): Top-left X coordinate
            y (int): Top-left Y coordinate
            w (int): Width in pixels
            h (int): Height in pixels
            color (int): 565 encoded color

        Notes:
            - ISR-safe: No
        """
        self.hline(x, y, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        self.hline(x, y + h - 1, w, color)

    def fill_rect(self, x, y, width, height, color):
        """
        绘制填充矩形
        使用分块写入以控制内存占用。

        Args:
            x (int): 矩形左上角 X 坐标
            y (int): 矩形左上角 Y 坐标
            width (int): 矩形宽度（像素）
            height (int): 矩形高度（像素）
            color (int): 565 编码颜色值

        Notes:
            - 使用 _BUFFER_SIZE 分块，避免一次性分配过大 buffer
            - ISR-safe: 否
        ==========================================
        Draw a filled rectangle at given location.

        Args:
            x (int): Top-left X coordinate
            y (int): Top-left Y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color

        Notes:
            - Uses _BUFFER_SIZE chunking to avoid large memory allocation
            - ISR-safe: No
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        # 计算完整块和剩余像素数
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        pixel = _encode_pixel(color)
        # 手动控制 CS 和 DC 以避免每次 _write 切换
        if self.cs:
            self.cs.off()
        self.dc.on()
        # 按块写入像素数据
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self._write(None, data)
        # 写入剩余不足一块的像素
        if rest:
            self._write(None, pixel * rest)

        if self.cs:
            self.cs.on()

    def fill(self, color):
        """
        使用指定颜色填充整个屏幕

        Args:
            color (int): 565 编码颜色值

        Notes:
            - ISR-safe: 否
        ==========================================
        Fill the entire screen with specified color.

        Args:
            color (int): 565 encoded color

        Notes:
            - ISR-safe: No
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def line(self, x0, y0, x1, y1, color):
        """
        使用 Bresenham 算法绘制直线
        包含超时保护以防止死循环。

        Args:
            x0 (int): 起点 X 坐标
            y0 (int): 起点 Y 坐标
            x1 (int): 终点 X 坐标
            y1 (int): 终点 Y 坐标
            color (int): 565 编码颜色值

        Notes:
            - 若斜率大于 1，交换 x/y 以减少循环次数
            - 包含超时保护（基于像素总数的安全上限）
            - ISR-safe: 否
        ==========================================
        Draw a line using Bresenham algorithm.
        Includes timeout protection to prevent infinite loops.

        Args:
            x0 (int): Start point X coordinate
            y0 (int): Start point Y coordinate
            x1 (int): End point X coordinate
            y1 (int): End point Y coordinate
            color (int): 565 encoded color

        Notes:
            - Swaps x/y when slope > 1 to reduce iterations
            - Includes timeout protection (safe upper bound based on pixel count)
            - ISR-safe: No
        """
        # Bresenham 直线算法
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        # 安全计数器，防止死循环
        safety = (dx + 1) * 2
        while x0 <= x1 and safety > 0:
            safety = safety - 1
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def vscrdef(self, tfa, vsa, bfa):
        """
        设置垂直滚动区域定义

        示例（135x240 屏幕）：tfa=40, vsa=240, bfa=40。
        显示区上方 40 行、中间 240 行可滚动、下方 40 行——可写入不可见区域
        然后通过 vscsad() 将其滚动到可见区域。

        Args:
            tfa (int): 顶部固定区域（像素行数）
            vsa (int): 垂直滚动区域（像素行数）
            bfa (int): 底部固定区域（像素行数）

        Notes:
            - ISR-safe: 否
        ==========================================
        Set Vertical Scrolling Definition.

        Example (135x240 display): tfa=40, vsa=240, bfa=40.
        40 lines above visible area, 240 lines scrollable, 40 lines below.
        Write to off-screen areas and scroll them into view with vscsad().

        Args:
            tfa (int): Top Fixed Area in lines
            vsa (int): Vertical Scrolling Area in lines
            bfa (int): Bottom Fixed Area in lines

        Notes:
            - ISR-safe: No
        """
        self._write(self.VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa):
        """
        设置垂直滚动起始地址 (RAM 中的起始行)

        定义帧内存中哪一行应显示在顶部固定区域之后的第一行位置。

        示例:
            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)

        Args:
            vssa (int): 垂直滚动起始地址

        Notes:
            - ISR-safe: 否
        ==========================================
        Set Vertical Scroll Start Address of RAM.

        Defines which line in Frame Memory is displayed as the first
        line after the Top Fixed Area.

        Args:
            vssa (int): Vertical Scrolling Start Address

        Notes:
            - ISR-safe: No
        """
        self._write(self.VSCSAD, struct.pack(">H", vssa))

    def _text8(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        内部方法 - 绘制 8 位宽字符（高度 8 或 16）

        Args:
            font: 字体模块，需包含 FIRST, LAST, WIDTH, HEIGHT, FONT 属性
            text (str): 要绘制的文本
            x0 (int): 起始列
            y0 (int): 起始行
            color (int): 前景色（565 编码）
            background (int): 背景色（565 编码）

        Notes:
            - ISR-safe: 否
            - 假设字体模块包含有效的 FIRST/LAST/WIDTH/HEIGHT/FONT 属性
        ==========================================
        Internal method - draw 8-bit wide characters (height 8 or 16).

        Args:
            font: Font module with FIRST, LAST, WIDTH, HEIGHT, FONT attrs
            text (str): Text to draw
            x0 (int): Start column
            y0 (int): Start row
            color (int): Foreground color (565 encoded)
            background (int): Background color (565 encoded)

        Notes:
            - ISR-safe: No
            - Assumes font module has valid FIRST/LAST/WIDTH/HEIGHT/FONT
        """
        for char in text:
            ch = ord(char)
            if font.FIRST <= ch < font.LAST and x0 + font.WIDTH <= self.width and y0 + font.HEIGHT <= self.height:
                # 根据字体高度确定绘制次数
                if font.HEIGHT == 8:
                    passes = 1
                    size = 8
                    each = 0
                else:
                    passes = 2
                    size = 16
                    each = 8

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = struct.pack(
                        ">64H",
                        color if font.FONT[idx] & _BIT7 else background,
                        color if font.FONT[idx] & _BIT6 else background,
                        color if font.FONT[idx] & _BIT5 else background,
                        color if font.FONT[idx] & _BIT4 else background,
                        color if font.FONT[idx] & _BIT3 else background,
                        color if font.FONT[idx] & _BIT2 else background,
                        color if font.FONT[idx] & _BIT1 else background,
                        color if font.FONT[idx] & _BIT0 else background,
                        color if font.FONT[idx + 1] & _BIT7 else background,
                        color if font.FONT[idx + 1] & _BIT6 else background,
                        color if font.FONT[idx + 1] & _BIT5 else background,
                        color if font.FONT[idx + 1] & _BIT4 else background,
                        color if font.FONT[idx + 1] & _BIT3 else background,
                        color if font.FONT[idx + 1] & _BIT2 else background,
                        color if font.FONT[idx + 1] & _BIT1 else background,
                        color if font.FONT[idx + 1] & _BIT0 else background,
                        color if font.FONT[idx + 2] & _BIT7 else background,
                        color if font.FONT[idx + 2] & _BIT6 else background,
                        color if font.FONT[idx + 2] & _BIT5 else background,
                        color if font.FONT[idx + 2] & _BIT4 else background,
                        color if font.FONT[idx + 2] & _BIT3 else background,
                        color if font.FONT[idx + 2] & _BIT2 else background,
                        color if font.FONT[idx + 2] & _BIT1 else background,
                        color if font.FONT[idx + 2] & _BIT0 else background,
                        color if font.FONT[idx + 3] & _BIT7 else background,
                        color if font.FONT[idx + 3] & _BIT6 else background,
                        color if font.FONT[idx + 3] & _BIT5 else background,
                        color if font.FONT[idx + 3] & _BIT4 else background,
                        color if font.FONT[idx + 3] & _BIT3 else background,
                        color if font.FONT[idx + 3] & _BIT2 else background,
                        color if font.FONT[idx + 3] & _BIT1 else background,
                        color if font.FONT[idx + 3] & _BIT0 else background,
                        color if font.FONT[idx + 4] & _BIT7 else background,
                        color if font.FONT[idx + 4] & _BIT6 else background,
                        color if font.FONT[idx + 4] & _BIT5 else background,
                        color if font.FONT[idx + 4] & _BIT4 else background,
                        color if font.FONT[idx + 4] & _BIT3 else background,
                        color if font.FONT[idx + 4] & _BIT2 else background,
                        color if font.FONT[idx + 4] & _BIT1 else background,
                        color if font.FONT[idx + 4] & _BIT0 else background,
                        color if font.FONT[idx + 5] & _BIT7 else background,
                        color if font.FONT[idx + 5] & _BIT6 else background,
                        color if font.FONT[idx + 5] & _BIT5 else background,
                        color if font.FONT[idx + 5] & _BIT4 else background,
                        color if font.FONT[idx + 5] & _BIT3 else background,
                        color if font.FONT[idx + 5] & _BIT2 else background,
                        color if font.FONT[idx + 5] & _BIT1 else background,
                        color if font.FONT[idx + 5] & _BIT0 else background,
                        color if font.FONT[idx + 6] & _BIT7 else background,
                        color if font.FONT[idx + 6] & _BIT6 else background,
                        color if font.FONT[idx + 6] & _BIT5 else background,
                        color if font.FONT[idx + 6] & _BIT4 else background,
                        color if font.FONT[idx + 6] & _BIT3 else background,
                        color if font.FONT[idx + 6] & _BIT2 else background,
                        color if font.FONT[idx + 6] & _BIT1 else background,
                        color if font.FONT[idx + 6] & _BIT0 else background,
                        color if font.FONT[idx + 7] & _BIT7 else background,
                        color if font.FONT[idx + 7] & _BIT6 else background,
                        color if font.FONT[idx + 7] & _BIT5 else background,
                        color if font.FONT[idx + 7] & _BIT4 else background,
                        color if font.FONT[idx + 7] & _BIT3 else background,
                        color if font.FONT[idx + 7] & _BIT2 else background,
                        color if font.FONT[idx + 7] & _BIT1 else background,
                        color if font.FONT[idx + 7] & _BIT0 else background,
                    )
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8)

                x0 += 8

    def _text16(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        内部方法 - 绘制 16 位宽字符（高度 16 或 32）

        Args:
            font: 字体模块，需包含 FIRST, LAST, WIDTH, HEIGHT, FONT 属性
            text (str): 要绘制的文本
            x0 (int): 起始列
            y0 (int): 起始行
            color (int): 前景色（565 编码）
            background (int): 背景色（565 编码）

        Notes:
            - ISR-safe: 否
            - 假设字体模块包含有效的 FIRST/LAST/WIDTH/HEIGHT/FONT 属性
        ==========================================
        Internal method - draw 16-bit wide characters (height 16 or 32).

        Args:
            font: Font module with FIRST, LAST, WIDTH, HEIGHT, FONT attrs
            text (str): Text to draw
            x0 (int): Start column
            y0 (int): Start row
            color (int): Foreground color (565 encoded)
            background (int): Background color (565 encoded)

        Notes:
            - ISR-safe: No
            - Assumes font module has valid FIRST/LAST/WIDTH/HEIGHT/FONT
        """
        for char in text:
            ch = ord(char)
            if font.FIRST <= ch < font.LAST and x0 + font.WIDTH <= self.width and y0 + font.HEIGHT <= self.height:
                each = 16
                # 根据字体高度确定绘制次数
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = struct.pack(
                        ">128H",
                        color if font.FONT[idx] & _BIT7 else background,
                        color if font.FONT[idx] & _BIT6 else background,
                        color if font.FONT[idx] & _BIT5 else background,
                        color if font.FONT[idx] & _BIT4 else background,
                        color if font.FONT[idx] & _BIT3 else background,
                        color if font.FONT[idx] & _BIT2 else background,
                        color if font.FONT[idx] & _BIT1 else background,
                        color if font.FONT[idx] & _BIT0 else background,
                        color if font.FONT[idx + 1] & _BIT7 else background,
                        color if font.FONT[idx + 1] & _BIT6 else background,
                        color if font.FONT[idx + 1] & _BIT5 else background,
                        color if font.FONT[idx + 1] & _BIT4 else background,
                        color if font.FONT[idx + 1] & _BIT3 else background,
                        color if font.FONT[idx + 1] & _BIT2 else background,
                        color if font.FONT[idx + 1] & _BIT1 else background,
                        color if font.FONT[idx + 1] & _BIT0 else background,
                        color if font.FONT[idx + 2] & _BIT7 else background,
                        color if font.FONT[idx + 2] & _BIT6 else background,
                        color if font.FONT[idx + 2] & _BIT5 else background,
                        color if font.FONT[idx + 2] & _BIT4 else background,
                        color if font.FONT[idx + 2] & _BIT3 else background,
                        color if font.FONT[idx + 2] & _BIT2 else background,
                        color if font.FONT[idx + 2] & _BIT1 else background,
                        color if font.FONT[idx + 2] & _BIT0 else background,
                        color if font.FONT[idx + 3] & _BIT7 else background,
                        color if font.FONT[idx + 3] & _BIT6 else background,
                        color if font.FONT[idx + 3] & _BIT5 else background,
                        color if font.FONT[idx + 3] & _BIT4 else background,
                        color if font.FONT[idx + 3] & _BIT3 else background,
                        color if font.FONT[idx + 3] & _BIT2 else background,
                        color if font.FONT[idx + 3] & _BIT1 else background,
                        color if font.FONT[idx + 3] & _BIT0 else background,
                        color if font.FONT[idx + 4] & _BIT7 else background,
                        color if font.FONT[idx + 4] & _BIT6 else background,
                        color if font.FONT[idx + 4] & _BIT5 else background,
                        color if font.FONT[idx + 4] & _BIT4 else background,
                        color if font.FONT[idx + 4] & _BIT3 else background,
                        color if font.FONT[idx + 4] & _BIT2 else background,
                        color if font.FONT[idx + 4] & _BIT1 else background,
                        color if font.FONT[idx + 4] & _BIT0 else background,
                        color if font.FONT[idx + 5] & _BIT7 else background,
                        color if font.FONT[idx + 5] & _BIT6 else background,
                        color if font.FONT[idx + 5] & _BIT5 else background,
                        color if font.FONT[idx + 5] & _BIT4 else background,
                        color if font.FONT[idx + 5] & _BIT3 else background,
                        color if font.FONT[idx + 5] & _BIT2 else background,
                        color if font.FONT[idx + 5] & _BIT1 else background,
                        color if font.FONT[idx + 5] & _BIT0 else background,
                        color if font.FONT[idx + 6] & _BIT7 else background,
                        color if font.FONT[idx + 6] & _BIT6 else background,
                        color if font.FONT[idx + 6] & _BIT5 else background,
                        color if font.FONT[idx + 6] & _BIT4 else background,
                        color if font.FONT[idx + 6] & _BIT3 else background,
                        color if font.FONT[idx + 6] & _BIT2 else background,
                        color if font.FONT[idx + 6] & _BIT1 else background,
                        color if font.FONT[idx + 6] & _BIT0 else background,
                        color if font.FONT[idx + 7] & _BIT7 else background,
                        color if font.FONT[idx + 7] & _BIT6 else background,
                        color if font.FONT[idx + 7] & _BIT5 else background,
                        color if font.FONT[idx + 7] & _BIT4 else background,
                        color if font.FONT[idx + 7] & _BIT3 else background,
                        color if font.FONT[idx + 7] & _BIT2 else background,
                        color if font.FONT[idx + 7] & _BIT1 else background,
                        color if font.FONT[idx + 7] & _BIT0 else background,
                        color if font.FONT[idx + 8] & _BIT7 else background,
                        color if font.FONT[idx + 8] & _BIT6 else background,
                        color if font.FONT[idx + 8] & _BIT5 else background,
                        color if font.FONT[idx + 8] & _BIT4 else background,
                        color if font.FONT[idx + 8] & _BIT3 else background,
                        color if font.FONT[idx + 8] & _BIT2 else background,
                        color if font.FONT[idx + 8] & _BIT1 else background,
                        color if font.FONT[idx + 8] & _BIT0 else background,
                        color if font.FONT[idx + 9] & _BIT7 else background,
                        color if font.FONT[idx + 9] & _BIT6 else background,
                        color if font.FONT[idx + 9] & _BIT5 else background,
                        color if font.FONT[idx + 9] & _BIT4 else background,
                        color if font.FONT[idx + 9] & _BIT3 else background,
                        color if font.FONT[idx + 9] & _BIT2 else background,
                        color if font.FONT[idx + 9] & _BIT1 else background,
                        color if font.FONT[idx + 9] & _BIT0 else background,
                        color if font.FONT[idx + 10] & _BIT7 else background,
                        color if font.FONT[idx + 10] & _BIT6 else background,
                        color if font.FONT[idx + 10] & _BIT5 else background,
                        color if font.FONT[idx + 10] & _BIT4 else background,
                        color if font.FONT[idx + 10] & _BIT3 else background,
                        color if font.FONT[idx + 10] & _BIT2 else background,
                        color if font.FONT[idx + 10] & _BIT1 else background,
                        color if font.FONT[idx + 10] & _BIT0 else background,
                        color if font.FONT[idx + 11] & _BIT7 else background,
                        color if font.FONT[idx + 11] & _BIT6 else background,
                        color if font.FONT[idx + 11] & _BIT5 else background,
                        color if font.FONT[idx + 11] & _BIT4 else background,
                        color if font.FONT[idx + 11] & _BIT3 else background,
                        color if font.FONT[idx + 11] & _BIT2 else background,
                        color if font.FONT[idx + 11] & _BIT1 else background,
                        color if font.FONT[idx + 11] & _BIT0 else background,
                        color if font.FONT[idx + 12] & _BIT7 else background,
                        color if font.FONT[idx + 12] & _BIT6 else background,
                        color if font.FONT[idx + 12] & _BIT5 else background,
                        color if font.FONT[idx + 12] & _BIT4 else background,
                        color if font.FONT[idx + 12] & _BIT3 else background,
                        color if font.FONT[idx + 12] & _BIT2 else background,
                        color if font.FONT[idx + 12] & _BIT1 else background,
                        color if font.FONT[idx + 12] & _BIT0 else background,
                        color if font.FONT[idx + 13] & _BIT7 else background,
                        color if font.FONT[idx + 13] & _BIT6 else background,
                        color if font.FONT[idx + 13] & _BIT5 else background,
                        color if font.FONT[idx + 13] & _BIT4 else background,
                        color if font.FONT[idx + 13] & _BIT3 else background,
                        color if font.FONT[idx + 13] & _BIT2 else background,
                        color if font.FONT[idx + 13] & _BIT1 else background,
                        color if font.FONT[idx + 13] & _BIT0 else background,
                        color if font.FONT[idx + 14] & _BIT7 else background,
                        color if font.FONT[idx + 14] & _BIT6 else background,
                        color if font.FONT[idx + 14] & _BIT5 else background,
                        color if font.FONT[idx + 14] & _BIT4 else background,
                        color if font.FONT[idx + 14] & _BIT3 else background,
                        color if font.FONT[idx + 14] & _BIT2 else background,
                        color if font.FONT[idx + 14] & _BIT1 else background,
                        color if font.FONT[idx + 14] & _BIT0 else background,
                        color if font.FONT[idx + 15] & _BIT7 else background,
                        color if font.FONT[idx + 15] & _BIT6 else background,
                        color if font.FONT[idx + 15] & _BIT5 else background,
                        color if font.FONT[idx + 15] & _BIT4 else background,
                        color if font.FONT[idx + 15] & _BIT3 else background,
                        color if font.FONT[idx + 15] & _BIT2 else background,
                        color if font.FONT[idx + 15] & _BIT1 else background,
                        color if font.FONT[idx + 15] & _BIT0 else background,
                    )
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8)
            x0 += font.WIDTH

    def text(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        使用位图字体在指定位置绘制文本
        根据字体宽度自动选择 8 位或 16 位渲染路径。

        Args:
            font: 字体模块，需包含 WIDTH, HEIGHT 等属性
            text (str): 要绘制的文本
            x0 (int): 起始列
            y0 (int): 起始行
            color (int): 前景色（565 编码），默认 WHITE
            background (int): 背景色（565 编码），默认 BLACK

        Notes:
            - 支持 8 位宽和 16 位宽位图字体
            - ISR-safe: 否
        ==========================================
        Draw text on display using bitmap font.
        Automatically selects 8-bit or 16-bit rendering path based on font width.

        Args:
            font: Font module with WIDTH, HEIGHT etc.
            text (str): Text to draw
            x0 (int): Start column
            y0 (int): Start row
            color (int): Foreground color (565 encoded), default WHITE
            background (int): Background color (565 encoded), default BLACK

        Notes:
            - Supports 8-bit and 16-bit wide bitmap fonts
            - ISR-safe: No
        """
        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, color, background)
        else:
            self._text16(font, text, x0, y0, color, background)

    def bitmap(self, bitmap, x, y, index=0):
        """
        在指定位置绘制位图图像

        Args:
            bitmap: 位图模块，需包含 HEIGHT, WIDTH, BPP, BITMAP, PALETTE 属性
            x (int): 起始列
            y (int): 起始行
            index (int): 位图调色板索引偏移，默认 0

        Notes:
            - 整个位图一次性打包到内存，大位图可能分配较大 buffer
            - ISR-safe: 否
        ==========================================
        Draw a bitmap at the specified column and row.

        Args:
            bitmap: Bitmap module with HEIGHT, WIDTH, BPP, BITMAP, PALETTE attrs
            x (int): Start column
            y (int): Start row
            index (int): Bitmap palette index offset, default 0

        Notes:
            - Entire bitmap packed into memory at once; large bitmaps may use significant buffer
            - ISR-safe: No
        """
        bitmap_size = bitmap.HEIGHT * bitmap.WIDTH
        buffer_len = bitmap_size * 2
        buffer = bytearray(buffer_len)
        # 计算起始位偏移
        bs_bit = bitmap.BPP * bitmap_size * index if index > 0 else 0

        for i in range(0, buffer_len, 2):
            color_index = 0
            # 按 BPP 位深度提取颜色索引
            for _ in range(bitmap.BPP):
                color_index <<= 1
                color_index |= (bitmap.BITMAP[bs_bit // 8] & 1 << (7 - (bs_bit % 8))) > 0
                bs_bit += 1

            color = bitmap.PALETTE[color_index]
            buffer[i + 1] = (color & 0xFF00) >> 8
            buffer[i] = color & 0xFF

        to_col = x + bitmap.WIDTH - 1
        to_row = y + bitmap.HEIGHT - 1
        if self.width > to_col and self.height > to_row:
            self._set_window(x, y, to_col, to_row)
            self._write(None, buffer)

    def write(self, font, string, x, y, fg=WHITE, bg=BLACK):
        """
        使用转换后的 TrueType 字体绘制字符串

        Args:
            font: 转换后的字体模块，需包含 HEIGHT, MAX_WIDTH, MAP, OFFSET_WIDTH, OFFSETS, WIDTHS, BITMAPS
            string (str): 要绘制的字符串
            x (int): 起始列
            y (int): 起始行
            fg (int): 前景色（565 编码），默认 WHITE
            bg (int): 背景色（565 编码），默认 BLACK

        Notes:
            - 不存在的字符会被静默跳过
            - ISR-safe: 否
        ==========================================
        Draw a string using a converted TrueType font.

        Args:
            font: Converted font module with HEIGHT, MAX_WIDTH, MAP, OFFSET_WIDTH, OFFSETS, WIDTHS, BITMAPS
            string (str): String to draw
            x (int): Start column
            y (int): Start row
            fg (int): Foreground color (565 encoded), default WHITE
            bg (int): Background color (565 encoded), default BLACK

        Notes:
            - Missing characters are silently skipped
            - ISR-safe: No
        """
        buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
        buffer = bytearray(buffer_len)
        fg_hi = (fg & 0xFF00) >> 8
        fg_lo = fg & 0xFF

        bg_hi = (bg & 0xFF00) >> 8
        bg_lo = bg & 0xFF

        for character in string:
            try:
                # 查找字符在字体映射表中的索引
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                if font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]

                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]

                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT * 2

                for i in range(0, buffer_needed, 2):
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        buffer[i] = fg_hi
                        buffer[i + 1] = fg_lo
                    else:
                        buffer[i] = bg_hi
                        buffer[i + 1] = bg_lo

                    bs_bit += 1

                to_col = x + char_width - 1
                to_row = y + font.HEIGHT - 1
                if self.width > to_col and self.height > to_row:
                    self._set_window(x, y, to_col, to_row)
                    self._write(None, buffer[:buffer_needed])

                x += char_width

            except ValueError:
                # 字符不在字体映射表中，跳过
                pass

    def write_width(self, font, string):
        """
        计算使用指定字体绘制字符串所需的像素宽度

        Args:
            font: 字体模块，需包含 MAP 和 WIDTHS 属性
            string (str): 要测量的字符串

        Returns:
            int: 字符串占用的像素宽度

        Notes:
            - ISR-safe: 否
        ==========================================
        Calculate the pixel width of a string using the specified font.

        Args:
            font: Font module with MAP and WIDTHS attrs
            string (str): String to measure

        Returns:
            int: Pixel width of the string

        Notes:
            - ISR-safe: No
        """
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]
            except ValueError:
                # 字符不在字体映射表中，跳过
                pass

        return width

    def deinit(self):
        """
        释放硬件资源
        关闭显示并将所有控制引脚设为高阻态以安全释放 GPIO。

        Notes:
            - 调用后不再对显示器进行任何操作
            - ISR-safe: 否
        ==========================================
        Release hardware resources.
        Turn off display and set control pins to high-impedance for safe GPIO release.

        Notes:
            - No further operations on display after calling this
            - ISR-safe: No
        """
        # 关闭显示
        self._write(self.DISPOFF)
        time.sleep_ms(10)
        # 进入睡眠模式以降低功耗
        self.sleep_mode(True)
        self._log("ST7789V deinitialized")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
