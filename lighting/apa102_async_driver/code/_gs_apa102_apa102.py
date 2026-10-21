# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Damien P. George, Adafruit Industries, Matt Trentini, FreakStudio
# @File    : apa102.py
# @Description : APA102/DotStar 可寻址 RGB LED 灯带 SPI 驱动类

# The MIT License (MIT)
# Copyright (c) 2016 Damien P. George (original Neopixel object)
# Copyright (c) 2017 Ladyada, Scott Shawcroft for Adafruit Industries
# Copyright (c) 2019 Matt Trentini (porting back to MicroPython)

__version__ = "1.0.0"
__author__ = "Damien P. George, Adafruit Industries, Matt Trentini, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入 micropython 常量优化模块
from micropython import const as mp_const

# ======================================== 全局变量 ============================================

# 兼容 CPython 的 const 定义
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# APA102/DotStar LED 灯带驱动类
class DotStar:
    """
    APA102/DotStar 可寻址 RGB LED 灯带 SPI 驱动类。

    该类封装了 APA102/DotStar LED 灯带的完整控制功能，包括颜色设置、亮度调节、
    像素缓冲区管理以及自动/手动刷新机制。通过 SPI 接口与灯带通信，适用于单像素
    到多像素级联场景。

    Attributes:
        _spi (machine.SPI | None): SPI 接口实例，用于与灯带通信。
        _n (int): 灯带中 LED 像素数量。
        _buf (bytearray): 内部像素数据缓冲区（含起始帧和结束帧）。
        end_header_size (int): 结束帧字节数（根据像素数计算）。
        end_header_index (int): 结束帧在缓冲区中的起始索引。
        pixel_order (tuple): 像素颜色通道顺序（如 RGB、BGR 等）。
        _brightness (float): 整体亮度值（0.0-1.0）。
        auto_write (bool): 是否在每次设置像素时自动调用 show()。

    Constants (类常量，均为 tuple):
        RGB, RBG, GRB, GBR, BRG, BGR: 像素颜色通道顺序常量。
        START_HEADER_SIZE: 起始帧字节数（固定 4 字节）。
        LED_START: LED 起始帧标志位（0xE0）。

    Methods:
        __init__(self, spi, n, *, brightness, auto_write, pixel_order):
            初始化 DotStar 灯带实例。

        __setitem__(self, index, val):
            设置指定索引的像素颜色，支持单像素和切片设置。

        __getitem__(self, index):
            获取指定索引的像素颜色，返回 (R, G, B) 元组。

        __len__(self):
            返回灯带中 LED 像素数量。

        fill(self, color):
            将所有像素设置为指定颜色。

        show(self):
            将像素缓冲区数据通过 SPI 写入灯带，实现显示刷新。

        deinit(self):
            清空灯带并释放 SPI 资源。

    Properties:
        brightness (float): 整体亮度值（0.0-1.0），可读写。

    Usage Notes & Implementation Considerations:
        - APA102 协议: 每个像素由 4 字节组成（1 字节起始帧 + 3 字节颜色数据），
          灯带前后各有 4 字节起始帧和若干字节结束帧。
        - SPI 通信: 使用 machine.SPI 接口，只需 SCK 和 MOSI 引脚，MISO 不使用。
        - 缓冲区管理: 内部维护完整的帧缓冲区（起始帧 + 像素数据 + 结束帧），
          自动计算结束帧长度（每 16 个像素额外增加 1 字节结束帧）。
        - 亮度调节: 通过 5 位全局亮度 + 硬件的 PWM 实现，可设置每个像素的独立亮度。
        - 自动刷新: auto_write=True 时，每次设置像素后自动调用 show()；
          设 False 时需手动调用 show() 生效，适合批量更新场景。
        - 颜色顺序: 不同制造商的 APA102 灯带可能使用不同的颜色通道顺序，
          通过 pixel_order 参数适配。
    """

    # ======================================== 常量定义 ========================================

    # 像素颜色顺序常量
    RGB = const((0, 1, 2))
    RBG = const((0, 2, 1))
    GRB = const((1, 0, 2))
    GBR = const((1, 2, 0))
    BRG = const((2, 0, 1))
    BGR = const((2, 1, 0))

    # 起始帧大小（4 字节全零）
    START_HEADER_SIZE = const(4)
    # LED 起始帧标志（高 3 位为 1，低 5 位为亮度）
    LED_START = const(0xE0)
    # 亮度位掩码（5 位亮度，0-31）
    BRIGHTNESS_MASK = const(0x1F)
    # 单像素数据字节数
    PIXEL_SIZE = const(4)

    def __init__(self, spi, n, *, brightness=1.0, auto_write=True, pixel_order=BGR):
        """
        初始化 DotStar/APA102 灯带驱动实例。

        Args:
            spi (machine.SPI): SPI 接口实例，用于与灯带通信（仅需 SCK 和 MOSI）。
            n (int): 灯带中 LED 像素数量，必须 >= 1。
            brightness (float, optional): 整体亮度值（0.0-1.0），默认 1.0。
            auto_write (bool, optional): 是否自动刷新显示，默认 True。
            pixel_order (tuple, optional): 像素颜色通道顺序，默认为 BGR。

        Raises:
            ValueError: 如果 n <= 0、brightness 超出范围或 pixel_order 无效。
            TypeError: 如果 spi 不是有效的 SPI 实例。

        ==========================================
        Initialize a DotStar/APA102 LED strip driver instance.

        Args:
            spi (machine.SPI): SPI instance for communication (only SCK and MOSI needed).
            n (int): Number of LED pixels in the strip, must be >= 1.
            brightness (float, optional): Global brightness (0.0-1.0), default 1.0.
            auto_write (bool, optional): Auto-refresh display, default True.
            pixel_order (tuple, optional): Pixel color channel order, default BGR.

        Raises:
            ValueError: If n <= 0, brightness out of range, or pixel_order invalid.
            TypeError: If spi is not a valid SPI instance.
        """
        # 检查 SPI 参数有效性
        if not (hasattr(spi, "write") and hasattr(spi, "deinit")):
            raise TypeError("spi must be a valid SPI instance")
        # 检查像素数量
        if not isinstance(n, int) or n < 1:
            raise ValueError("n must be a positive integer >= 1")
        # 检查亮度范围
        if not isinstance(brightness, (int, float)) or brightness < 0.0 or brightness > 1.0:
            raise ValueError("brightness must be between 0.0 and 1.0")
        # 检查颜色顺序
        if pixel_order not in (DotStar.RGB, DotStar.RBG, DotStar.GRB, DotStar.GBR, DotStar.BRG, DotStar.BGR):
            raise ValueError("pixel_order must be one of DotStar.RGB/RBG/GRB/GBR/BRG/BGR")
        # 检查 auto_write
        if not isinstance(auto_write, bool):
            raise ValueError("auto_write must be bool")

        # 保存 SPI 接口实例
        self._spi = spi
        # 保存像素数量
        self._n = n

        # 计算结束帧大小（每 16 个像素额外增加 1 字节）
        self.end_header_size = n // 16
        if n % 16 != 0:
            self.end_header_size += 1

        # 分配帧缓冲区：[4字节起始帧] + [n*4字节像素数据] + [end_header_size字节结束帧]
        self._buf = bytearray(n * DotStar.PIXEL_SIZE + DotStar.START_HEADER_SIZE + self.end_header_size)
        self.end_header_index = len(self._buf) - self.end_header_size

        # 保存像素颜色顺序
        self.pixel_order = pixel_order

        # 填充起始帧（全零）
        for i in range(DotStar.START_HEADER_SIZE):
            self._buf[i] = 0x00

        # 填充每个像素的起始字节（0xFF）
        for i in range(DotStar.START_HEADER_SIZE, self.end_header_index, DotStar.PIXEL_SIZE):
            self._buf[i] = 0xFF

        # 填充结束帧（全 0xFF）
        for i in range(self.end_header_index, len(self._buf)):
            self._buf[i] = 0xFF

        # 保存亮度值（先设为 1.0 避免 setter 在初始化时调用 show()）
        self._brightness = 1.0
        # 初始化时暂时关闭自动刷新
        self.auto_write = False
        # 设置亮度（通过 setter，不会触发 show()）
        self.brightness = brightness
        # 恢复自动刷新设置
        self.auto_write = auto_write

    # ======================================== 魔术方法 ========================================

    def __enter__(self):
        """
        上下文管理器入口，支持 with 语句。

        Returns:
            DotStar: 当前 DotStar 实例。

        ==========================================
        Context manager entry, supports with statement.

        Returns:
            DotStar: The current DotStar instance.
        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """
        上下文管理器退出，自动调用 deinit() 释放资源。

        ==========================================
        Context manager exit, automatically calls deinit() to release resources.
        """
        self.deinit()

    def __repr__(self):
        """
        返回灯带当前颜色状态的字符串表示。

        Returns:
            str: 格式为 "[(R,G,B), (R,G,B), ...]" 的颜色列表。

        ==========================================
        Return string representation of current color state.

        Returns:
            str: Color list in format "[(R,G,B), (R,G,B), ...]".
        """
        return "[" + ", ".join([str(x) for x in self]) + "]"

    def __setitem__(self, index, val):
        """
        设置指定位置的像素颜色。

        支持两种设置方式：
        - 单像素设置：index 为整数，val 为 (R,G,B) 元组/列表 或 RGB 整数值（0xRRGGBB）
        - 切片设置：index 为 slice 对象，val 为颜色值序列

        Args:
            index (int | slice): 像素索引（0-based）或切片对象。
            val (tuple | int): 颜色值，(R,G,B) 元组或 0xRRGGBB 格式整数值。

        Raises:
            ValueError: 当切片设置时，颜色序列长度与切片范围不匹配。
            IndexError: 当 index 超出范围（整数索引时）。

        ==========================================
        Set the color of the pixel(s) at the specified index.

        Args:
            index (int | slice): Pixel index (0-based) or slice object.
            val (tuple | int): Color value, (R,G,B) tuple or 0xRRGGBB integer.

        Raises:
            ValueError: When slice assignment length does not match slice range.
            IndexError: When index is out of range (integer index).
        """
        # 处理切片索引
        if isinstance(index, slice):
            start, stop, step = index.indices(self._n)
            length = stop - start
            if step != 0:
                length = (length + step - 1) // step
            if len(val) != length:
                raise ValueError("Slice and input sequence size do not match")
            for val_i, in_i in enumerate(range(start, stop, step)):
                self._set_item(in_i, val[val_i])
        else:
            # 单个像素设置
            self._set_item(index, val)

        # 自动刷新
        if self.auto_write:
            self.show()

    def __getitem__(self, index):
        """
        获取指定位置的像素颜色。

        Args:
            index (int | slice): 像素索引或切片对象。

        Returns:
            tuple | list: 单像素返回 (R,G,B) 元组，切片返回颜色元组列表。

        Raises:
            IndexError: 当 index 超出范围（整数索引时）。

        ==========================================
        Get the color of the pixel(s) at the specified index.

        Args:
            index (int | slice): Pixel index or slice object.

        Returns:
            tuple | list: Single pixel returns (R,G,B) tuple, slice returns list of tuples.

        Raises:
            IndexError: When index is out of range (integer index).
        """
        # 处理切片索引
        if isinstance(index, slice):
            out = []
            for in_i in range(*index.indices(self._n)):
                out.append(tuple(self._buf[in_i * DotStar.PIXEL_SIZE + (3 - i) + DotStar.START_HEADER_SIZE] for i in range(3)))
            return out
        # 处理负索引
        if index < 0:
            index += len(self)
        # 检查索引范围
        if index >= self._n or index < 0:
            raise IndexError
        # 读取单个像素颜色
        offset = index * DotStar.PIXEL_SIZE
        return tuple(self._buf[offset + (3 - i) + DotStar.START_HEADER_SIZE] for i in range(3))

    def __len__(self):
        """
        返回灯带中 LED 像素数量。

        Returns:
            int: LED 像素数量。

        ==========================================
        Return the number of LED pixels in the strip.

        Returns:
            int: Number of LED pixels.
        """
        return self._n

    # ======================================== 公开方法 ========================================

    def fill(self, color):
        """
        将所有像素设置为指定的颜色。

        Args:
            color (tuple | int): 颜色值，(R,G,B) 元组或 0xRRGGBB 整数值。

        ==========================================
        Set all pixels to the specified color.

        Args:
            color (tuple | int): Color value, (R,G,B) tuple or 0xRRGGBB integer.
        """
        # 临时关闭自动刷新以提高效率
        auto_write = self.auto_write
        self.auto_write = False
        # 逐个设置每个像素
        for i in range(self._n):
            self[i] = color
        # 恢复自动刷新
        self.auto_write = auto_write
        # 刷新显示
        if auto_write:
            self.show()

    def show(self):
        """
        将像素缓冲区数据通过 SPI 写入灯带，使颜色设置生效。

        本方法构建完整的 APA102 帧（起始帧 + 像素数据 + 结束帧）并通过 SPI 发送。
        当亮度小于 1.0 时，会在发送前创建亮度调整后的缓冲区副本。

        Notes:
            - 此函数可能不会立即返回，因为 SPI 写入可以异步执行。
            - 当亮度为 1.0 时直接使用内部缓冲区，避免额外分配。

        ==========================================
        Write pixel buffer data to the strip via SPI to apply color changes.

        This method constructs the complete APA102 frame (start frame + pixel data + end frame)
        and sends it via SPI. When brightness < 1.0, a brightness-adjusted copy is created.

        Notes:
            - This function may not return immediately as SPI writes can be asynchronous.
            - Uses internal buffer directly when brightness is 1.0 to avoid extra allocation.
        """
        # 选择输出缓冲区（亮度不足 1.0 时需要调整后发送）
        buf = self._buf
        if self.brightness < 1.0:
            # 创建亮度调整后的缓冲区副本
            buf = bytearray(self._buf)
            # 重新填充起始帧
            for i in range(DotStar.START_HEADER_SIZE):
                buf[i] = 0x00
            # 调整每个像素的颜色亮度
            for i in range(DotStar.START_HEADER_SIZE, self.end_header_index):
                if i % DotStar.PIXEL_SIZE != 0:
                    buf[i] = int(self._buf[i] * self._brightness)
            # 重新填充结束帧
            for i in range(self.end_header_index, len(buf)):
                buf[i] = 0xFF

        # 通过 SPI 写入帧数据
        if self._spi:
            self._spi.write(buf)

    def deinit(self):
        """
        清空所有像素并释放 SPI 硬件资源。

        关闭自动刷新，将所有像素颜色置零并调用 show() 清空显示，
        然后释放 SPI 接口。

        Notes:
            - 调用后需重新创建实例才能继续使用。

        ==========================================
        Clear all pixels and release SPI hardware resources.

        Disables auto_write, sets all pixels to black, calls show() to clear,
        then deinitializes the SPI interface.

        Notes:
            - A new instance must be created to continue use after calling this.
        """
        # 关闭自动刷新
        self.auto_write = False
        # 将所有像素颜色置零
        buf = self._buf
        for i in range(DotStar.START_HEADER_SIZE, self.end_header_index):
            if i % DotStar.PIXEL_SIZE != 0:
                buf[i] = 0
        # 刷新显示（清空灯带）
        self.show()
        # 释放 SPI 资源
        if self._spi:
            self._spi.deinit()

    def _log(self, msg):
        """
        输出调试日志信息。

        预留的调试日志方法，格式为 "[APA102] 消息内容"。

        Args:
            msg (str): 要输出的调试信息。

        ==========================================
        Output debug log message.

        Reserved debug log method, format "[APA102] message".

        Args:
            msg (str): Debug message to output.
        """
        pass

    # ======================================== 属性定义 ========================================

    @property
    def brightness(self):
        """
        获取当前整体亮度值。

        Returns:
            float: 亮度值（0.0-1.0）。

        ==========================================
        Get the current global brightness value.

        Returns:
            float: Brightness value (0.0-1.0).
        """
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        """
        设置整体亮度值。

        Args:
            brightness (float): 亮度值（0.0-1.0），超出范围会被裁剪。

        ==========================================
        Set the global brightness value.

        Args:
            brightness (float): Brightness value (0.0-1.0), clamped if out of range.
        """
        # 裁剪亮度值到 [0.0, 1.0] 范围
        self._brightness = min(max(brightness, 0.0), 1.0)
        # 自动刷新
        if self.auto_write:
            self.show()

    # ======================================== 私有方法 ========================================

    def _set_item(self, index, val):
        """
        设置单个像素的颜色和亮度到内部缓冲区。

        Args:
            index (int): 像素索引（0-based）。
            val (tuple | int | list): 颜色值，支持以下格式：
                - (R, G, B) 元组/列表
                - (R, G, B, brightness) 元组/列表（独立亮度 0.0-1.0）
                - 0xRRGGBB 整数值

        Notes:
            - 每个像素的起始字节包含 3 位起始标志 (0b111) + 5 位亮度控制。
            - 独立像素亮度通过 PWM 实现，可能影响 POV 应用效果。
            - 颜色通道顺序由 pixel_order 属性控制。

        ==========================================
        Set a single pixel's color and brightness to the internal buffer.

        Args:
            index (int): Pixel index (0-based).
            val (tuple | int | list): Color value, supports:
                - (R, G, B) tuple/list
                - (R, G, B, brightness) tuple/list (per-pixel brightness 0.0-1.0)
                - 0xRRGGBB integer

        Notes:
            - Each pixel's start byte contains 3-bit start flag (0b111) + 5-bit brightness control.
            - Per-pixel brightness uses PWM, which may affect POV applications.
            - Color channel order is controlled by the pixel_order property.
        """
        # 计算像素在缓冲区中的偏移位置
        offset = index * DotStar.PIXEL_SIZE + DotStar.START_HEADER_SIZE
        rgb = val

        # 处理 0xRRGGBB 整数值格式
        if isinstance(val, int):
            rgb = (val >> 16, (val >> 8) & 0xFF, val & 0xFF)

        # 提取独立像素亮度（若提供）
        if len(rgb) == 4:
            brightness = val[3]
        else:
            brightness = 1.0

        # 计算 5 位亮度值（0-31）
        # math.ceil(brightness * 31) 的等效非浮点实现
        brightness_byte = 32 - int(32 - brightness * 31) & DotStar.BRIGHTNESS_MASK
        # 设置像素起始字节（3 位起始标志 + 5 位亮度）
        self._buf[offset] = brightness_byte | DotStar.LED_START
        # 按指定颜色顺序写入 RGB 值
        self._buf[offset + 1] = rgb[self.pixel_order[0]]
        self._buf[offset + 2] = rgb[self.pixel_order[1]]
        self._buf[offset + 3] = rgb[self.pixel_order[2]]


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
