# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/18 下午2:15
# @Author  : peter-l5
# @File    : sh1107.py
# @Description : SH1107 OLED显示驱动，支持I2C和SPI接口，提供基本的绘图功能。
# @License : MIT
__version__ = "v319"
__author__ = "peter-l5"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
from micropython import const
import time

try:
    import framebuf2 as framebuf

    _fb_variant = 2
except:
    import framebuf

    _fb_variant = 1
print("SH1107: framebuf is ", ("standard" if _fb_variant ==
      1 else "extended"))

# ======================================== 全局变量 ============================================
# SH1107命令常量定义
_LOW_COLUMN_ADDRESS = const(0x00)      # 低列地址设置
_HIGH_COLUMN_ADDRESS = const(0x10)     # 高列地址设置
_MEM_ADDRESSING_MODE = const(0x20)     # 内存寻址模式设置
_SET_CONTRAST = const(0x8100)          # 对比度设置命令（双字节）
_SET_SEGMENT_REMAP = const(0xA0)       # 段重映射设置
_SET_MULTIPLEX_RATIO = const(0xA800)   # 多路复用比率设置（双字节）
_SET_NORMAL_INVERSE = const(0xA6)      # 正常/反色显示设置
_SET_DISPLAY_OFFSET = const(0xD300)    # 显示偏移设置（双字节）
_SET_DC_DC_CONVERTER_SF = const(0xAD81) # DC-DC转换器设置（双字节）
_SET_DISPLAY_OFF = const(0xAE)         # 关闭显示
_SET_DISPLAY_ON = const(0xAF)          # 开启显示
_SET_PAGE_ADDRESS = const(0xB0)        # 页地址设置
_SET_SCAN_DIRECTION = const(0xC0)      # 扫描方向设置
_SET_DISP_CLK_DIV = const(0xD550)      # 显示时钟分频设置（双字节）
_SET_DIS_PRECHARGE = const(0xD922)     # 预充电周期设置（双字节）
_SET_VCOM_DSEL_LEVEL = const(0xDB35)   # VCOMH电压级别设置（双字节）
_SET_DISPLAY_START_LINE = const(0xDC00) # 显示起始行设置（双字节）

