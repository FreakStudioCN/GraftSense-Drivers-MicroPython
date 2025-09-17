# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/13 下午2:21   
# @Author  : 李清水            
# @File    : neopixel_matrix.py       
# @Description : WS2812矩阵驱动库

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin
# 导入framebuf模块
import framebuf
# 导入WS2812驱动模块
import neopixel
# 导入MicroPython相关模块
import micropython
from micropython import const
# 导入json模块
import json

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# WS2812 矩阵驱动类
class NeopixelMatrix(framebuf.FrameBuffer):
    """
    该类用于驱动基于 WS2812 的 LED 矩阵，支持 RGB565 图像渲染、颜色转换、局部刷新和滚动显示。

    Attributes:
        np (NeoPixel): WS2812 灯珠驱动实例。
        width (int): 矩阵宽度（像素）。
        height (int): 矩阵高度（像素）。
        layout (str): 布局类型，支持 "row" 和 "snake"。
        buffer (memoryview): RGB565 帧缓存，每像素 2 字节。
        order (str): WS2812 的 RGB 通道顺序。
        flip_h (bool): 是否水平翻转。
        flip_v (bool): 是否垂直翻转。
        rotate (int): 矩阵旋转角度（0、90、180、270）。
        _brightness (float): 显示亮度，范围 0.0–1.0。
        COLOR_CACHE (dict): 颜色转换缓存，加速重复 RGB565 转换。

    Methods:
        brightness() -> float: 获取当前亮度。
        brightness(value: float) -> None: 设置亮度并刷新缓存。
        rgb565_to_rgb888(val: int, brightness: float, order: str) -> tuple: 转换颜色。
        show(x1: int, y1: int, x2: int, y2: int) -> None: 局部或全屏刷新。
        scroll(xstep: int, ystep: int, clear_color: int, wrap: bool) -> None: 滚动显示。
        show_rgb565_image(image_data: str|dict, offset_x: int, offset_y: int) -> None: 显示 JSON 图片。
        load_rgb565_image(filename: str, offset_x: int, offset_y: int) -> None: 从文件加载图片。

    Notes:
        - 本类使用了 micropython.native 装饰器优化性能。
        - 涉及 neopixel.NeoPixel.write() 的方法属于硬件 I/O 操作，非 ISR-safe。
        - JSON 图片需符合定义的 RGB565 格式规范。

    ==========================================

    NeopixelMatrix driver for WS2812-based LED matrices.
    Provides support for RGB565 rendering, color conversion, partial refresh, and scrolling.

    Attributes:
        np (NeoPixel): WS2812 driver instance.
        width (int): matrix width in pixels.
        height (int): matrix height in pixels.
        layout (str): layout type, "row" or "snake".
        buffer (memoryview): RGB565 framebuffer.
        order (str): RGB order of WS2812 LEDs.
        flip_h (bool): horizontal flip.
        flip_v (bool): vertical flip.
        rotate (int): rotation angle (0, 90, 180, 270).
        _brightness (float): brightness scale factor 0.0–1.0.
        COLOR_CACHE (dict): cache for color conversion results.

    Methods:
        brightness() -> float: get brightness.
        brightness(value: float) -> None: set brightness and reinit cache.
        rgb565_to_rgb888(val: int, brightness: float, order: str) -> tuple: convert RGB565 to RGB888.
        show(x1: int, y1: int, x2: int, y2: int) -> None: refresh LED matrix.
        scroll(xstep: int, ystep: int, clear_color: int, wrap: bool) -> None: scroll contents.
        show_rgb565_image(image_data: str|dict, offset_x: int, offset_y: int) -> None: render JSON image.
        load_rgb565_image(filename: str, offset_x: int, offset_y: int) -> None: load JSON image from file.

    Notes:
        - Methods involving neopixel.NeoPixel.write() perform hardware I/O and are not ISR-safe.
        - JSON image must follow the RGB565 specification.
    """

    # 常用颜色（RGB565）
    COLOR_BLACK   = const(0x0000)
    COLOR_WHITE   = const(0xFFFF)
    COLOR_RED     = const(0xF800)
    COLOR_GREEN   = const(0x07E0)
    COLOR_BLUE    = const(0x001F)
    COLOR_YELLOW  = const(0xFFE0)
    COLOR_CYAN    = const(0x07FF)
    COLOR_MAGENTA = const(0xF81F)

    # RGB顺序常量（WS2812不同模块可能顺序不同）
    ORDER_RGB = 'RGB'
    ORDER_GRB = 'GRB'
    ORDER_BGR = 'BGR'
    ORDER_BRG = 'BRG'
    ORDER_RBG = 'RBG'
    ORDER_GBR = 'GBR'

    # 布局类型常量
    LAYOUT_ROW = 'row'
    LAYOUT_SNAKE = 'snake'

    # 缓存颜色转换结果，加速重复色值的处理
    COLOR_CACHE = {}

    # 图片JSON格式规范:
    # {
    #     "pixels": [    # 必需 - RGB565像素数组，每个值范围0-65535
    #         0xF800,    # 红色 (R=31, G=0, B=0)
    #         0x07E0,    # 绿色 (R=0, G=63, B=0)
    #         0x001F     # 蓝色 (R=0, G=0, B=31)
    #     ],
    #     "width": 128,   # 可选 - 图片宽度(像素)，默认使用显示器宽度
    #                     # 注: len(pixels)必须能被width整除
    #     # 以下为可选元数据(不影响渲染):
    #     "height": 64,   # 自动计算: len(pixels)/width
    #     "description": "示例图片",
    #     "version": 1.0
    # }

    def __init__(self, width, height, pin, layout=LAYOUT_ROW, brightness=0.2, order=ORDER_BRG,
                 flip_h=False, flip_v=False, rotate=0):
        """
        初始化 WS2812 矩阵对象，创建 NeoPixel 实例及 FrameBuffer 缓冲区，并设置布局、亮度和旋转。

        Args:
            width (int): 矩阵宽度，像素数量，必须大于 0。
            height (int): 矩阵高度，像素数量，必须大于 0。
            pin (Pin): 控制 WS2812 的 GPIO 引脚。
            layout (str): 布局类型，可选 "row" 或 "snake"，默认为 "row"。
            brightness (float): 亮度值，范围 0.0–1.0，默认为 0.2。
            order (str): RGB 顺序，默认为 "BRG"，可选值：RGB, GRB, BGR, BRG, RBG, GBR。
            flip_h (bool): 是否水平翻转，默认 False。
            flip_v (bool): 是否垂直翻转，默认 False。
            rotate (int): 顺时针旋转角度，可选 0, 90, 180, 270，默认 0。

        Raises:
            ValueError: 参数非法，如宽高小于 1，布局或颜色顺序不合法，亮度超范围，旋转角度非法。

        Notes:
            - 会创建 NeoPixel 对象及 framebuf 缓冲区。
            - 初始化会填充颜色缓存，加速 RGB565 转 RGB888。
            - 非 ISR-safe，不可在中断中调用。

        ==========================================

        Initialize WS2812 matrix object, creating NeoPixel instance and FrameBuffer buffer,
        and setting layout, brightness, flipping and rotation.

        Args:
            width (int): Matrix width in pixels, must be >0.
            height (int): Matrix height in pixels, must be >0.
            pin (Pin): GPIO pin controlling WS2812.
            layout (str): Layout type, "row" or "snake", default "row".
            brightness (float): Brightness value, 0.0–1.0, default 0.2.
            order (str): RGB order, default "BRG", options: RGB, GRB, BGR, BRG, RBG, GBR.
            flip_h (bool): Horizontal flip, default False.
            flip_v (bool): Vertical flip, default False.
            rotate (int): Rotation in degrees, 0,90,180,270, default 0.

        Raises:
            ValueError: Invalid parameters, e.g., width/height <1, invalid layout or order, brightness out of range, illegal rotation.

        Notes:
            - Creates NeoPixel object and framebuf buffer.
            - Initializes color cache for fast RGB565 to RGB888 conversion.
            - Not ISR-safe.
        """
        # 检查参数是否合法
        if width < 1 or height < 1:
            raise ValueError('width and height must be greater than 0')

        # 检查布局类型是否合法
        if layout not in [NeopixelMatrix.LAYOUT_ROW, NeopixelMatrix.LAYOUT_SNAKE]:
            raise ValueError('layout must be one of "NeopixelMatrix.LAYOUT_ROW" or "NeopixelMatrix.LAYOUT_SNAKE"')

        # 检查颜色转换顺序是否合法
        if order not in [NeopixelMatrix.ORDER_RGB, NeopixelMatrix.ORDER_GRB, NeopixelMatrix.ORDER_BGR,
                         NeopixelMatrix.ORDER_BRG, NeopixelMatrix.ORDER_RBG, NeopixelMatrix.ORDER_GBR]:
            raise ValueError('order must be one of "NeopixelMatrix.ORDER_RGB", "NeopixelMatrix.ORDER_GRB", "NeopixelMatrix.ORDER_BGR", '
                             '"NeopixelMatrix.ORDER_BRG", "NeopixelMatrix.ORDER_RBG" or "NeopixelMatrix.ORDER_GBR"')

        # 检查翻转参数是否合法
        if not isinstance(flip_h, bool) or not isinstance(flip_v, bool):
            raise ValueError('flip_h and flip_v must be bool')

        # 检查旋转角度是否合法：只能为0、90、180、270
        if not (rotate == 0 or rotate == 90 or rotate == 180 or rotate == 270):
            raise ValueError('rotate must be 90, 180 or 270')

        # 创建 NeoPixel 对象，共 width*height 个像素
        self.np = neopixel.NeoPixel(pin, width * height)
        # 保存矩阵宽度、高度
        self.width = width
        self.height = height

        # 保存布局类型（行/蛇形）：
        #   行优先排列：每一行从左到右依次编号，每一行的方向都相同。
        #   蛇形排列：偶数行（第 0、2、4 行等）从左到右，奇数行（第 1、3、5 行等）从右到左。
        self.layout = layout
        # 创建用于 framebuf 的 RGB565 缓冲区（2 字节一个像素）
        self.buffer = memoryview(bytearray(width * height * 2))

        # 保存颜色转换顺序
        self.order = order
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.rotate = rotate % 360

        # 初始化 framebuf.FrameBuffer，使用 RGB565 模式
        super().__init__(self.buffer, width, height, framebuf.RGB565)

        # 初始化亮度并缓存常用颜色
        self._brightness = brightness
        self._init_color_cache()

    def _init_color_cache(self):
        """
        初始化颜色转换缓存，预计算常用颜色的 RGB565 到 RGB888 转换结果。

        Notes:
            - 缓存会被清空并重新填充常用颜色的转换结果
            - 当亮度改变时会自动调用此方法更新缓存

        ==========================================

        Initialize color conversion cache, precompute RGB565 to RGB888 conversion results for common colors.

        Notes:
            - Cache will be cleared and repopulated with conversion results for common colors
            - Automatically called when brightness changes to update cache
        """
        NeopixelMatrix.COLOR_CACHE.clear()
        common_colors = [
            NeopixelMatrix.COLOR_BLACK,
            NeopixelMatrix.COLOR_WHITE,
            NeopixelMatrix.COLOR_RED,
            NeopixelMatrix.COLOR_GREEN,
            NeopixelMatrix.COLOR_BLUE,
            NeopixelMatrix.COLOR_YELLOW,
            NeopixelMatrix.COLOR_CYAN,
            NeopixelMatrix.COLOR_MAGENTA
        ]
        for color in common_colors:
            # 计算并缓存
            self.rgb565_to_rgb888(color)

    @property
    def brightness(self) -> float:
        """
        获取当前亮度值。

        Returns:
            float: 当前亮度，范围 0.0–1.0。

        Notes:
            - 亮度值影响所有像素的显示强度
            - 此为属性的getter方法

        ==========================================

        Get current brightness value.

        Returns:
            float: Current brightness, range 0.0–1.0.

        Notes:
            - Brightness value affects display intensity of all pixels
            - This is the getter method for the property
        """
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        """
        设置亮度值并重新初始化颜色缓存。

        Args:
            value (float): 新的亮度值，范围 0.0–1.0。

        Raises:
            ValueError: 亮度值超出 0.0–1.0 范围。

        Notes:
            - 亮度变化会影响所有后续的颜色转换
            - 设置后会自动重建颜色转换缓存

        ==========================================

        Set brightness value and reinitialize color cache.

        Args:
            value (float): New brightness value, range 0.0–1.0.

        Raises:
            ValueError: brightness value is out of 0.0–1.0 range.

        Notes:
            - Brightness change affects all subsequent color conversions
            - Automatically rebuilds color conversion cache after setting
        """
        if not 0 <= value <= 1:
            raise ValueError("Brightness must be between 0 and 1")
        self._brightness = value
        # 清空并重新初始化缓存
        self._init_color_cache()

    @micropython.native
    def _pos2index(self, x, y) -> int:
        """
        将 (x, y) 坐标转换为 NeoPixel 像素数组中的索引，考虑旋转、翻转和布局设置。

        Args:
            x (int): 像素的 X 坐标（水平方向）。
            y (int): 像素的 Y 坐标（垂直方向）。

        Returns:
            int: 对应像素在 NeoPixel 数组中的索引。

        Notes:
            - 内部辅助方法，处理坐标到物理像素的映射
            - 考虑旋转、翻转和布局设置的综合影响
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Convert (x, y) coordinates to index in NeoPixel pixel array, considering rotation, flipping and layout settings.

        Args:
            x (int): X coordinate of the pixel (horizontal).
            y (int): Y coordinate of the pixel (vertical).

        Returns:
            int: Index of the corresponding pixel in NeoPixel array.

        Notes:
            - Internal helper method handling coordinate to physical pixel mapping
            - Considers combined effects of rotation, flipping and layout settings
            - Optimized with micropython.native decorator
        """
        # 1. 旋转处理
        if self.rotate == 90:
            x, y = y, self.width - 1 - x
        elif self.rotate == 180:
            x, y = self.width - 1 - x, self.height - 1 - y
        elif self.rotate == 270:
            x, y = self.height - 1 - y, x

        # 2. 翻转处理
        if self.flip_h:
            x = self.width - 1 - x
        if self.flip_v:
            y = self.height - 1 - y

        # 行优先：直接线性排列
        if self.layout == NeopixelMatrix.LAYOUT_ROW:
            return y * self.width + x
        # 蛇形排列：奇数行方向反转
        elif self.layout == NeopixelMatrix.LAYOUT_SNAKE:
            return y * self.width + (x if y % 2 == 0 else self.width - 1 - x)

    @micropython.native
    def rgb565_to_rgb888(self, val, brightness=None, order=None) -> tuple:
        """
        将 RGB565 颜色格式转换为 RGB888 格式，并应用亮度和颜色通道顺序。

        Args:
            val (int): RGB565 颜色值（0x0000–0xFFFF）。
            brightness (float, optional): 亮度系数，范围 0.0–1.0，默认使用当前亮度。
            order (str, optional): 颜色通道顺序，默认使用实例设置的顺序。

        Returns:
            tuple: (r, g, b) 形式的 RGB888 颜色值（0–255）。

        Raises:
            ValueError: 当亮度值超出范围或颜色顺序不合法时。

        Notes:
            - 使用缓存机制避免重复计算，提高性能
            - 使用 micropython.native 装饰器优化转换速度
            - 转换公式参考：https://en.wikipedia.org/wiki/High_color#16-bit

        ==========================================

        Convert RGB565 color format to RGB888 format, applying brightness and color channel order.

        Args:
            val (int): RGB565 color value (0x0000–0xFFFF).
            brightness (float, optional): Brightness factor, range 0.0–1.0, uses current brightness by default.
            order (str, optional): Color channel order, uses instance setting by default.

        Returns:
            tuple: RGB888 color values in (r, g, b) form (0–255).

        Raises:
            ValueError: When brightness value is out of range or color order is invalid.

        Notes:
            - Uses caching mechanism to avoid redundant calculations and improve performance
            - Optimized with micropython.native decorator
            - Conversion formula reference: https://en.wikipedia.org/wiki/High_color#16-bit
        """
        if brightness is None:
            brightness = self._brightness

        if order is None:
            order = self.order

        if not 0 <= brightness <= 1:
            raise ValueError("Brightness must be between 0 and 1")

        # 检查缓存
        cache_key = (val, brightness, order)
        if cache_key in NeopixelMatrix.COLOR_CACHE:
            return NeopixelMatrix.COLOR_CACHE[cache_key]

        # 提取 RGB565 颜色分量
        r = (val >> 11) & 0x1F
        g = (val >> 5) & 0x3F
        b = val & 0x1F

        # 转换为 8bit 并应用亮度
        r8 = int(((r * 527 + 23) >> 6) * brightness)
        g8 = int(((g * 259 + 33) >> 6) * brightness)
        b8 = int(((b * 527 + 23) >> 6) * brightness)

        # 根据顺序组合
        if order == NeopixelMatrix.ORDER_RGB:
            rgb = (r8, g8, b8)
        elif order == NeopixelMatrix.ORDER_GRB:
            rgb = (g8, r8, b8)
        elif order == NeopixelMatrix.ORDER_BGR:
            rgb = (b8, g8, r8)
        elif order == NeopixelMatrix.ORDER_BRG:
            rgb = (b8, r8, g8)
        elif order == NeopixelMatrix.ORDER_RBG:
            rgb = (r8, b8, g8)
        elif order == NeopixelMatrix.ORDER_GBR:
            rgb = (g8, b8, r8)
        else:
            raise ValueError('Invalid order: {}'.format(order))

        # 写入缓存
        NeopixelMatrix.COLOR_CACHE[cache_key] = rgb

        return rgb

    @micropython.native
    def show(self, x1=0, y1=0, x2=None, y2=None):
        """
        将帧缓存中的内容刷新到物理 LED 矩阵，支持局部区域刷新以提高效率。

        Args:
            x1 (int, optional): 刷新区域左上角 X 坐标，默认 0。
            y1 (int, optional): 刷新区域左上角 Y 坐标，默认 0。
            x2 (int, optional): 刷新区域右下角 X 坐标，默认宽度-1。
            y2 (int, optional): 刷新区域右下角 Y 坐标，默认高度-1。

        Raises:
            ValueError: 当坐标超出矩阵范围或区域不合法（x2 < x1 或 y2 < y1）时。

        Notes:
            - 调用 neopixel.NeoPixel.write() 执行实际硬件刷新，非 ISR-safe
            - 局部刷新可减少数据传输量，提高性能
            - 使用 micropython.native 装饰器优化循环性能

        ==========================================

        Refresh content from frame buffer to physical LED matrix, supporting partial area refresh for efficiency.

        Args:
            x1 (int, optional): Top-left X coordinate of refresh area, default 0.
            y1 (int, optional): Top-left Y coordinate of refresh area, default 0.
            x2 (int, optional): Bottom-right X coordinate of refresh area, default width-1.
            y2 (int, optional): Bottom-right Y coordinate of refresh area, default height-1.

        Raises:
            ValueError: When coordinates are out of matrix range or area is invalid (x2 < x1 or y2 < y1).

        Notes:
            - Calls neopixel.NeoPixel.write() to perform actual hardware refresh, not ISR-safe
            - Partial refresh reduces data transfer and improves performance
            - Optimized with micropython.native decorator
        """
        # 如果没指定 x2，默认整行
        x2 = x2 if x2 is not None else self.width - 1
        # 如果没指定 y2，默认整列
        y2 = y2 if y2 is not None else self.height - 1

        # 检查区域参数是否合法
        # 检查起始坐标是否合法
        if not (0 <= x1 < self.width and 0 <= y1 < self.height):
            raise ValueError(f'Start coordinate ({x1},{y1}) out of range ')
        # 检查结束坐标是否合法
        if not (0 <= x2 < self.width and 0 <= y2 < self.height):
            raise ValueError(f'End coordinate ({x2},{y2}) out of range ')
        # 检查区域是否合法
        if x2 < x1 or y2 < y1:
            raise ValueError('Invalid area: ({x1},{y1})-({x2},{y2})'.format(x1=x1, y1=y1, x2=x2, y2=y2))

        # 遍历每一行
        for y in range(y1, y2 + 1):
            # 遍历每一列
            for x in range(x1, x2 + 1):
                # 计算 WS2812 的实际索引
                idx = self._pos2index(x, y)
                # 每个像素占 2 字节，计算在 buffer 中的偏移地址
                addr = (y * self.width + x) * 2
                # 从 FrameBuffer 中读取 RGB565 值（高字节在前）
                val = (self.buffer[addr] << 8) | self.buffer[addr + 1]
                # 转换为 RGB888 后赋值给 WS2812
                self.np[idx] = self.rgb565_to_rgb888(val, self.brightness, self.order)

        # 写入所有像素数据到 WS2812 灯带，点亮屏幕
        self.np.write()

    @micropython.native
    def scroll(self, xstep, ystep, clear_color=None, wrap=False):
        """
        沿水平和垂直方向滚动显示内容，支持循环滚动和普通滚动两种模式。

        Args:
            xstep (int): 水平滚动像素数，正数向右，负数向左。
            ystep (int): 垂直滚动像素数，正数向下，负数向上。
            clear_color (int, optional): 滚动后露出区域的填充颜色（RGB565），默认黑色。
            wrap (bool, optional): 是否循环滚动，True 表示循环，False 表示普通滚动，默认 False。

        Raises:
            ValueError: 当 xstep/ystep 不是整数、clear_color 不是整数或 wrap 不是布尔值时。

        Notes:
            - 滚动仅修改帧缓存，需调用 show() 方法刷新到物理矩阵
            - 循环滚动模式下内容会从另一侧出现，普通模式下露出区域会被填充
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Scroll display content horizontally and vertically, supporting both circular and normal scrolling modes.

        Args:
            xstep (int): Number of pixels to scroll horizontally, positive for right, negative for left.
            ystep (int): Number of pixels to scroll vertically, positive for down, negative for up.
            clear_color (int, optional): Fill color for exposed areas after scrolling (RGB565), default black.
            wrap (bool, optional): Whether to wrap around, True for circular scrolling, False for normal scrolling, default False.

        Raises:
            ValueError: When xstep/ystep are not integers, clear_color is not integer, or wrap is not boolean.

        Notes:
            - Scrolling only modifies frame buffer, need to call show() to refresh physical matrix
            - In wrap mode content reappears on opposite side, in normal mode exposed areas are filled
            - Optimized with micropython.native decorator
        """
        # 如果没有指定清除颜色，使用默认黑色
        if clear_color is None:
            clear_color = NeopixelMatrix.COLOR_BLACK

        # 检查滚动参数是否合法
        if not isinstance(xstep, int) or not isinstance(ystep, int):
            raise ValueError('xstep and ystep must be int')

        # 检查颜色参数是否合法
        if not isinstance(clear_color, int):
            raise ValueError('clear_color must be int')

        # 检查循环滚动设置参数是否合法
        if not isinstance(wrap, bool):
            raise ValueError('wrap must be bool')

        if wrap:
            # 循环滚动模式 - 保存原始缓冲区
            temp_buffer = bytearray(self.buffer)

            # 处理水平滚动
            if xstep != 0:
                abs_xstep = abs(xstep) % self.width
                if xstep > 0:
                    # 向右滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_x = (x - abs_xstep) % self.width
                            src_addr = (y * self.width + src_x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
                else:
                    # 向左滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_x = (x + abs_xstep) % self.width
                            src_addr = (y * self.width + src_x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]

            # 处理垂直滚动
            if ystep != 0:
                abs_ystep = abs(ystep) % self.height
                if ystep > 0:
                    # 向下滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_y = (y - abs_ystep) % self.height
                            src_addr = (src_y * self.width + x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
                else:
                    # 向上滚动
                    for y in range(self.height):
                        for x in range(self.width):
                            src_y = (y + abs_ystep) % self.height
                            src_addr = (src_y * self.width + x) * 2
                            dst_addr = (y * self.width + x) * 2
                            self.buffer[dst_addr] = temp_buffer[src_addr]
                            self.buffer[dst_addr + 1] = temp_buffer[src_addr + 1]
        else:
            # 普通滚动模式
            super().scroll(xstep, ystep)

            # 清除水平滚动残留
            if xstep > 0:
                # 向右滚动，清除左侧残留
                self.vline(0, 0, self.height, clear_color)
            elif xstep < 0:
                # 向左滚动，清除右侧残留
                self.vline(self.width - 1, 0, self.height, clear_color)

            # 清除垂直滚动残留
            if ystep > 0:
                # 向下滚动，清除顶部残留
                self.hline(0, 0, self.width, clear_color)
            elif ystep < 0:
                # 向上滚动，清除底部残留
                self.hline(0, self.height - 1, self.width, clear_color)

    @micropython.native
    def show_rgb565_image(self, image_data, offset_x=0, offset_y=0):
        """
        显示 JSON 格式的 RGB565 图像数据，可以是 JSON 字符串或已解析的字典。

        Args:
            image_data (str | dict): JSON 图像数据，可以是字符串或已解析的字典。
            offset_x (int, optional): 图像显示的 X 偏移量，默认 0。
            offset_y (int, optional): 图像显示的 Y 偏移量，默认 0。

        Raises:
            ValueError: 当图像数据格式不合法时。
            json.JSONDecodeError: 当 JSON 字符串解析失败时。

        Notes:
            - 图像数据需符合类中定义的 JSON 格式规范
            - 仅修改帧缓存，需调用 show() 方法刷新显示
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Display JSON formatted RGB565 image data, which can be a JSON string or parsed dictionary.

        Args:
            image_data (str | dict): JSON image data, can be string or parsed dictionary.
            offset_x (int, optional): X offset for image display, default 0.
            offset_y (int, optional): Y offset for image display, default 0.

        Raises:
            ValueError: When image data format is invalid.
            json.JSONDecodeError: When JSON string parsing fails.

        Notes:
            - Image data must conform to JSON format specification defined in the class
            - Only modifies frame buffer, need to call show() to refresh display
            - Optimized with micropython.native decorator
        """
        try:
            # 解析JSON数据
            if isinstance(image_data, str):
                image_data = json.loads(image_data)

            # 验证数据格式
            self._validate_rgb565_image(image_data)

            # 渲染图片
            self._draw_rgb565_data(
                image_data['pixels'],
                image_data.get('width', self.width),
                offset_x,
                offset_y
            )
        except Exception as e:
            print("Error: {}".format(e))

    @micropython.native
    def _validate_rgb565_image(self, data):
        """
        验证 RGB565 图像数据的格式是否符合规范。

        Args:
            data (dict): 已解析的图像数据字典。

        Raises:
            ValueError: 当数据缺少必要键、像素不是列表或颜色值超出范围时,宽度不是正整数时。

        Notes:
            - 内部辅助方法，确保图像数据格式正确
            - 检查必要的键、数据类型和值范围
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Validate that RGB565 image data format conforms to specifications.

        Args:
            data (dict): Parsed image data dictionary.

        Raises:
            ValueError: When data lacks required keys, pixels are not a list, or color values are out of range,
            width must be positive integer.

        Notes:
            - Internal helper method ensuring correct image data format
            - Checks for required keys, data types and value ranges
            - Optimized with micropython.native decorator
        """
        required = ['pixels']
        if not all(key in data for key in required):
            raise ValueError('lack required keys: {}'.format(required))

        if not isinstance(data['pixels'], list):
            raise ValueError('pixels must be list')

        if 'width' in data and data['width'] <= 0:
            raise ValueError('width must be positive integer')

        for color in data['pixels']:
            if not 0 <= color <= 0xFFFF:
                raise ValueError('color must be 0-65535')

    @micropython.native
    def _draw_rgb565_data(self, pixels, img_width, offset_x, offset_y):
        """
        将 RGB565 像素数据绘制到帧缓存的指定位置。

        Args:
            pixels (list): RGB565 颜色值列表。
            img_width (int): 图像宽度（像素），用于计算像素坐标。
            offset_x (int): 绘制的 X 偏移量。
            offset_y (int): 绘制的 Y 偏移量。

        Notes:
            - 内部辅助方法，负责实际绘制像素
            - 仅绘制矩阵范围内的像素，超出部分会被忽略
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Draw RGB565 pixel data to specified position in frame buffer.

        Args:
            pixels (list): List of RGB565 color values.
            img_width (int): Image width in pixels, used to calculate pixel coordinates.
            offset_x (int): X offset for drawing.
            offset_y (int): Y offset for drawing.

        Notes:
            - Internal helper method responsible for actual pixel drawing
            - Only draws pixels within matrix range, out-of-bounds pixels are ignored
            - Optimized with micropython.native decorator
        """
        for i, color in enumerate(pixels):
            x = i % img_width + offset_x
            y = i // img_width + offset_y

            if 0 <= x < self.width and 0 <= y < self.height:
                self.pixel(x, y, color)

    @micropython.native
    def load_rgb565_image(self, filename, offset_x=0, offset_y=0):
        """
        从文件加载 JSON 格式的 RGB565 图像并显示在指定位置。

        Args:
            filename (str): 包含 JSON 图像数据的文件名。
            offset_x (int, optional): 图像显示的 X 偏移量，默认 0。
            offset_y (int, optional): 图像显示的 Y 偏移量，默认 0。

        Notes:
            - 调用 show_rgb565_image() 处理实际的图像解析和绘制
            - 仅修改帧缓存，需调用 show() 方法刷新显示
            - 使用 micropython.native 装饰器优化性能

        ==========================================

        Load JSON formatted RGB565 image from file and display at specified position.

        Args:
            filename (str): Filename containing JSON image data.
            offset_x (int, optional): X offset for image display, default 0.
            offset_y (int, optional): Y offset for image display, default 0.

        Notes:
            - Calls show_rgb565_image() to handle actual image parsing and drawing
            - Only modifies frame buffer, need to call show() to refresh display
            - Optimized with micropython.native decorator
        """
        try:
            with open(filename, 'r') as f:
                self.show_rgb565_image(f.read(), offset_x, offset_y)
        except OSError as e:
            print("Error: {}".format(e))

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
