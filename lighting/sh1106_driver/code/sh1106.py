# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午6:00
# @Author  : robert-hh
# @File    : sh1106.py
# @Description : SH1106 OLED驱动，支持I2C和SPI接口，实现显示、绘图、旋转、对比度等功能 参考自:https://github.com/robert-hh/SH1106
# @License : MIT
__version__ = "0.1.0"
__author__ = "robert-hh"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from micropython import const
import utime as time
import framebuf

# ======================================== 全局变量 ============================================

# 对比度设置命令
_SET_CONTRAST = const(0x81)
# 显示正常/反色设置命令
_SET_NORM_INV = const(0xA6)
# 显示开关命令
_SET_DISP = const(0xAE)
# 扫描方向设置命令
_SET_SCAN_DIR = const(0xC0)
# 段重映射设置命令
_SET_SEG_REMAP = const(0xA0)
# 低位列地址命令
_LOW_COLUMN_ADDRESS = const(0x00)
# 高位列地址命令
_HIGH_COLUMN_ADDRESS = const(0x10)
# 页地址设置命令
_SET_PAGE_ADDRESS = const(0xB0)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SH1106(framebuf.FrameBuffer):
    """
    SH1106 OLED 基础驱动类
    Attributes:
        width: 屏幕宽度
        height: 屏幕高度
        external_vcc: 是否外部供电
        flip_en: 是否翻转使能
        rotate90: 是否旋转90度
        pages: 屏幕页数
        bufsize: 缓冲区大小
        renderbuf: 渲染缓冲区
        displaybuf: 显示缓冲区
        pages_to_update: 需要更新的页
        delay: 上电延时

    Methods:
        __init__: 构造函数
        write_cmd: 写命令（抽象）
        write_data: 写数据（抽象）
        init_display: 初始化显示屏
        poweroff: 关闭显示
        poweron: 打开显示
        flip: 翻转屏幕
        sleep: 进入/退出休眠
        contrast: 设置对比度
        invert: 设置反色
        show: 刷新显示
        pixel: 画点
        text: 显示文字
        line: 画线
        hline: 画水平线
        vline: 画垂直线
        fill: 填充全屏
        blit: 叠加图像
        scroll: 滚动屏幕
        fill_rect: 填充矩形
        rect: 画矩形
        ellipse: 画椭圆
        register_updates: 注册需要更新的页
        reset: 复位屏幕

    Notes:
        为抽象类，需子类实现write_cmd和write_data

    ==========================================
    SH1106 OLED base driver class
    Attributes:
        width: Screen width
        height: Screen height
        external_vcc: Use external VCC
        flip_en: Flip enable
        rotate90: Rotate 90 degrees
        pages: Screen pages
        bufsize: Buffer size
        renderbuf: Render buffer
        displaybuf: Display buffer
        pages_to_update: Pages need to update
        delay: Power on delay

    Methods:
        __init__: Constructor
        write_cmd: Write command (abstract)
        write_data: Write data (abstract)
        init_display: Initialize display
        poweroff: Power off display
        poweron: Power on display
        flip: Flip display
        sleep: Enter/exit sleep mode
        contrast: Set contrast
        invert: Set inverse display
        show: Update display
        pixel: Draw pixel
        text: Draw text
        line: Draw line
        hline: Draw horizontal line
        vline: Draw vertical line
        fill: Fill screen
        blit: Blit buffer
        scroll: Scroll screen
        fill_rect: Fill rectangle
        rect: Draw rectangle
        ellipse: Draw ellipse
        register_updates: Register update pages
        reset: Reset display

    Notes:
        Abstract class, write_cmd and write_data must be implemented in subclass
    """

    def __init__(self, width: int, height: int, external_vcc: bool, rotate: int = 0) -> None:
        """
        构造函数，初始化显示参数和缓冲区
        Args:
            width (int): 屏幕宽度，必须为正整数
            height (int): 屏幕高度，必须为正整数且能被8整除
            external_vcc (bool): 是否使用外部VCC供电
            rotate (int): 旋转角度，可选0, 90, 180, 270

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出合法范围

        Notes:
            无

        ==========================================
        Constructor, initialize display parameters and buffer
        Args:
            width (int): Screen width, must be positive integer
            height (int): Screen height, must be positive integer and divisible by 8
            external_vcc (bool): Use external VCC supply
            rotate (int): Rotation angle, can be 0, 90, 180, 270

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Parameter value out of valid range

        Notes:
            None
        """
        # 参数验证
        if width is None:
            raise ValueError("width cannot be None")
        if not isinstance(width, int) or width <= 0:
            raise TypeError("width must be positive integer")
        if height is None:
            raise ValueError("height cannot be None")
        if not isinstance(height, int) or height <= 0 or height % 8 != 0:
            raise TypeError("height must be positive integer multiple of 8")
        if external_vcc is None:
            raise ValueError("external_vcc cannot be None")
        if not isinstance(external_vcc, bool):
            raise TypeError("external_vcc must be bool")
        if rotate is None:
            raise ValueError("rotate cannot be None")
        if not isinstance(rotate, int) or rotate not in (0, 90, 180, 270):
            raise ValueError("rotate must be 0, 90, 180, or 270")

        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.flip_en = rotate == 180 or rotate == 270
        self.rotate90 = rotate == 90 or rotate == 270
        self.pages = self.height // 8
        self.bufsize = self.pages * self.width
        self.renderbuf = bytearray(self.bufsize)
        self.pages_to_update = 0
        self.delay = 0

        if self.rotate90:
            self.displaybuf = bytearray(self.bufsize)
            super().__init__(self.renderbuf, self.height, self.width, framebuf.MONO_HMSB)
        else:
            self.displaybuf = self.renderbuf
            super().__init__(self.renderbuf, self.width, self.height, framebuf.MONO_VLSB)

        self.rotate = self.flip
        self.init_display()

    def write_cmd(self, *args, **kwargs) -> None:
        """
        写命令（抽象方法）
        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        Raises:
            NotImplementedError: 未实现

        Notes:
            必须在子类中实现

        ==========================================
        Write command (abstract method)
        Args:
            *args: Variable length arguments
            **kwargs: Keyword arguments

        Raises:
            NotImplementedError: Not implemented

        Notes:
            Must be implemented in subclass
        """
        raise NotImplementedError

    def write_data(self, *args, **kwargs) -> None:
        """
        写数据（抽象方法）
        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        Raises:
            NotImplementedError: 未实现

        Notes:
            必须在子类中实现

        ==========================================
        Write data (abstract method)
        Args:
            *args: Variable length arguments
            **kwargs: Keyword arguments

        Raises:
            NotImplementedError: Not implemented

        Notes:
            Must be implemented in subclass
        """
        raise NotImplementedError

    def init_display(self) -> None:
        """
        初始化显示屏，执行复位、清屏、上电和翻转设置
        Args:
            无

        Raises:
            无

        Notes:
            无

        ==========================================
        Initialize display, perform reset, clear, power on and flip setup
        Args:
            None

        Raises:
            None

        Notes:
            None
        """
        self.reset()
        self.fill(0)
        self.show()
        self.poweron()
        self.flip(self.flip_en)

    def poweroff(self) -> None:
        """
        关闭显示电源
        Args:
            无

        Raises:
            无

        Notes:
            无

        ==========================================
        Power off display
        Args:
            None

        Raises:
            None

        Notes:
            None
        """
        self.write_cmd(_SET_DISP | 0x00)

    def poweron(self) -> None:
        """
        打开显示电源
        Args:
            无

        Raises:
            无

        Notes:
            如果设置了上电延时，则等待指定时间

        ==========================================
        Power on display
        Args:
            None

        Raises:
            None

        Notes:
            Wait if delay is set
        """
        self.write_cmd(_SET_DISP | 0x01)
        if self.delay:
            time.sleep_ms(self.delay)

    def flip(self, flag: bool | None = None, update: bool = True) -> None:
        """
        翻转屏幕显示方向
        Args:
            flag (bool | None): 翻转标志，None表示取反当前状态
            update (bool): 是否立即刷新显示

        Raises:
            TypeError: 参数类型错误

        Notes:
            控制水平和垂直翻转

        ==========================================
        Flip display orientation
        Args:
            flag (bool | None): Flip flag, None to toggle current state
            update (bool): Update immediately

        Raises:
            TypeError: Incorrect parameter type

        Notes:
            Control horizontal and vertical flip
        """
        # 参数验证
        if flag is not None and not isinstance(flag, bool):
            raise TypeError("flag must be bool or None")
        if not isinstance(update, bool):
            raise TypeError("update must be bool")

        if flag is None:
            flag = not self.flip_en
        mir_v = flag ^ self.rotate90
        mir_h = flag
        self.write_cmd(_SET_SEG_REMAP | (0x01 if mir_v else 0x00))
        self.write_cmd(_SET_SCAN_DIR | (0x08 if mir_h else 0x00))
        self.flip_en = flag
        if update:
            self.show(True)

    def sleep(self, value: bool) -> None:
        """
        进入/退出休眠模式，参数验证逻辑：
        - 检查value是否为None
        - 检查value是否为bool类型
        """
        # 1. None检查：value不能为None
        if value is None:
            raise ValueError("sleep(): parameter 'value' cannot be None")

        # 2. 类型检查：value必须是bool类型
        if not isinstance(value, bool):
            raise TypeError("sleep(): parameter 'value' must be bool (got {})".format(type(value).__name__))

        # 核心逻辑（原函数）
        self.write_cmd(_SET_DISP | (not value))

    def contrast(self, contrast: int) -> None:
        """
        设置屏幕对比度
        Args:
            contrast (int): 对比度值，范围0~255

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出范围

        Notes:
            值越大屏幕越亮

        ==========================================
        Set display contrast
        Args:
            contrast (int): Contrast value, range 0~255

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Parameter value out of range

        Notes:
            Higher value = brighter
        """
        if contrast is None:
            raise ValueError("contrast cannot be None")
        if not isinstance(contrast, int):
            raise TypeError("contrast must be int")
        if contrast < 0 or contrast > 255:
            raise ValueError("contrast must be between 0 and 255")
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert: bool) -> None:
        """
        设置反色显示
        Args:
            invert (bool): True=反色，False=正常

        Raises:
            TypeError: 参数类型错误

        Notes:
            无

        ==========================================
        Set inverse display
        Args:
            invert (bool): True=inverse, False=normal

        Raises:
            TypeError: Incorrect parameter type

        Notes:
            None
        """
        if invert is None:
            raise ValueError("invert cannot be None")
        if not isinstance(invert, bool):
            raise TypeError("invert must be bool")
        self.write_cmd(_SET_NORM_INV | (invert & 1))

    def show(self, full_update: bool = False) -> None:
        """
        刷新显示，参数验证逻辑：
        - 检查full_update是否为None
        - 检查full_update是否为bool类型
        """
        # 1. None检查：full_update不能为None（即使有默认值，显式传入None仍需拦截）
        if full_update is None:
            raise ValueError("show(): parameter 'full_update' cannot be None")

        # 2. 类型检查：full_update必须是bool类型
        if not isinstance(full_update, bool):
            raise TypeError("show(): parameter 'full_update' must be bool (got {})".format(type(full_update).__name__))

        # 核心逻辑（原函数）
        (w, p, db, rb) = (self.width, self.pages, self.displaybuf, self.renderbuf)
        if self.rotate90:
            for i in range(self.bufsize):
                db[w * (i % p) + (i // p)] = rb[i]
        if full_update:
            pages_to_update = (1 << self.pages) - 1
        else:
            pages_to_update = self.pages_to_update
        for page in range(self.pages):
            if pages_to_update & (1 << page):
                self.write_cmd(_SET_PAGE_ADDRESS | page)
                self.write_cmd(_LOW_COLUMN_ADDRESS | 2)
                self.write_cmd(_HIGH_COLUMN_ADDRESS | 0)
                self.write_data(db[w * page : w * page + w])
        self.pages_to_update = 0
        """
        刷新显示，参数验证逻辑：
        - 检查full_update是否为None
        - 检查full_update是否为bool类型
        """
        # 1. None检查：full_update不能为None（即使有默认值，显式传入None仍需拦截）
        if full_update is None:
            raise ValueError("show(): parameter 'full_update' cannot be None")

        # 2. 类型检查：full_update必须是bool类型
        if not isinstance(full_update, bool):
            raise TypeError("show(): parameter 'full_update' must be bool (got {})".format(type(full_update).__name__))

        # 核心逻辑（原函数）
        (w, p, db, rb) = (self.width, self.pages, self.displaybuf, self.renderbuf)
        if self.rotate90:
            for i in range(self.bufsize):
                db[w * (i % p) + (i // p)] = rb[i]
        if full_update:
            pages_to_update = (1 << self.pages) - 1
        else:
            pages_to_update = self.pages_to_update
        for page in range(self.pages):
            if pages_to_update & (1 << page):
                self.write_cmd(_SET_PAGE_ADDRESS | page)
                self.write_cmd(_LOW_COLUMN_ADDRESS | 2)
                self.write_cmd(_HIGH_COLUMN_ADDRESS | 0)
                self.write_data(db[w * page : w * page + w])
        self.pages_to_update = 0

    def pixel(self, x: int, y: int, color: int | None = None) -> int | None:
        """
        画点或读取点颜色
        Args:
            x (int): X坐标，范围0~width-1
            y (int): Y坐标，范围0~height-1
            color (int | None): 颜色值（0或1），None表示读取

        Returns:
            int | None: 当color为None时返回当前点颜色（0或1），否则返回None

        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标超出范围或颜色值无效

        Notes:
            无

        ==========================================
        Draw or get pixel
        Args:
            x (int): X coordinate, range 0~width-1
            y (int): Y coordinate, range 0~height-1
            color (int | None): Color value (0 or 1), None to read

        Returns:
            int | None: Current pixel color (0 or 1) if color is None, else None

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Coordinate out of range or invalid color value

        Notes:
            None
        """
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be int")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("Coordinates out of range")
        if color is not None:
            if not isinstance(color, int):
                raise TypeError("color must be int or None")
            if color not in (0, 1):
                raise ValueError("color must be 0 or 1")
            super().pixel(x, y, color)
            page = y // 8
            self.pages_to_update |= 1 << page
            return None
        else:
            return super().pixel(x, y)

    def text(self, text: str, x: int, y: int, color: int = 1) -> None:
        """
        显示文字
        Args:
            text (str): 要显示的字符串
            x (int): 起始X坐标
            y (int): 起始Y坐标
            color (int): 颜色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标或颜色无效

        Notes:
            无

        ==========================================
        Draw text
        Args:
            text (str): String to display
            x (int): Start X coordinate
            y (int): Start Y coordinate
            color (int): Color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid coordinate or color

        Notes:
            None
        """
        if text is None:
            raise ValueError("text cannot be None")
        if not isinstance(text, str):
            raise TypeError("text must be str")
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be int")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        # 坐标范围检查由 framebuf 处理，但我们可以粗略检查
        super().text(text, x, y, color)
        self.register_updates(y, y + 7)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        """
        画线
        Args:
            x0 (int): 起点X坐标
            y0 (int): 起点Y坐标
            x1 (int): 终点X坐标
            y1 (int): 终点Y坐标
            color (int): 颜色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 颜色无效

        Notes:
            无

        ==========================================
        Draw line
        Args:
            x0 (int): Start X coordinate
            y0 (int): Start Y coordinate
            x1 (int): End X coordinate
            y1 (int): End Y coordinate
            color (int): Color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid color

        Notes:
            None
        """
        if x0 is None or y0 is None or x1 is None or y1 is None:
            raise ValueError("Coordinates cannot be None")
        if not all(isinstance(v, int) for v in (x0, y0, x1, y1)):
            raise TypeError("Coordinates must be int")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().line(x0, y0, x1, y1, color)
        self.register_updates(y0, y1)

    def hline(self, x: int, y: int, w: int, color: int) -> None:
        """
        画水平线
        Args:
            x (int): 起点X坐标
            y (int): Y坐标
            w (int): 线宽（像素数）
            color (int): 颜色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 颜色或宽度无效

        Notes:
            无

        ==========================================
        Draw horizontal line
        Args:
            x (int): Start X coordinate
            y (int): Y coordinate
            w (int): Width in pixels
            color (int): Color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid color or width

        Notes:
            None
        """
        if x is None or y is None or w is None:
            raise ValueError("x, y, w cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(w, int):
            raise TypeError("x, y, w must be int")
        if w <= 0:
            raise ValueError("w must be positive")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().hline(x, y, w, color)
        self.register_updates(y)

    def vline(self, x: int, y: int, h: int, color: int) -> None:
        """
        画垂直线
        Args:
            x (int): X坐标
            y (int): 起点Y坐标
            h (int): 高度（像素数）
            color (int): 颜色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 颜色或高度无效

        Notes:
            无

        ==========================================
        Draw vertical line
        Args:
            x (int): X coordinate
            y (int): Start Y coordinate
            h (int): Height in pixels
            color (int): Color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid color or height

        Notes:
            None
        """
        if x is None or y is None or h is None:
            raise ValueError("x, y, h cannot be None")
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(h, int):
            raise TypeError("x, y, h must be int")
        if h <= 0:
            raise ValueError("h must be positive")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().vline(x, y, h, color)
        self.register_updates(y, y + h - 1)

    def fill(self, color: int) -> None:
        """
        全屏填充
        Args:
            color (int): 填充色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 颜色无效

        Notes:
            无

        ==========================================
        Fill full screen
        Args:
            color (int): Fill color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid color

        Notes:
            None
        """
        if color is None:
            raise ValueError("color cannot be None")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().fill(color)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x: int, y: int, key: int = -1, palette=None) -> None:
        """
        叠加图像
        Args:
            fbuf: 帧缓冲对象
            x (int): 目标X坐标
            y (int): 目标Y坐标
            key (int): 透明色，默认为-1（不使用）
            palette: 调色板，默认为None

        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标无效

        Notes:
            无

        ==========================================
        Blit buffer
        Args:
            fbuf: Frame buffer object
            x (int): Target X coordinate
            y (int): Target Y coordinate
            key (int): Transparent color, default -1 (disabled)
            palette: Palette, default None

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid coordinate

        Notes:
            None
        """
        if fbuf is None:
            raise ValueError("fbuf cannot be None")
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be int")
        if not isinstance(key, int):
            raise TypeError("key must be int")
        # 其他参数检查省略
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y + self.height)

    def scroll(self, x: int, y: int) -> None:
        """
        屏幕滚动
        Args:
            x (int): 水平偏移量
            y (int): 垂直偏移量

        Raises:
            TypeError: 参数类型错误

        Notes:
            全屏刷新

        ==========================================
        Scroll screen
        Args:
            x (int): Horizontal offset
            y (int): Vertical offset

        Raises:
            TypeError: Incorrect parameter type

        Notes:
            Full screen update
        """
        if x is None or y is None:
            raise ValueError("x and y cannot be None")
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("x and y must be int")
        super().scroll(x, y)
        self.pages_to_update = (1 << self.pages) - 1

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """
        填充矩形
        Args:
            x (int): 左上角X坐标
            y (int): 左上角Y坐标
            w (int): 宽度
            h (int): 高度
            color (int): 填充色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 宽度/高度无效或颜色无效

        Notes:
            无

        ==========================================
        Fill rectangle
        Args:
            x (int): Top-left X coordinate
            y (int): Top-left Y coordinate
            w (int): Width
            h (int): Height
            color (int): Fill color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid width/height or color

        Notes:
            None
        """
        if x is None or y is None or w is None or h is None:
            raise ValueError("x, y, w, h cannot be None")
        if not all(isinstance(v, int) for v in (x, y, w, h)):
            raise TypeError("x, y, w, h must be int")
        if w <= 0 or h <= 0:
            raise ValueError("w and h must be positive")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().fill_rect(x, y, w, h, color)
        self.register_updates(y, y + h - 1)

    def rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """
        画矩形边框
        Args:
            x (int): 左上角X坐标
            y (int): 左上角Y坐标
            w (int): 宽度
            h (int): 高度
            color (int): 边框色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 宽度/高度无效或颜色无效

        Notes:
            无

        ==========================================
        Draw rectangle outline
        Args:
            x (int): Top-left X coordinate
            y (int): Top-left Y coordinate
            w (int): Width
            h (int): Height
            color (int): Outline color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid width/height or color

        Notes:
            None
        """
        if x is None or y is None or w is None or h is None:
            raise ValueError("x, y, w, h cannot be None")
        if not all(isinstance(v, int) for v in (x, y, w, h)):
            raise TypeError("x, y, w, h must be int")
        if w <= 0 or h <= 0:
            raise ValueError("w and h must be positive")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().rect(x, y, w, h, color)
        self.register_updates(y, y + h - 1)

    def ellipse(self, x: int, y: int, xr: int, yr: int, color: int) -> None:
        """
        画椭圆
        Args:
            x (int): 中心X坐标
            y (int): 中心Y坐标
            xr (int): X轴半径
            yr (int): Y轴半径
            color (int): 颜色，0或1

        Raises:
            TypeError: 参数类型错误
            ValueError: 半径无效或颜色无效

        Notes:
            无

        ==========================================
        Draw ellipse
        Args:
            x (int): Center X coordinate
            y (int): Center Y coordinate
            xr (int): X radius
            yr (int): Y radius
            color (int): Color, 0 or 1

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid radius or color

        Notes:
            None
        """
        if x is None or y is None or xr is None or yr is None:
            raise ValueError("x, y, xr, yr cannot be None")
        if not all(isinstance(v, int) for v in (x, y, xr, yr)):
            raise TypeError("x, y, xr, yr must be int")
        if xr <= 0 or yr <= 0:
            raise ValueError("xr and yr must be positive")
        if not isinstance(color, int):
            raise TypeError("color must be int")
        if color not in (0, 1):
            raise ValueError("color must be 0 or 1")
        super().ellipse(x, y, xr, yr, color)
        self.register_updates(y - yr, y + yr - 1)

    def register_updates(self, y0: int, y1: int | None = None) -> None:
        """
        注册需要更新的显示页
        Args:
            y0 (int): 起始Y坐标
            y1 (int | None): 结束Y坐标，None表示只更新y0所在页

        Raises:
            TypeError: 参数类型错误
            ValueError: 坐标无效

        Notes:
            根据Y坐标计算需要更新的页

        ==========================================
        Register pages to update
        Args:
            y0 (int): Start Y coordinate
            y1 (int | None): End Y coordinate, None means only update page of y0

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid coordinates

        Notes:
            Calculate pages by Y coordinate
        """
        if y0 is None:
            raise ValueError("y0 cannot be None")
        if not isinstance(y0, int):
            raise TypeError("y0 must be int")
        if y1 is not None and not isinstance(y1, int):
            raise TypeError("y1 must be int or None")
        # 粗略范围检查
        if y0 < 0 or y0 >= self.height:
            raise ValueError("y0 out of range")
        if y1 is not None and (y1 < 0 or y1 >= self.height):
            raise ValueError("y1 out of range")

        start_page = max(0, y0 // 8)
        end_page = max(0, y1 // 8) if y1 is not None else start_page
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        for page in range(start_page, end_page + 1):
            self.pages_to_update |= 1 << page

    def reset(self, res=None) -> None:
        """
        硬件复位屏幕，参数验证逻辑：
        - res为可选参数，允许为None（表示不使用硬件复位）
        - 若res不为None，需检查是否为Pin对象（通过是否有init方法判断）
        """
        # 1. 非None时的类型检查：res必须是Pin类实例（有init方法）
        if res is not None and not hasattr(res, "init"):
            raise TypeError("reset(): parameter 'res' must be a Pin object or None (got {})".format(type(res).__name__))

        # 核心逻辑（原函数）
        if res is not None:
            res(1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(20)
            res(1)
            time.sleep_ms(20)


class SH1106_I2C(SH1106):
    """
    SH1106 I2C接口驱动类
    Attributes:
        i2c: I2C对象
        addr: I2C地址
        res: 复位引脚
        temp: 临时数据缓冲区

    Methods:
        __init__: 构造函数
        write_cmd: I2C写命令
        write_data: I2C写数据
        reset: 复位

    Notes:
        适用于I2C接口的OLED

    ==========================================
    SH1106 I2C interface driver class
    Attributes:
        i2c: I2C object
        addr: I2C address
        res: Reset pin
        temp: Temp data buffer

    Methods:
        __init__: Constructor
        write_cmd: I2C write command
        write_data: I2C write data
        reset: Reset

    Notes:
        For I2C interface OLED
    """

    def __init__(self, width: int, height: int, i2c, res=None, addr: int = 0x3C, rotate: int = 0, external_vcc: bool = False, delay: int = 0) -> None:
        """
        构造函数，初始化I2C接口
        Args:
            width (int): 屏幕宽度
            height (int): 屏幕高度
            i2c: I2C总线对象
            res: 复位引脚（可选）
            addr (int): I2C设备地址，默认0x3C
            rotate (int): 旋转角度
            external_vcc (bool): 是否外部供电
            delay (int): 上电延时（毫秒）

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值无效

        Notes:
            无

        ==========================================
        Constructor, initialize I2C interface
        Args:
            width (int): Screen width
            height (int): Screen height
            i2c: I2C bus object
            res: Reset pin (optional)
            addr (int): I2C device address, default 0x3C
            rotate (int): Rotation angle
            external_vcc (bool): Use external VCC
            delay (int): Power on delay in ms

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid parameter value

        Notes:
            None
        """
        if i2c is None:
            raise ValueError("i2c cannot be None")
        # 简单检查 i2c 对象是否有 writeto 方法
        if not hasattr(i2c, "writeto"):
            raise TypeError("i2c must have writeto method")
        if res is not None and not hasattr(res, "init"):
            raise TypeError("res must be a Pin object or None")
        if addr is None:
            raise ValueError("addr cannot be None")
        if not isinstance(addr, int) or addr < 0x08 or addr > 0x77:
            raise ValueError("addr must be int between 0x08 and 0x77")
        if not isinstance(delay, int) or delay < 0:
            raise ValueError("delay must be non-negative int")
        self.i2c = i2c
        self.addr = addr
        self.res = res
        self.temp = bytearray(2)
        self.delay = delay
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, rotate)

    def write_cmd(self, cmd: int) -> None:
        """
        I2C写命令
        Args:
            cmd (int): 命令字节，0~255

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出范围

        Notes:
            无

        ==========================================
        I2C write command
        Args:
            cmd (int): Command byte, 0~255

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Parameter value out of range

        Notes:
            None
        """
        if cmd is None:
            raise ValueError("cmd cannot be None")
        if not isinstance(cmd, int):
            raise TypeError("cmd must be int")
        if cmd < 0 or cmd > 255:
            raise ValueError("cmd must be between 0 and 255")
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf) -> None:
        """
        I2C写数据
        Args:
            buf: 数据缓冲区（bytes或bytearray）

        Raises:
            TypeError: 参数类型错误

        Notes:
            无

        ==========================================
        I2C write data
        Args:
            buf: Data buffer (bytes or bytearray)

        Raises:
            TypeError: Incorrect parameter type

        Notes:
            None
        """
        if buf is None:
            raise ValueError("buf cannot be None")
        if not isinstance(buf, (bytes, bytearray)):
            raise TypeError("buf must be bytes or bytearray")
        self.i2c.writeto(self.addr, b"\x40" + buf)

    def reset(self) -> None:
        """
        SPI接口复位（重写父类），参数验证逻辑：
        """
        super().reset(self.res)


class SH1106_SPI(SH1106):
    """
    SH1106 SPI接口驱动类
    Attributes:
        spi: SPI对象
        dc: 数据/命令引脚
        res: 复位引脚
        cs: 片选引脚

    Methods:
        __init__: 构造函数
        write_cmd: SPI写命令
        write_data: SPI写数据
        reset: 复位

    Notes:
        适用于SPI接口的OLED

    ==========================================
    SH1106 SPI interface driver class
    Attributes:
        spi: SPI object
        dc: Data/Command pin
        res: Reset pin
        cs: Chip select pin

    Methods:
        __init__: Constructor
        write_cmd: SPI write command
        write_data: SPI write data
        reset: Reset

    Notes:
        For SPI interface OLED
    """

    def __init__(self, width: int, height: int, spi, dc, res=None, cs=None, rotate: int = 0, external_vcc: bool = False, delay: int = 0) -> None:
        """
        构造函数，初始化SPI接口
        Args:
            width (int): 屏幕宽度
            height (int): 屏幕高度
            spi: SPI总线对象
            dc: 数据/命令引脚
            res: 复位引脚（可选）
            cs: 片选引脚（可选）
            rotate (int): 旋转角度
            external_vcc (bool): 是否外部供电
            delay (int): 上电延时（毫秒）

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值无效

        Notes:
            无

        ==========================================
        Constructor, initialize SPI interface
        Args:
            width (int): Screen width
            height (int): Screen height
            spi: SPI bus object
            dc: Data/Command pin
            res: Reset pin (optional)
            cs: Chip select pin (optional)
            rotate (int): Rotation angle
            external_vcc (bool): Use external VCC
            delay (int): Power on delay in ms

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Invalid parameter value

        Notes:
            None
        """
        if spi is None:
            raise ValueError("spi cannot be None")
        if not hasattr(spi, "write"):
            raise TypeError("spi must have write method")
        if dc is None:
            raise ValueError("dc cannot be None")
        if not hasattr(dc, "init"):
            raise TypeError("dc must be a Pin object")
        if res is not None and not hasattr(res, "init"):
            raise TypeError("res must be a Pin object or None")
        if cs is not None and not hasattr(cs, "init"):
            raise TypeError("cs must be a Pin object or None")
        if not isinstance(delay, int) or delay < 0:
            raise ValueError("delay must be non-negative int")

        dc.init(dc.OUT, value=0)
        if res is not None:
            res.init(res.OUT, value=0)
        if cs is not None:
            cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        self.delay = delay
        super().__init__(width, height, external_vcc, rotate)

    def write_cmd(self, cmd: int) -> None:
        """
        SPI写命令
        Args:
            cmd (int): 命令字节，0~255

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出范围

        Notes:
            无

        ==========================================
        SPI write command
        Args:
            cmd (int): Command byte, 0~255

        Raises:
            TypeError: Incorrect parameter type
            ValueError: Parameter value out of range

        Notes:
            None
        """
        if cmd is None:
            raise ValueError("cmd cannot be None")
        if not isinstance(cmd, int):
            raise TypeError("cmd must be int")
        if cmd < 0 or cmd > 255:
            raise ValueError("cmd must be between 0 and 255")
        if self.cs is not None:
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(bytearray([cmd]))
            self.cs(1)
        else:
            self.dc(0)
            self.spi.write(bytearray([cmd]))

    def write_data(self, buf) -> None:
        """
        SPI写数据
        Args:
            buf: 数据缓冲区（bytes或bytearray）

        Raises:
            TypeError: 参数类型错误

        Notes:
            无

        ==========================================
        SPI write data
        Args:
            buf: Data buffer (bytes or bytearray)

        Raises:
            TypeError: Incorrect parameter type

        Notes:
            None
        """
        if buf is None:
            raise ValueError("buf cannot be None")
        if not isinstance(buf, (bytes, bytearray)):
            raise TypeError("buf must be bytes or bytearray")
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
        SPI接口复位（重写父类），参数验证逻辑：
        """
        super().reset(self.res)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