# ======================================== 自定义类 ============================================
class SH1107(framebuf.FrameBuffer):
    """
    【中文：SH1107 OLED驱动基类，继承自FrameBuffer，提供显示缓冲区管理和基本绘图方法】
    Attributes:
        width (int): 显示宽度（像素），旋转后可能交换
        height (int): 显示高度（像素），旋转后可能交换
        external_vcc (bool): 是否使用外部VCC供电
        delay_ms (int): 操作延迟时间（毫秒）
        flip_flag (bool): 当前是否翻转显示
        rotate90 (bool): 是否旋转90度或270度
        rotate (int): 旋转角度（0/90/180/270）
        inverse (bool): 当前是否反色显示
        pages (int): 总页数（高度//8）
        row_width (int): 每行字节数（宽度//8）
        bufsize (int): 缓冲区大小（pages * width）
        displaybuf (bytearray): 显示缓冲区原始字节数组
        displaybuf_mv (memoryview): 显示缓冲区内存视图
        pages_to_update (int): 需要更新的页位掩码
        _is_awake (bool): 屏幕是否处于唤醒状态

    Methods:
        init_display(): 初始化显示参数
        poweron(): 开启显示
        poweroff(): 关闭显示
        sleep(): 进入/退出睡眠模式
        flip(): 设置/切换显示翻转
        display_start_line(): 设置显示起始行
        contrast(): 设置对比度
        invert(): 设置/切换反色显示
        show(): 将缓冲区更新到屏幕
        pixel(): 获取/设置像素点
        text(): 绘制文本
        line(): 绘制直线
        hline(): 绘制水平线
        vline(): 绘制垂直线
        fill(): 填充全屏
        blit(): 位块传输
        scroll(): 滚动显示
        fill_rect(): 填充矩形
        rect(): 绘制矩形
        ellipse(): 绘制椭圆
        poly(): 绘制多边形
        large_text(): 绘制大字体文本（需扩展framebuf）
        circle(): 绘制圆（需扩展framebuf）
        triangle(): 绘制三角形（需扩展framebuf）
        register_updates(): 注册需要更新的页面
        reset(): 硬件复位

    Notes:
        - 支持旋转（0/90/180/270度），旋转后宽度/高度互换
        - 使用页面更新机制，只刷新修改的区域以提升性能

    ==========================================
    English description
    Attributes:
        width (int): Display width in pixels (may swap after rotation)
        height (int): Display height in pixels (may swap after rotation)
        external_vcc (bool): Whether using external VCC power
        delay_ms (int): Operation delay in milliseconds
        flip_flag (bool): Current flip state
        rotate90 (bool): Whether rotated by 90 or 270 degrees
        rotate (int): Rotation angle (0/90/180/270)
        inverse (bool): Current inverse display state
        pages (int): Total number of pages (height//8)
        row_width (int): Bytes per row (width//8)
        bufsize (int): Buffer size (pages * width)
        displaybuf (bytearray): Raw display buffer bytearray
        displaybuf_mv (memoryview): Memory view of display buffer
        pages_to_update (int): Bitmask of pages needing update
        _is_awake (bool): Whether display is awake

    Methods:
        init_display(): Initialize display parameters
        poweron(): Turn on display
        poweroff(): Turn off display
        sleep(): Enter/exit sleep mode
        flip(): Set/toggle display flip
        display_start_line(): Set display start line
        contrast(): Set contrast
        invert(): Set/toggle inverse display
        show(): Update screen from buffer
        pixel(): Get/set pixel
        text(): Draw text
        line(): Draw line
        hline(): Draw horizontal line
        vline(): Draw vertical line
        fill(): Fill entire screen
        blit(): Block transfer
        scroll(): Scroll display
        fill_rect(): Fill rectangle
        rect(): Draw rectangle
        ellipse(): Draw ellipse
        poly(): Draw polygon
        large_text(): Draw large text (requires extended framebuf)
        circle(): Draw circle (requires extended framebuf)
        triangle(): Draw triangle (requires extended framebuf)
        register_updates(): Register pages that need update
        reset(): Hardware reset

    Notes:
        - Rotation supported (0/90/180/270), width/height swap accordingly
        - Page update mechanism improves performance by updating only changed areas
    """

    def __init__(self, width: int, height: int, external_vcc: bool, delay_ms: int = 200, rotate: int = 0) -> None:
        # 参数验证
        if width is None or height is None or external_vcc is None:
            raise ValueError("width, height, external_vcc cannot be None")
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("width and height must be integers")
        if not isinstance(external_vcc, bool):
            raise TypeError("external_vcc must be boolean")
        if not isinstance(delay_ms, int):
            raise TypeError("delay_ms must be integer")
        if delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        if rotate not in (0, 90, 180, 270):
            raise ValueError("rotate must be 0, 90, 180, or 270")

        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.delay_ms = delay_ms
        self.flip_flag = False
        self.rotate90 = rotate == 90 or rotate == 270
        self.rotate = rotate
        self.inverse = False
        if self.rotate90:
            self.width, self.height = self.height, self.width
        self.pages = self.height // 8
        self.row_width = self.width // 8
        self.bufsize = self.pages * self.width
        self.displaybuf = bytearray(self.bufsize)
        self.displaybuf_mv = memoryview(self.displaybuf)
        self.pages_to_update = 0
        self._is_awake = False
        if self.rotate90:
            super().__init__(self.displaybuf, self.width, self.height, framebuf.MONO_VLSB)
        else:
            super().__init__(self.displaybuf, self.width, self.height, framebuf.MONO_HMSB)
        self.init_display()

    def init_display(self) -> None:
        """
        【中文：初始化显示控制器，设置显示参数并清屏】
        Args:
            无
        Raises:
            无
        Notes:
            无

        ==========================================
        English description
        Args:
            None
        Raises:
            None
        Notes:
            None
        """
        multiplex_ratio = 0x7F if (self.height == 128) else 0x3F
        self.reset()
        self.poweroff()
        self.fill(0)
        self.write_command(
            (_SET_MULTIPLEX_RATIO | multiplex_ratio).to_bytes(2, "big"))
        self.write_command((_MEM_ADDRESSING_MODE | (
            0x00 if self.rotate90 else 0x01)).to_bytes(1, "big"))
        self.write_command(_SET_PAGE_ADDRESS.to_bytes(
            1, "big"))
        self.write_command(_SET_DC_DC_CONVERTER_SF.to_bytes(2, "big"))
        self.write_command(_SET_DISP_CLK_DIV.to_bytes(2, "big"))
        self.write_command(_SET_VCOM_DSEL_LEVEL.to_bytes(2, "big"))
        self.write_command(_SET_DIS_PRECHARGE.to_bytes(2, "big"))
        self.contrast(0)
        self.invert(False)

        self.flip(self.flip_flag)
        self.poweron()

    def poweron(self) -> None:
        """
        【中文：开启显示（唤醒屏幕）】
        Args:
            无
        Raises:
            无
        Notes:
            调用后延迟delay_ms毫秒等待稳定

        ==========================================
        English description
        Args:
            None
        Raises:
            None
        Notes:
            Delay of delay_ms milliseconds after power-on for stabilization
        """
        self.write_command(_SET_DISPLAY_ON.to_bytes(1, "big"))
        self._is_awake = True

        time.sleep_ms(self.delay_ms)

    def poweroff(self) -> None:
        """
        【中文：关闭显示（睡眠模式）】
        Args:
            无
        Raises:
            无
        Notes:
            无

        ==========================================
        English description
        Args:
            None
        Raises:
            None
        Notes:
            None
        """
        self.write_command(_SET_DISPLAY_OFF.to_bytes(1, "big"))
        self._is_awake = False

    def sleep(self, value: bool = True) -> None:
        """
        【中文：控制睡眠模式】
        Args:
            value (bool): True进入睡眠，False唤醒
        Raises:
            TypeError: 参数类型错误
        Notes:
            无

        ==========================================
        English description
        Args:
            value (bool): True to sleep, False to wake
        Raises:
            TypeError: if value is not boolean
        Notes:
            None
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, bool):
            raise TypeError("value must be boolean")
        if value == True:
            self.poweroff()
        else:
            self.poweron()

    @property
    def is_awake(self) -> bool:
        """
        【中文：获取屏幕唤醒状态】
        Args:
            无
        Returns:
            bool: True表示唤醒，False表示睡眠

        ==========================================
        English description
        Args:
            None
        Returns:
            bool: True if awake, False if sleeping
        """
        return self._is_awake

    def flip(self, flag: bool | None = None, update: bool = True) -> None:
        """
        【中文：设置/切换显示翻转】
        Args:
            flag (bool | None): 翻转状态，None则取反当前值
            update (bool): 是否立即更新显示
        Raises:
            TypeError: 参数类型错误
        Notes:
            翻转包括段重映射和扫描方向调整

        ==========================================
        English description
        Args:
            flag (bool | None): Flip state, None to toggle current
            update (bool): Whether to update display immediately
        Raises:
            TypeError: if parameter types are incorrect
        Notes:
            Flip includes segment remap and scan direction adjustment
        """
        if update is None:
            raise ValueError("update cannot be None")
        if not isinstance(update, bool):
            raise TypeError("update must be boolean")
        if flag is not None and not isinstance(flag, bool):
            raise TypeError("flag must be boolean or None")

        if flag is None:
            flag = not self.flip_flag
        if self.height == 128 and self.width == 128:
            row_offset = 0x00
        elif self.rotate90:
            row_offset = 0x60
        else:
            row_offset = 0x20 if (self.rotate == 180) ^ flag else 0x60
        remap = 0x00 if (self.rotate in (90, 180)) ^ flag else 0x01
        direction = 0x08 if (self.rotate in (180, 270)) ^ flag else 0x00
        self.write_command(
            (_SET_DISPLAY_OFFSET | row_offset).to_bytes(2, "big"))
        self.write_command((_SET_SEGMENT_REMAP | remap).to_bytes(1, "big"))
        self.write_command(
            (_SET_SCAN_DIRECTION | direction).to_bytes(1, "big"))
        self.flip_flag = flag
        if update:
            self.show(True)

    def display_start_line(self, value: int) -> None:
        """
        【中文：设置显示起始行】
        Args:
            value (int): 起始行索引，范围0-127
        Raises:
            TypeError: 参数类型错误
            ValueError: 值超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            value (int): Start line index, range 0-127
        Raises:
            TypeError: if value is not integer
            ValueError: if value out of range
        Notes:
            None
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError("value must be integer")
        if value < 0 or value > 0x7F:
            raise ValueError("display start line must be 0-127")
        self.write_command(
            (_SET_DISPLAY_START_LINE | (value & 0x7F)).to_bytes(2, "big"))

    def contrast(self, contrast: int) -> None:
        """
        【中文：设置显示对比度】
        Args:
            contrast (int): 对比度值，范围0-255
        Raises:
            TypeError: 参数类型错误
            ValueError: 值超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            contrast (int): Contrast value, range 0-255
        Raises:
            TypeError: if contrast is not integer
            ValueError: if contrast out of range
        Notes:
            None
        """
        if contrast is None:
            raise ValueError("contrast cannot be None")
        if not isinstance(contrast, int):
            raise TypeError("contrast must be integer")
        if contrast < 0 or contrast > 0xFF:
            raise ValueError("contrast must be 0-255")
        self.write_command(
            (_SET_CONTRAST | (contrast & 0xFF)).to_bytes(2, "big"))

    def invert(self, invert: bool | None = None) -> None:
        """
        【中文：设置/切换反色显示】
        Args:
            invert (bool | None): True反色，False正常，None切换当前值
        Raises:
            TypeError: 参数类型错误
        Notes:
            无

        ==========================================
        English description
        Args:
            invert (bool | None): True inverse, False normal, None toggle
        Raises:
            TypeError: if invert is not boolean or None
        Notes:
            None
        """
        if invert is not None and not isinstance(invert, bool):
            raise TypeError("invert must be boolean or None")
        if invert == None:
            invert = not self.inverse
        self.write_command(
            (_SET_NORMAL_INVERSE | (invert & 1)).to_bytes(1, "big"))
        self.inverse = invert

    def show(self, full_update: bool = False) -> None:
        """
        【中文：将缓冲区内容刷新到屏幕】
        Args:
            full_update (bool): True强制更新所有页，False只更新标记的页
        Raises:
            TypeError: 参数类型错误
        Notes:
            根据旋转模式采用不同的数据发送顺序

        ==========================================
        English description
        Args:
            full_update (bool): True to force update all pages, False update only marked pages
        Raises:
            TypeError: if full_update is not boolean
        Notes:
            Data sending order depends on rotation mode
        """
        if full_update is None:
            raise ValueError("full_update cannot be None")
        if not isinstance(full_update, bool):
            raise TypeError("full_update must be boolean")
        (w, p, db_mv) = (self.width, self.pages, self.displaybuf_mv)
        current_page = 1
        if full_update:
            pages_to_update = (1 << p) - 1
        else:
            pages_to_update = self.pages_to_update
        if self.rotate90:
            buffer_3Bytes = bytearray(3)
            buffer_3Bytes[1] = _LOW_COLUMN_ADDRESS
            buffer_3Bytes[2] = _HIGH_COLUMN_ADDRESS
            for page in range(p):
                if pages_to_update & current_page:
                    buffer_3Bytes[0] = _SET_PAGE_ADDRESS | page
                    self.write_command(buffer_3Bytes)
                    page_start = w * page
                    self.write_data(db_mv[page_start: page_start + w])
                current_page <<= 1
        else:
            row_bytes = w // 8
            buffer_2Bytes = bytearray(2)
            for start_row in range(0, p * 8, 8):
                if pages_to_update & current_page:
                    for row in range(start_row, start_row + 8):

                        buffer_2Bytes[0] = row & 0x0F
                        buffer_2Bytes[1] = _HIGH_COLUMN_ADDRESS | (row >> 4)
                        self.write_command(buffer_2Bytes)
                        slice_start = row * row_bytes
                        self.write_data(
                            db_mv[slice_start: slice_start + row_bytes])
                current_page <<= 1
        self.pages_to_update = 0

    def pixel(self, x: int, y: int, c: int | None = None) -> int | None:
        """
        【中文：获取或设置像素点】
        Args:
            x (int): x坐标
            y (int): y坐标
            c (int | None): 颜色（0或1），None表示获取
        Returns:
            int | None: 获取时返回当前颜色，设置时返回None
        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标或颜色值超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x (int): x coordinate
            y (int): y coordinate
            c (int | None): Color (0 or 1), None for get
        Returns:
            int | None: Current color if getting, None if setting
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if coordinate or color out of range
        Notes:
            None
        """
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("pixel coordinates out of range")
        if c is not None:
            if not isinstance(c, int):
                raise TypeError("c must be integer or None")
            if c not in (0, 1):
                raise ValueError("c must be 0 or 1")
        if c is None:
            return super().pixel(x, y)
        else:
            super().pixel(x, y, c)
            page = y // 8
            self.pages_to_update |= 1 << page

    def text(self, text: str, x: int, y: int, c: int = 1) -> None:
        """
        【中文：绘制文本】
        Args:
            text (str): 要绘制的字符串
            x (int): 起始x坐标
            y (int): 起始y坐标
            c (int): 颜色，0或1
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数无效或超出范围
        Notes:
            自动注册更新的页面（字符高度8像素）

        ==========================================
        English description
        Args:
            text (str): String to draw
            x (int): Start x coordinate
            y (int): Start y coordinate
            c (int): Color, 0 or 1
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters invalid or out of range
        Notes:
            Automatically registers affected pages (character height 8 pixels)
        """
        if text is None or x is None or y is None or c is None:
            raise ValueError("text, x, y, c cannot be None")
        if not isinstance(text, str):
            raise TypeError("text must be string")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(c, int):
            raise TypeError("x, y, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("start coordinates out of range")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().text(text, x, y, c)
        self.register_updates(y, y + 7)

    def line(self, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
        """
        【中文：绘制直线】
        Args:
            x0, y0: 起点坐标
            x1, y1: 终点坐标
            c (int): 颜色
        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标或颜色值超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x0, y0: start point coordinates
            x1, y1: end point coordinates
            c (int): color
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if coordinate or color out of range
        Notes:
            None
        """
        if x0 is None or y0 is None or x1 is None or y1 is None or c is None:
            raise ValueError("x0, y0, x1, y1, c cannot be None")
        if not isinstance(x0, int) or not isinstance(y0, int) or not isinstance(x1, int) or not isinstance(y1, int) or not isinstance(c, int):
            raise TypeError("coordinates and c must be integers")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().line(x0, y0, x1, y1, c)
        self.register_updates(y0, y1)

    def hline(self, x: int, y: int, w: int, c: int) -> None:
        """
        【中文：绘制水平线】
        Args:
            x, y: 起点坐标
            w (int): 线段长度
            c (int): 颜色
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x, y: start coordinates
            w (int): length
            c (int): color
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters out of range
        Notes:
            None
        """
        if x is None or y is None or w is None or c is None:
            raise ValueError("x, y, w, c cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(w, int) or not isinstance(c, int):
            raise TypeError("x, y, w, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("start coordinates out of range")
        if w <= 0 or x + w > self.width:
            raise ValueError("invalid line length")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().hline(x, y, w, c)
        self.register_updates(y)

    def vline(self, x: int, y: int, h: int, c: int) -> None:
        """
        【中文：绘制垂直线】
        Args:
            x, y: 起点坐标
            h (int): 线段高度
            c (int): 颜色
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x, y: start coordinates
            h (int): height
            c (int): color
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters out of range
        Notes:
            None
        """
        if x is None or y is None or h is None or c is None:
            raise ValueError("x, y, h, c cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(h, int) or not isinstance(c, int):
            raise TypeError("x, y, h, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("start coordinates out of range")
        if h <= 0 or y + h > self.height:
            raise ValueError("invalid line height")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().vline(x, y, h, c)
        self.register_updates(y, y + h - 1)

    def fill(self, c: int) -> None:
        """
        【中文：填充整个屏幕】
        Args:
            c (int): 颜色
        Raises:
            TypeError: 参数类型错误
            ValueError: 颜色值超出范围
        Notes:
            标记所有页需要更新

        ==========================================
        English description
        Args:
            c (int): color
        Raises:
            TypeError: if c is not integer
            ValueError: if c out of range
        Notes:
            Marks all pages for update
        """
        if c is None:
            raise ValueError("c cannot be None")
        if not isinstance(c, int):
            raise TypeError("c must be integer")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().fill(c)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf: framebuf.FrameBuffer, x: int, y: int, key: int = -1, palette=None) -> None:
        """
        【中文：位块传输，将另一个帧缓冲区内容复制到当前缓冲区】
        Args:
            fbuf (framebuf.FrameBuffer): 源帧缓冲区
            x, y (int): 目标左上角坐标
            key (int): 透明色索引，-1表示不使用透明
            palette: 调色板（未使用）
        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标或参数无效
        Notes:
            注册受影响的页面（整个高度范围）

        ==========================================
        English description
        Args:
            fbuf (framebuf.FrameBuffer): source framebuffer
            x, y (int): target top-left coordinates
            key (int): transparent color index, -1 for no transparency
            palette: palette (unused)
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if coordinates or parameters invalid
        Notes:
            Registers affected pages (entire height range)
        """
        if fbuf is None or x is None or y is None or key is None:
            raise ValueError("fbuf, x, y, key cannot be None")
        if not isinstance(fbuf, framebuf.FrameBuffer):
            raise TypeError("fbuf must be FrameBuffer")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(key, int):
            raise TypeError("x, y, key must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("target coordinates out of range")
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y + self.height)

    def scroll(self, x: int, y: int) -> None:
        """
        【中文：滚动显示内容】
        Args:
            x (int): 水平滚动像素数
            y (int): 垂直滚动像素数
        Raises:
            TypeError: 参数类型错误
        Notes:
            标记所有页需要更新

        ==========================================
        English description
        Args:
            x (int): horizontal scroll pixels
            y (int): vertical scroll pixels
        Raises:
            TypeError: if parameters are not integers
        Notes:
            Marks all pages for update
        """
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be integers")
        super().scroll(x, y)
        self.pages_to_update = (1 << self.pages) - 1

    def fill_rect(self, x: int, y: int, w: int, h: int, c: int) -> None:
        """
        【中文：绘制并填充矩形】
        Args:
            x, y: 左上角坐标
            w, h: 宽度和高度
            c (int): 颜色
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x, y: top-left coordinates
            w, h: width and height
            c (int): color
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters out of range
        Notes:
            None
        """
        if x is None or y is None or w is None or h is None or c is None:
            raise ValueError("x, y, w, h, c cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(w, int) or not isinstance(h, int) or not isinstance(c, int):
            raise TypeError("x, y, w, h, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("start coordinates out of range")
        if w <= 0 or x + w > self.width or h <= 0 or y + h > self.height:
            raise ValueError("invalid rectangle dimensions")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        try:
            super().fill_rect(x, y, w, h, c)
        except:
            super().rect(x, y, w, h, c, f=True)
        self.register_updates(y, y + h - 1)

    def rect(self, x: int, y: int, w: int, h: int, c: int, f: bool | None = None) -> None:
        """
        【中文：绘制矩形边框（可选填充）】
        Args:
            x, y: 左上角坐标
            w, h: 宽度和高度
            c (int): 颜色
            f (bool | None): True填充，False边框，None默认边框
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数超出范围
        Notes:
            无

        ==========================================
        English description
        Args:
            x, y: top-left coordinates
            w, h: width and height
            c (int): color
            f (bool | None): True fill, False outline, None default outline
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters out of range
        Notes:
            None
        """
        if x is None or y is None or w is None or h is None or c is None:
            raise ValueError("x, y, w, h, c cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(w, int) or not isinstance(h, int) or not isinstance(c, int):
            raise TypeError("x, y, w, h, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("start coordinates out of range")
        if w <= 0 or x + w > self.width or h <= 0 or y + h > self.height:
            raise ValueError("invalid rectangle dimensions")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        if f is not None and not isinstance(f, bool):
            raise TypeError("f must be boolean or None")
        if f == None or f == False:
            super().rect(x, y, w, h, c)
        else:
            try:
                super().rect(x, y, w, h, c, f)
            except:
                super().fill_rect(x, y, w, h, c)
        self.register_updates(y, y + h - 1)

    def ellipse(self, x: int, y: int, xr: int, yr: int, c: int, *args, **kwargs) -> None:
        """
        【中文：绘制椭圆】
        Args:
            x, y: 中心坐标
            xr, yr: x轴半径和y轴半径
            c (int): 颜色
            *args, **kwargs: 其他参数（传递给父类）
        Raises:
            TypeError: 参数类型错误
            ValueError: 参数超出范围
        Notes:
            注册受影响页面（垂直范围）

        ==========================================
        English description
        Args:
            x, y: center coordinates
            xr, yr: x-radius and y-radius
            c (int): color
            *args, **kwargs: additional arguments (passed to parent)
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if parameters out of range
        Notes:
            Registers affected pages (vertical range)
        """
        if x is None or y is None or xr is None or yr is None or c is None:
            raise ValueError("x, y, xr, yr, c cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(xr, int) or not isinstance(yr, int) or not isinstance(c, int):
            raise TypeError("x, y, xr, yr, c must be integers")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("center coordinates out of range")
        if xr <= 0 or yr <= 0 or x - xr < 0 or x + xr >= self.width or y - yr < 0 or y + yr >= self.height:
            raise ValueError("ellipse exceeds display bounds")
        if c not in (0, 1):
            raise ValueError("c must be 0 or 1")
        super().ellipse(x, y, xr, yr, c, *args, **kwargs)
        self.register_updates(y - yr, y + yr)

    def poly(self, *args, **kwargs) -> None:
        """
        【中文：绘制多边形】
        Args:
            *args, **kwargs: 传递给父类的参数
        Raises:
            无（依赖父类验证）
        Notes:
            标记所有页需要更新（简化处理）

        ==========================================
        English description
        Args:
            *args, **kwargs: arguments passed to parent
        Raises:
            None (relies on parent validation)
        Notes:
            Marks all pages for update (simplified)
        """
        super().poly(*args, **kwargs)
        self.pages_to_update = (1 << self.pages) - 1

    if _fb_variant == 2:

        def large_text(self, s: str, x: int, y: int, m: int, c: int = 1, r: int = 0, *args, **kwargs) -> None:
            """
            【中文：绘制大字体文本（需要扩展framebuf v206+）】
            Args:
                s (str): 字符串
                x, y (int): 起始坐标
                m (int): 放大倍数
                c (int): 颜色
                r (int): 旋转角度
                *args, **kwargs: 其他参数
            Raises:
                TypeError: 参数类型错误
                ValueError: 参数超出范围
                Exception: 扩展framebuf版本不足
            Notes:
                无

            ==========================================
            English description
            Args:
                s (str): string
                x, y (int): start coordinates
                m (int): magnification factor
                c (int): color
                r (int): rotation angle
                *args, **kwargs: additional arguments
            Raises:
                TypeError: if parameters are of incorrect type
                ValueError: if parameters out of range
                Exception: if extended framebuf version insufficient
            Notes:
                None
            """
            if s is None or x is None or y is None or m is None or c is None or r is None:
                raise ValueError("s, x, y, m, c, r cannot be None")
            if not isinstance(s, str):
                raise TypeError("s must be string")
            if not isinstance(x, int) or not isinstance(y, int) or not isinstance(m, int) or not isinstance(c, int) or not isinstance(r, int):
                raise TypeError("x, y, m, c, r must be integers")
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                raise ValueError("start coordinates out of range")
            if m <= 0:
                raise ValueError("magnification must be positive")
            if c not in (0, 1):
                raise ValueError("c must be 0 or 1")
            if r not in (0, 90, 180, 270):
                raise ValueError("rotation must be 0, 90, 180, or 270")
            try:
                super().large_text(s, x, y, m, c, r, *args, **kwargs)
            except:
                raise Exception("extended framebuffer v206+ required")
            h = (8 * m) * (1 if r is None or r %
                           360 // 90 in (0, 2) else len(s))
            self.register_updates(y, y + h - 1)

        def circle(self, x: int, y: int, radius: int, c: int, f: bool | None = None) -> None:
            """
            【中文：绘制圆】
            Args:
                x, y: 圆心坐标
                radius (int): 半径
                c (int): 颜色
                f (bool | None): True填充，False边框，None边框
            Raises:
                TypeError: 参数类型错误
                ValueError: 参数超出范围
            Notes:
                无

            ==========================================
            English description
            Args:
                x, y: center coordinates
                radius (int): radius
                c (int): color
                f (bool | None): True fill, False outline, None outline
            Raises:
                TypeError: if parameters are of incorrect type
                ValueError: if parameters out of range
            Notes:
                None
            """
            if x is None or y is None or radius is None or c is None:
                raise ValueError("x, y, radius, c cannot be None")
            if not isinstance(x, int) or not isinstance(y, int) or not isinstance(radius, int) or not isinstance(c, int):
                raise TypeError("x, y, radius, c must be integers")
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                raise ValueError("center coordinates out of range")
            if radius <= 0 or x - radius < 0 or x + radius >= self.width or y - radius < 0 or y + radius >= self.height:
                raise ValueError("circle exceeds display bounds")
            if c not in (0, 1):
                raise ValueError("c must be 0 or 1")
            if f is not None and not isinstance(f, bool):
                raise TypeError("f must be boolean or None")
            super().circle(x, y, radius, c, f)
            self.register_updates(y - radius, y + radius)

        def triangle(self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, c: int, f: bool | None = None) -> None:
            """
            【中文：绘制三角形】
            Args:
                x0,y0,x1,y1,x2,y2: 三个顶点坐标
                c (int): 颜色
                f (bool | None): True填充，False边框，None边框
            Raises:
                TypeError: 参数类型错误
                ValueError: 坐标或颜色值超出范围
            Notes:
                无

            ==========================================
            English description
            Args:
                x0,y0,x1,y1,x2,y2: three vertex coordinates
                c (int): color
                f (bool | None): True fill, False outline, None outline
            Raises:
                TypeError: if parameters are of incorrect type
                ValueError: if coordinates or color out of range
            Notes:
                None
            """
            if x0 is None or y0 is None or x1 is None or y1 is None or x2 is None or y2 is None or c is None:
                raise ValueError("all coordinates and c cannot be None")
            if not isinstance(x0, int) or not isinstance(y0, int) or not isinstance(x1, int) or not isinstance(y1, int) or not isinstance(x2, int) or not isinstance(y2, int) or not isinstance(c, int):
                raise TypeError("coordinates and c must be integers")
            if c not in (0, 1):
                raise ValueError("c must be 0 or 1")
            if f is not None and not isinstance(f, bool):
                raise TypeError("f must be boolean or None")
            super().triangle(x0, y0, x1, y1, x2, y2, c, f)
            self.register_updates(min(y0, y1, y2), max(y0, y1, y2))

    def register_updates(self, y0: int, y1: int | None = None) -> None:
        """
        【中文：注册需要更新的页面】
        Args:
            y0 (int): 起始y坐标
            y1 (int | None): 结束y坐标，None表示仅y0所在页
        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标超出范围
        Notes:
            内部方法，用于标记修改区域对应的页面

        ==========================================
        English description
        Args:
            y0 (int): start y coordinate
            y1 (int | None): end y coordinate, None for single page at y0
        Raises:
            TypeError: if parameters are of incorrect type
            ValueError: if coordinates out of range
        Notes:
            Internal method to mark pages corresponding to modified area
        """
        if y0 is None:
            raise ValueError("y0 cannot be None")
        if not isinstance(y0, int):
            raise TypeError("y0 must be integer")
        if y0 < 0 or y0 >= self.height:
            raise ValueError("y0 out of range")
        if y1 is not None:
            if not isinstance(y1, int):
                raise TypeError("y1 must be integer or None")
            if y1 < 0 or y1 >= self.height:
                raise ValueError("y1 out of range")
        y1 = min((y1 if y1 is not None else y0), self.height - 1)

        start_page = y0 // 8
        end_page = (y1 // 8) if (y1 is not None) else start_page

        if start_page > end_page:
            start_page, end_page = end_page, start_page

        if end_page >= 0:
            if start_page < 0:
                start_page = 0
            for page in range(start_page, end_page + 1):
                self.pages_to_update |= 1 << page

    def reset(self, res) -> None:
        """
        【中文：硬件复位】
        Args:
            res: 复位引脚对象（具有高低电平控制功能）
        Raises:
            ValueError: 如果res为None
        Notes:
            无

        ==========================================
        English description
        Args:
            res: reset pin object (with high/low control)
        Raises:
            ValueError: if res is None
        Notes:
            None
        """
        if res is not None:
            res(1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(20)
            res(1)
            time.sleep_ms(20)


class SH1107_I2C(SH1107):
    """
    【中文：基于I2C接口的SH1107驱动】
    Attributes:
        i2c (I2C): I2C总线对象
        address (int): 设备I2C地址
        res: 复位引脚对象（可选）

    Methods:
        write_command(): 通过I2C发送命令
        write_data(): 通过I2C发送数据
        reset(): 硬件复位

    Notes:
        默认I2C地址为0x3D

    ==========================================
    English description
    Attributes:
        i2c (I2C): I2C bus object
        address (int): I2C device address
        res: reset pin object (optional)

    Methods:
        write_command(): Send command via I2C
        write_data(): Send data via I2C
        reset(): Hardware reset

    Notes:
        Default I2C address is 0x3D
    """

    def __init__(
        self, width: int, height: int, i2c, res=None, address: int = 0x3D, rotate: int = 0, external_vcc: bool = False, delay_ms: int = 200
    ) -> None:
        # 参数验证
        if width is None or height is None or i2c is None or address is None or rotate is None or external_vcc is None or delay_ms is None:
            raise ValueError("width, height, i2c, address, rotate, external_vcc, delay_ms cannot be None")
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("width and height must be integers")
        if not isinstance(address, int):
            raise TypeError("address must be integer")
        if address < 0x3C or address > 0x3F:   # 常见SH1107地址范围
            raise ValueError("I2C address out of typical range 0x3C-0x3F")
        if not isinstance(rotate, int):
            raise TypeError("rotate must be integer")
        if rotate not in (0, 90, 180, 270):
            raise ValueError("rotate must be 0, 90, 180, or 270")
        if not isinstance(external_vcc, bool):
            raise TypeError("external_vcc must be boolean")
        if not isinstance(delay_ms, int):
            raise TypeError("delay_ms must be integer")
        if delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        if res is not None:
            # 假设res是Pin对象，不进行具体类型检查
            pass

        self.i2c = i2c
        self.address = address
        self.res = res
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_command(self, command_list: bytes) -> None:
        """
        【中文：通过I2C发送命令字节序列】
        Args:
            command_list (bytes or bytearray): 命令字节序列
        Raises:
            TypeError: 参数类型错误
        Notes:
            在数据前附加控制字节0x00

        ==========================================
        English description
        Args:
            command_list (bytes or bytearray): command byte sequence
        Raises:
            TypeError: if command_list is not bytes or bytearray
        Notes:
            Prepends control byte 0x00 to data
        """
        if command_list is None:
            raise ValueError("command_list cannot be None")
        if not isinstance(command_list, (bytes, bytearray)):
            raise TypeError("command_list must be bytes or bytearray")
        self.i2c.writeto(self.address, b"\x00" + command_list)

    def write_data(self, buf: bytes) -> None:
        """
        【中文：通过I2C发送数据字节序列】
        Args:
            buf (bytes or bytearray or memoryview): 数据字节序列
        Raises:
            TypeError: 参数类型错误
        Notes:
            在数据前附加控制字节0x40

        ==========================================
        English description
        Args:
            buf (bytes or bytearray or memoryview): data byte sequence
        Raises:
            TypeError: if buf is not bytes, bytearray, or memoryview
        Notes:
            Prepends control byte 0x40 to data
        """
        if buf is None:
            raise ValueError("buf cannot be None")
        if not isinstance(buf, (bytes, bytearray, memoryview)):
            raise TypeError("buf must be bytes, bytearray, or memoryview")
        self.i2c.writevto(self.address, (b"\x40", buf))

    def reset(self) -> None:
        """
        【中文：执行硬件复位】
        Args:
            无
        Raises:
            无
        Notes:
            调用父类reset方法，传入复位引脚对象

        ==========================================
        English description
        Args:
            None
        Raises:
            None
        Notes:
            Calls parent reset method with reset pin
        """
        super().reset(self.res)


class SH1107_SPI(SH1107):
    """
    【中文：基于SPI接口的SH1107驱动】
    Attributes:
        spi (SPI): SPI总线对象
        dc (Pin): 数据/命令选择引脚
        res (Pin): 复位引脚（可选）
        cs (Pin): 片选引脚（可选）

    Methods:
        write_command(): 通过SPI发送命令
        write_data(): 通过SPI发送数据
        reset(): 硬件复位

    Notes:
        - 当cs存在时，每次传输前自动拉低片选
        - 数据/命令引脚在发送前设置正确电平

    ==========================================
    English description
    Attributes:
        spi (SPI): SPI bus object
        dc (Pin): Data/Command select pin
        res (Pin): Reset pin (optional)
        cs (Pin): Chip select pin (optional)

    Methods:
        write_command(): Send command via SPI
        write_data(): Send data via SPI
        reset(): Hardware reset

    Notes:
        - When cs is present, it is automatically pulled low before each transfer
        - DC pin is set to appropriate level before sending
    """

    def __init__(self, width: int, height: int, spi, dc, res=None, cs=None, rotate: int = 0, external_vcc: bool = False, delay_ms: int = 0) -> None:
        # 参数验证
        if width is None or height is None or spi is None or dc is None or rotate is None or external_vcc is None or delay_ms is None:
            raise ValueError("width, height, spi, dc, rotate, external_vcc, delay_ms cannot be None")
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("width and height must be integers")
        if not isinstance(rotate, int):
            raise TypeError("rotate must be integer")
        if rotate not in (0, 90, 180, 270):
            raise ValueError("rotate must be 0, 90, 180, or 270")
        if not isinstance(external_vcc, bool):
            raise TypeError("external_vcc must be boolean")
        if not isinstance(delay_ms, int):
            raise TypeError("delay_ms must be integer")
        if delay_ms < 0:
            raise ValueError("delay_ms must be non-negative")
        # spi, dc, res, cs 为外设对象，不进行具体类型检查

        dc.init(dc.OUT, value=0)
        if res is not None:
            res.init(res.OUT, value=0)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        super().__init__(width, height, external_vcc, delay_ms, rotate)

    def write_command(self, cmd: bytes) -> None:
        """
        【中文：通过SPI发送命令字节序列】
        Args:
            cmd (bytes): 命令字节序列
        Raises:
            TypeError: 参数类型错误
        Notes:
            - 如果cs存在，传输前后自动控制片选
            - dc置低表示命令模式

        ==========================================
        English description
        Args:
            cmd (bytes): command byte sequence
        Raises:
            TypeError: if cmd is not bytes
        Notes:
            - If cs exists, it is controlled automatically before/after transfer
            - DC low indicates command mode
        """
        if cmd is None:
            raise ValueError("cmd cannot be None")
        if not isinstance(cmd, bytes):
            raise TypeError("cmd must be bytes")
        if self.cs is not None:
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(cmd)
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(cmd)

    def write_data(self, buf: bytes) -> None:
        """
        【中文：通过SPI发送数据字节序列】
        Args:
            buf (bytes): 数据字节序列
        Raises:
            TypeError: 参数类型错误
        Notes:
            - 如果cs存在，传输前后自动控制片选
            - dc置高表示数据模式

        ==========================================
        English description
        Args:
            buf (bytes): data byte sequence
        Raises:
            TypeError: if buf is not bytes
        Notes:
            - If cs exists, it is controlled automatically before/after transfer
            - DC high indicates data mode
        """
        if buf is None:
            raise ValueError("buf cannot be None")
        if not isinstance(buf, bytes):
            raise TypeError("buf must be bytes")
        if self.cs is not None:
            self.cs(1)
            self.dc(1)
            self.cs(0)
            self.spi.write(buf)
            self.cs(1)
        else:
            self.dc(1)
            self.spi.write(buf)

    def reset(self) -> None:
        """
        【中文：执行硬件复位】
        Args:
            无
        Raises:
            无
        Notes:
            调用父类reset方法，传入复位引脚对象

        ==========================================
        English description
        Args:
            None
        Raises:
            None
        Notes:
            Calls parent reset method with reset pin
        """
        super().reset(self.res)

# ======================================== 初始化配置 ===========================================
# （无初始化代码）

# ========================================  主程序  ============================================
# （无主程序逻辑）