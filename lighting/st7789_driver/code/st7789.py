# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/7 上午12:02
# @Author  : 李清水
# @File    : st7789.py
# @Description : LCD屏幕驱动芯片st7789的类实现
# 参考russhughes st7789py_mpy：https://github.com/russhughes/st7789py_mpy/blob/master/lib/st7789py.py

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from micropython import const
import machine
import micropython

# 时间相关的模块
import time

# 数学计算相关的模块
from math import sin, cos

# 打包和解包相关的模块
import struct

# ======================================== 全局变量 ============================================

# ST7789 命令列表

# 软复位命令，用于初始化液晶屏
_ST7789_SWRESET = b"\x01"
# 进入睡眠模式命令
_ST7789_SLPIN = b"\x10"
# 退出睡眠模式命令
_ST7789_SLPOUT = b"\x11"
# 正常模式命令
_ST7789_NORON = b"\x13"
# 关闭屏幕反转命令
_ST7789_INVOFF = b"\x20"
# 打开屏幕反转命令
_ST7789_INVON = b"\x21"
# 关闭屏幕显示命令
_ST7789_DISPOFF = b"\x28"
# 打开屏幕显示命令
_ST7789_DISPON = b"\x29"
# 设置列地址范围命令
_ST7789_CASET = b"\x2a"
# 设置行地址范围命令
_ST7789_RASET = b"\x2b"
# 写入内存命令
_ST7789_RAMWR = b"\x2c"
# 设置垂直扫描方向命令
_ST7789_VSCRDEF = b"\x33"
# 设置颜色模式命令
_ST7789_COLMOD = b"\x3a"
# 设置内存访问控制命令
_ST7789_MADCTL = b"\x36"
# 设置垂直偏移命令
_ST7789_VSCSAD = b"\x37"
# 设置内存控制命令
_ST7789_RAMCTL = b"\xb0"

# MADCTL 位定义
_ST7789_MADCTL_MY = const(0x80)  # 指定像素数据从下往上读取
_ST7789_MADCTL_MX = const(0x40)  # 指定像素数据从右往左读取
_ST7789_MADCTL_MV = const(0x20)  # 指定像素数据从上往下滚动
_ST7789_MADCTL_ML = const(0x10)  # 指定像素数据从左往右滚动
_ST7789_MADCTL_BGR = const(0x08)  # 指定像素数据顺序为 BGR
_ST7789_MADCTL_MH = const(0x04)  # 保留位，未使用
_ST7789_MADCTL_RGB = const(0x00)  # 指定像素数据顺序为 RGB

# 常量定义
RGB = const(0x00)  # 指定像素数据顺序为 RGB
BGR = const(0x08)  # 指定像素数据顺序为 BGR

# 颜色模式定义
_COLOR_MODE_65K = const(0x50)  # 65K 色模式
_COLOR_MODE_262K = const(0x60)  # 262K 色模式
_COLOR_MODE_12BIT = const(0x03)  # 12 位色模式
_COLOR_MODE_16BIT = const(0x05)  # 16 位色模式
_COLOR_MODE_18BIT = const(0x06)  # 18 位色模式
_COLOR_MODE_16M = const(0x07)  # 1600 万色模式

# 颜色定义
BLACK = const(0x0000)  # 黑色
BLUE = const(0x001F)  # 蓝色
RED = const(0xF800)  # 红色
GREEN = const(0x07E0)  # 绿色
CYAN = const(0x07FF)  # 青色
MAGENTA = const(0xF81F)  # 品红色
YELLOW = const(0xFFE0)  # 黄色
WHITE = const(0xFFFF)  # 白色

# 编码像素格式定义
_ENCODE_PIXEL = const(">H")  # 大端字节序，两个字节表示一个像素值
_ENCODE_PIXEL_SWAPPED = const("<H")  # 小端字节序，两个字节表示一个像素值
_ENCODE_POS = const(">HH")  # 大端字节序，两个字节分别表示横纵坐标
_ENCODE_POS_16 = const("<HH")  # 小端字节序，两个字节分别表示横纵坐标

# 用于设置缓冲区大小和位数的常量

# 缓冲区大小至少为 128 字节，适用于 8 位宽字体
# 缓冲区大小至少为 256 字节，适用于 16 位宽字体
_BUFFER_SIZE = const(257)

# 位定义
_BIT7 = const(0x80)  # 第 7 位
_BIT6 = const(0x40)  # 第 6 位
_BIT5 = const(0x20)  # 第 5 位
_BIT4 = const(0x10)  # 第 4 位
_BIT3 = const(0x08)  # 第 3 位
_BIT2 = const(0x04)  # 第 2 位
_BIT1 = const(0x02)  # 第 1 位
_BIT0 = const(0x01)  # 第 0 位

# 存储每个屏幕尺寸对应的旋转信息的字典
_DISPLAY_240x320 = ((0x00, 240, 320, 0, 0, False), (0x60, 320, 240, 0, 0, False), (0xC0, 240, 320, 0, 0, False), (0xA0, 320, 240, 0, 0, False))

_DISPLAY_240x240 = ((0x00, 240, 240, 0, 0, False), (0x60, 240, 240, 0, 0, False), (0xC0, 240, 240, 0, 80, False), (0xA0, 240, 240, 80, 0, False))

_DISPLAY_135x240 = (
    (0x00, 135, 240, 52, 40, False),
    (0x60, 240, 135, 40, 53, False),
    (0xC0, 135, 240, 53, 40, False),
    (0xA0, 240, 135, 40, 52, False),
)

_DISPLAY_128x128 = ((0x00, 128, 128, 2, 1, False), (0x60, 128, 128, 1, 2, False), (0xC0, 128, 128, 2, 1, False), (0xA0, 128, 128, 1, 2, False))

# 到旋转表的索引值
_WIDTH = const(0)
_HEIGHT = const(1)
_XSTART = const(2)
_YSTART = const(3)
_NEEDS_SWAP = const(4)

# 支持的显示器 (物理宽度, 物理高度, 旋转表)
_SUPPORTED_DISPLAYS = ((240, 320, _DISPLAY_240x320), (240, 240, _DISPLAY_240x240), (135, 240, _DISPLAY_135x240), (128, 128, _DISPLAY_128x128))

# 初始化时需要发送的命令元组，格式为命令, 数据, 延迟毫秒
_ST7789_INIT_CMDS = (
    (b"\x11", b"\x00", 120),  # 退出休眠模式
    (b"\x13", b"\x00", 0),  # 打开显示屏
    # 参数 0a 表示行扫描方向从下往上，82 表示列扫描方向从右往左
    (b"\xb6", b"\x0a\x82", 0),  # 设置显示功能控制
    # 参数 55 表示红绿蓝的权重分别为 5、6、5
    (b"\x3a", b"\x55", 10),  # 设置像素格式为 16 位每像素 (RGB565)
    # 参数 0c 表示起始行，0c 表示结束行，00 表示起始列，33 表示结束列
    (b"\xb2", b"\x0c\x0c\x00\x33\x33", 0),  # 设置门控控制
    # 参数 35 表示 VGS 电压
    (b"\xb7", b"\x35", 0),  # 设置栅极控制
    # 参数 28 表示 VCOM 电压
    (b"\xbb", b"\x28", 0),  # 设置 VCOMS 设置
    (b"\xc0", b"\x0c", 0),  # 设置电源控制 1
    (b"\xc2", b"\x01\xff", 0),  # 设置电源控制 2
    (b"\xc3", b"\x10", 0),  # 设置电源控制 3
    (b"\xc4", b"\x20", 0),  # 设置电源控制 4
    (b"\xc6", b"\x0f", 0),  # 设置 VCOM 控制 1
    (b"\xd0", b"\xa4\xa1", 0),  # 设置电源控制 A
    # 设置伽马曲线正极性，用于调整红绿蓝三色的亮度
    (b"\xe0", b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17", 0),
    # 设置伽马曲线负极性，用于调整红绿蓝三色的亮度
    (b"\xe1", b"\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e", 0),
    (b"\x21", b"\x00", 0),  # 启用显示反转
    (b"\x29", b"\x00", 120),  # 打开显示屏，等待 120 毫秒
)

# ======================================== 功能函数 ============================================


def color565(red: int, green: int = 0, blue: int = 0) -> int:
    """
    将红、绿、蓝通道值（0-255）转换为 16 位 BGR565 编码。

    Args:
        red (int): 红色通道数值，取值范围 0 到 255（MicroPython 内置类型：int）。
        green (int, optional): 绿色通道数值，取值范围 0 到 255，默认 0（MicroPython 内置类型：int）。
        blue (int, optional): 蓝色通道数值，取值范围 0 到 255，默认 0（MicroPython 内置类型：int）。

    Returns:
        int: 对应颜色的 BGR565 编码值（16 位整数，MicroPython 内置类型：int）。

    Raises:
        ValueError: 如果任一颜色通道值不在 0 到 255 范围内，则抛出该异常。
    """
    if isinstance(red, (tuple, list)):
        # 如果传入的是元组或列表，取前三个元素作为红、绿、蓝的值
        red, green, blue = red[:3]
    # 将 BGR 值限制在 0-255 范围内
    r = max(0, min(red, 255))
    g = max(0, min(green, 255))
    b = max(0, min(blue, 255))
    # 计算 RGB565 编码，BGR565编码的计算公式如下：
    # R = (Red & 0b11111000) >> 3
    # G = (Green & 0b11111100) >> 2
    # B = (Blue & 0b11111000) >> 3
    # 将新的BGR值组合成16位565编码
    return (b & 0x1F) << 11 | (g & 0x3F) << 5 | (r & 0x1F)


# ======================================== 自定义类 ============================================


# ST7789 LCD屏幕控制芯片类
class ST7789:
    """
    ST7789 驱动类，封装与 ST7789 系列显示控制器通信的低级接口与基本图形/文本绘制功能。

    该类直接操作 SPI 与控制引脚（DC/RESET/CS/背光），实现初始化序列、寄存器写入、
    窗口设置、像素/矩形/直线/多边形等基础绘制操作，并为更高层的 UI 类（如 LCD）提供稳定的底层支持。

    Attributes:
        spi (machine.SPI): 用于与显示器通信的 SPI 实例。（MicroPython 内置类型：machine.SPI）
        dc (machine.Pin): 数据/命令选择引脚实例。（MicroPython 内置类型：machine.Pin）
        reset (machine.Pin | None): 复位引脚实例或 None。（MicroPython 内置类型：machine.Pin / None）
        cs (machine.Pin | None): 片选引脚实例或 None。（MicroPython 内置类型：machine.Pin / None）
        backlight (machine.Pin | None): 背光引脚实例或 None。（MicroPython 内置类型：machine.Pin / None）
        width (int): 当前逻辑宽度（像素，随 rotation 变化）。（MicroPython 内置类型：int）
        height (int): 当前逻辑高度（像素，随 rotation 变化）。（MicroPython 内置类型：int）
        physical_width (int): 屏幕物理宽度（像素）。（MicroPython 内置类型：int）
        physical_height (int): 屏幕物理高度（像素）。（MicroPython 内置类型：int）
        xstart (int): 列偏移（MicroPython 内置类型：int）。
        ystart (int): 行偏移（MicroPython 内置类型：int）。
        rotations (tuple): 支持的旋转表（每项包含 MADCTL/width/height/xstart/ystart/needs_swap）。（MicroPython 内置类型：tuple）
        init_cmds (tuple): 用于初始化显示器的命令序列（command,data,delay_ms）。（MicroPython 内置类型：tuple）
        needs_swap (bool): 指示写入像素时是否需要交换字节序（MicroPython 内置类型：bool）。
        color_order (int): 像素字节顺序标志（例如 BGR/RGB 常量）。（MicroPython 内置类型：int）
        _rotation (int): 当前旋转索引 0-3。（MicroPython 内置类型：int）

    Methods:
        __init__(self, spi: machine.SPI, width: int, height: int,
                 reset: machine.Pin = None, dc: machine.Pin = None, cs: machine.Pin = None,
                 backlight: machine.Pin = None, rotation: int = 0,
                 color_order: int = BGR, custom_init: tuple = None, custom_rotations: tuple = None) -> None:
            构造函数，初始化引脚/状态、执行硬复位并按 init_cmds 初始化显示器。
            Raises:
                ValueError: 若分辨率不被支持或缺少必需引脚（例如 dc）。

        _find_rotations(width: int, height: int) -> tuple | None:
            静态方法，根据物理尺寸查找支持的 rotations 表，找不到则返回 None。

        init(self, commands: tuple) -> None:
            按序发送初始化命令序列。commands 每项格式为 (command: bytes, data: bytes, delay_ms: int)。

        _write(self, command: bytes = None, data: bytes = None) -> None:
            低级写入：处理 CS/DC 引脚并通过 SPI 发送 command/data（command 或 data 可为 None）。

        hard_reset(self) -> None:
            硬复位：使用 reset 引脚执行时序（包含必要的延时），并在结束时释放 CS。

        soft_reset(self) -> None:
            软复位：发送 SWRESET 命令并等待。

        sleep_mode(self, value: bool) -> None:
            进入/退出睡眠（SLPIN/SLPOUT），value=True 表示进入睡眠。

        inversion_mode(self, value: bool) -> None:
            打开/关闭显示反转（INVON/INVOFF），value 表示是否开启。

        rotation(self, rotation: int) -> None:
            应用旋转索引：更新 MADCTL/width/height/xstart/ystart/needs_swap，并写入 MADCTL。

        _set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
            限定后续像素写入矩形区域，向 CASET/RASET 写入地址并发送 RAMWR。

        pixel(self, x: int, y: int, color: int) -> None:
            在 (x,y) 写入单像素，依据 needs_swap 选择像素字节序。

        hline / vline / rect / fill_rect / fill (各种形状绘制):
            基本图形绘制方法，fill_rect 使用 _BUFFER_SIZE 分块写入以控制内存占用。

        blit_buffer(self, buffer: bytes | bytearray | memoryview, x: int, y: int, width: int, height: int) -> None:
            将已按当前像素字节序组织的像素缓冲区写入屏幕（支持 bytes/bytearray/memoryview）。

        line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
            使用 Bresenham 算法绘制直线。

        vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
            设置垂直滚动区域（TFA/VSA/BFA），参数以像素为单位。

        vscsad(self, vssa: int) -> None:
            设置垂直滚动起始地址（Vertical Scroll Start Address）。

        _pack8 / _pack16 (viper 优化函数):
            高性能内部打包函数，用于将字形数据转换成像素缓冲（用于 _text8/_text16）。
            **重要**: 由于 @micropython.viper 的限制，函数签名中不得使用 `bytearray`, `bytes`, `memoryview` 或返回类型注解，
            这些注解会导致 ViperTypeError。可在 docstring 中说明返回值类型（如返回 bytearray），但不要写入签名。

        _text8(self, font, text: str, x0: int, y0: int, fg_color: int, bg_color: int) -> None:
            基于 8 宽字形的文本绘制实现（调用 _pack8 + blit_buffer）。

        _text16(self, font, text: str, x0: int, y0: int, fg_color: int, bg_color: int) -> None:
            基于 16 宽字形的文本绘制实现（调用 _pack16 + blit_buffer）。

        text(self, font, text: str, x0: int, y0: int, color: int = WHITE, background: int = BLACK) -> None:
            高层文本接口：根据 font.WIDTH 自动切换 _text8/_text16，并在必要时调整字节序。

        bitmap / pbitmap:
            位图绘制方法：bitmap 一次性打包整个位图（占用内存较大），pbitmap 按行绘制以节省内存。

        write(self, font, string: str, x: int, y: int, fg: int = WHITE, bg: int = BLACK) -> None:
            使用转换后的 TrueType 风格字体逐字符写入（支持 variable-width 与偏移表的字体）。

        write_width(self, font, string: str) -> int:
            计算字符串绘制所需像素宽度并返回（用于排版/对齐）。

        polygon(self, points: list, x: int, y: int, color: int, angle: float = 0.0, center_x: int = 0, center_y: int = 0) -> None:
            绘制闭合多边形，支持可选旋转；当 points 长度 < 3 时抛出 ValueError。

    Usage Notes:
        - 对于 @micropython.viper 装饰的内部函数（如 _pack8/_pack16），签名中不要使用复杂类型注解，
          建议只为整型参数使用注解 (int)，并在 docstring 中说明其他参数与返回类型。
        - 所有外部可见接口使用 MicroPython 常见内置类型进行说明（int/bytes/bytearray/memoryview/str/list/tuple/machine.Pin/machine.SPI）。
        - 在内存受限的设备上优先使用逐行或分块绘制（pbitmap / fill_rect 分块），避免一次性分配超大缓冲。
        - 若遇到 Viper 编译错误（例如 ViperTypeError），检查被装饰函数的注解并去掉不被支持的类型注解。
    """

    def __init__(
        self,
        spi: "machine.SPI",
        width: int,
        height: int,
        reset: "machine.Pin" = None,
        dc: "machine.Pin" = None,
        cs: "machine.Pin" = None,
        backlight: "machine.Pin" = None,
        rotation: int = 0,
        color_order: int = BGR,
        custom_init: tuple = None,
        custom_rotations: tuple = None,
    ) -> None:
        """
        ST7789 的初始化方法。

        Args:
            spi (machine.SPI): 已配置的 SPI 实例，用于与显示屏通信（MicroPython 内置类型：machine.SPI）。
            width (int): 屏幕物理宽度（像素）。 (MicroPython 内置类型：int)
            height (int): 屏幕物理高度（像素）。 (MicroPython 内置类型：int)
            reset (machine.Pin, optional): 复位引脚实例，若不需要可传 None。默认 None。（MicroPython 内置类型：machine.Pin）
            dc (machine.Pin, optional): 数据/命令引脚实例。**必需**（若未提供将抛出 ValueError）。默认 None。（MicroPython 内置类型：machine.Pin）
            cs (machine.Pin, optional): 片选引脚实例，若使用可提供，默认 None。（MicroPython 内置类型：machine.Pin）
            backlight (machine.Pin, optional): 背光引脚实例，若提供则会初始化并置为开启状态，默认 None。（MicroPython 内置类型：machine.Pin）
            rotation (int, optional): 旋转索引值（0-3），指示显示方向。默认 0。（MicroPython 内置类型：int）
            color_order (int, optional): 指定像素数据的顺序（例如 BGR/RGB 常量）。默认 BGR。（MicroPython 内置类型：int）
            custom_init (tuple, optional): 自定义初始化命令的元组，若提供则覆盖默认初始化命令。默认 None。（MicroPython 内置类型：tuple）
            custom_rotations (tuple, optional): 自定义旋转信息的元组，若提供则覆盖自动查找的旋转表。默认 None。（MicroPython 内置类型：tuple）

        Returns:
            None: 构造函数不返回值。（MicroPython 内置类型：None）

        Raises:
            ValueError: 当所给 width x height 不在支持的显示列表中时，会抛出该异常，消息中包含支持的分辨率列表。
            ValueError: 当未提供必需的 dc 引脚时，会抛出该异常（"dc pin is required."）。
        """

        # 根据屏幕尺寸和旋转角度找到支持的旋转信息
        self.rotations = custom_rotations or self._find_rotations(width, height)
        if not self.rotations:
            supported_displays = ", ".join([f"{display[0]}x{display[1]}" for display in _SUPPORTED_DISPLAYS])
            raise ValueError(f"Unsupported {width}x{height} display. Supported displays: {supported_displays}")

        # 检查是否提供了 DC 引脚，若没有提供，则抛出一个 ValueError 异常
        if dc is None:
            raise ValueError("dc pin is required.")

        # 设置屏幕的物理尺寸和逻辑尺寸
        self.physical_width = self.width = width
        self.physical_height = self.height = height
        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        # 计算并设置旋转角度
        self._rotation = rotation % 4
        self.color_order = color_order
        # 如果提供了自定义的初始化命令，则使用它们，否则使用默认的命令
        self.init_cmds = custom_init or _ST7789_INIT_CMDS

        # 初始化控制引脚
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.reset.init(self.reset.OUT, value=1)
        # 如果提供了背光引脚，则初始化它
        if backlight is not None:
            self.backlight.init(self.backlight.OUT, value=1)

        # 硬重置显示屏
        self.hard_reset()
        # 进行两次初始化
        self.init(self.init_cmds)
        self.init(self.init_cmds)
        # 设置旋转角度
        self.rotation(self._rotation)
        # 标记是否需要交换像素数据
        self.needs_swap = False
        # 用白色填充屏幕
        self.fill(0x0)

    @staticmethod
    def _find_rotations(width: int, height: int) -> "tuple | None":
        """
        根据屏幕的物理尺寸和逻辑尺寸，找到支持的旋转信息。

        Args:
            width (int): 屏幕宽度（像素）。(MicroPython 内置类型：int)
            height (int): 屏幕高度（像素）。(MicroPython 内置类型：int)

        Returns:
            tuple | None: 若找到匹配项，返回该显示规格对应的旋转表（tuple，MicroPython 内置类型：tuple）。
                          若未找到，返回 None（MicroPython 内置类型：None）。

        """
        for display in _SUPPORTED_DISPLAYS:
            if display[0] == width and display[1] == height:
                return display[2]
        return None

    def init(self, commands: tuple) -> None:
        """
        初始化屏幕。

        Args:
            commands (tuple): 初始化命令的元组。每个元素应为三元组：(command_bytes, data_bytes, delay_ms)。
                              - command_bytes (bytes): 命令字节序列（MicroPython 内置类型：bytes）
                              - data_bytes (bytes): 紧随命令发送的数据字节序列（MicroPython 内置类型：bytes）
                              - delay_ms (int): 发送该命令后需要等待的毫秒数（MicroPython 内置类型：int）
                          整体类型为 tuple（MicroPython 内置类型：tuple），例如:
                          ((b'\x01', b'', 150), (b'\x11', b'', 255), ...)

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Raises:
            TypeError: 如果 commands 不是可迭代的三元组序列，调用方可能收到此类异常（实现层会在迭代/解包时触发）。
        """
        for command, data, delay in commands:
            self._write(command, data)
            time.sleep_ms(delay)

    def _write(self, command: bytes = None, data: bytes = None) -> None:
        """
        向屏幕写入数据或命令。

        Args:
            command (bytes, optional): 要发送的命令字节序列，若无命令可传 None。默认 None。（MicroPython 内置类型：bytes 或 None）
            data (bytes, optional): 要发送的数据字节序列，若无数据可传 None。默认 None。（MicroPython 内置类型：bytes 或 None）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 如果存在片选引脚(self.cs)，发送前会将其拉低以选择设备，数据/命令区分由 dc 引脚控制。
            - 本方法假设 self.spi、self.dc、self.cs 均已按需初始化并可安全调用对应方法（on/off/write）。
        """
        if self.cs:
            # 给CS引脚置低电平以选择设备
            self.cs.off()
        if command is not None:
            # 给DC引脚置低电平以发送命令
            self.dc.off()
            # 向设备发送命令字节
            self.spi.write(command)
        if data is not None:
            # 拉高DC引脚以发送数据
            self.dc.on()
            # 向设备发送数据字节
            self.spi.write(data)
            if self.cs:
                # 拉高CS引脚以结束数据传输
                self.cs.on()

    def hard_reset(self) -> None:
        """
        硬重置屏幕，通过复位引脚产生完整的复位时序并等待芯片启动。

        Args:
            None

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 当存在片选引脚(self.cs)时，会在复位前拉低 CS 以选择设备，复位完成后拉高 CS 以结束传输。
            - 假定 self.reset、self.cs 已正确初始化为 machine.Pin 实例并提供 on()/off() 方法。
        """
        if self.cs:
            # 给CS引脚置低电平以选择设备
            self.cs.off()
        if self.reset:
            # 给RESET引脚置高电平以开始重置屏幕
            self.reset.on()
        # 等待 10 毫秒
        time.sleep_ms(10)
        if self.reset:
            # 给RESET引脚置低电平以结束重置屏幕
            self.reset.off()
        time.sleep_ms(10)
        if self.reset:
            # 给RESET引脚置高电平以唤醒芯片
            self.reset.on()
        # 等待120毫秒，确保芯片完全初始化
        time.sleep_ms(120)
        if self.cs:
            # 拉高CS引脚以结束数据传输
            self.cs.on()

    def soft_reset(self) -> None:
        """
        软重置屏幕，通过发送软复位命令来让显示控制器执行复位流程。

        Args:
            None

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 该方法向设备发送 _ST7789_SWRESET 命令并等待固定延时以确保生效。
            - 假定 self._write 可用并能正确发送命令到显示器。
        """
        # 通过发送软复位命令来重置液晶屏
        self._write(_ST7789_SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value: bool) -> None:
        """
        启用或禁用显示休眠模式（Sleep In / Sleep Out）。

        Args:
            value (bool): 如果为 True，则启用休眠模式（发送 SLPIN）；如果为 False，则退出休眠模式（发送 SLPOUT）。
                          (MicroPython 内置类型：bool)

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)

    def inversion_mode(self, value: bool) -> None:
        """
        设置屏幕显示是否反色（Display Inversion On/Off）。

        Args:
            value (bool): True 表示开启屏幕反转（INVON），False 表示关闭屏幕反转（INVOFF）。
                          (MicroPython 内置类型：bool)

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        if value:
            self._write(_ST7789_INVON)
        else:
            self._write(_ST7789_INVOFF)

    def rotation(self, rotation: int) -> None:
        """
        设置并应用显示旋转/翻转模式 (更新 MADCTL 寄存器并调整逻辑宽高/偏移)。

        Args:
            rotation (int): 旋转索引（0-3），代表：
                           - 0: Portrait（竖屏 / 默认）
                           - 1: Landscape（横屏）
                           - 2: Inverted Portrait（竖屏翻转）
                           - 3: Inverted Landscape（横屏翻转）
                           (MicroPython 内置类型：int)

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Raises:
            IndexError: 如果 self.rotations 为空或结构不正确，索引访问可能抛出异常（通常在初始化阶段已被校验以避免此情况）。
        """

        # 计算旋转后的索引
        rotation %= len(self.rotations)
        # 更新当前旋转值
        self._rotation = rotation
        # 获取旋转后的参数
        (
            madctl,
            self.width,
            self.height,
            self.xstart,
            self.ystart,
            self.needs_swap,
        ) = self.rotations[rotation]

        # 根据颜色顺序设置 MADCTL 寄存器
        if self.color_order == BGR:
            madctl |= _ST7789_MADCTL_BGR
        else:
            madctl &= ~_ST7789_MADCTL_BGR
        # 写入 MADCTL 寄存器
        self._write(_ST7789_MADCTL, bytes([madctl]))

    def _set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """
        设置窗口区域，将屏幕上的像素数据更新到指定的矩形区域内。

        Args:
            x0 (int): 窗口区域的左上角横坐标，取值范围为 [0, self.width)。（MicroPython 内置类型：int）
            y0 (int): 窗口区域的左上角纵坐标，取值范围为 [0, self.height)。（MicroPython 内置类型：int）
            x1 (int): 窗口区域的右下角横坐标，取值范围为 [x0, self.width)。（MicroPython 内置类型：int）
            y1 (int): 窗口区域的右下角纵坐标，取值范围为 [y0, self.height)。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 如果提供的坐标不合法（不满足 x0 <= x1 <= self.width 或 y0 <= y1 <= self.height），
              本方法将不执行任何写入操作并直接返回。
            - 使用 struct.pack 将坐标按 _ENCODE_POS 指定的格式（通常为大端、每项 2 字节）打包后发送至 CASET/RASET 寄存器。
        """
        #  检查入口参数是否合法
        if x0 <= x1 <= self.width and y0 <= y1 <= self.height:
            # 向 CASET 寄存器写入列地址范围
            self._write(
                _ST7789_CASET,
                # 使用了 _ENCODE_POS 变量作为打包格式字符串，该字符串指定了每个整数的字节顺序和大小
                # _ENCODE_POS示使用大端字节序，每个整数占两个字节
                # 按照打包格式字符串将后两个参数进行打包以便于传输
                struct.pack(_ENCODE_POS, x0 + self.xstart, x1 + self.xstart),
            )
            # 向 RASET 寄存器写入行地址范围
            self._write(
                _ST7789_RASET,
                struct.pack(_ENCODE_POS, y0 + self.ystart, y1 + self.ystart),
            )
            # 开始写入像素数据到显存
            self._write(_ST7789_RAMWR)

    def vline(self, x: int, y: int, length: int, color: int) -> None:
        """
        在指定位置绘制垂直线。

        Args:
            x (int): 线的起始横坐标（MicroPython 内置类型：int）。
            y (int): 线的起始纵坐标（MicroPython 内置类型：int）。
            length (int): 线的高度（像素数）（MicroPython 内置类型：int）。
            color (int): 颜色值，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        self.fill_rect(x, y, 1, length, color)

    def hline(self, x: int, y: int, length: int, color: int) -> None:
        """
        在指定位置绘制水平线。

        Args:
            x (int): 线的起始横坐标（MicroPython 内置类型：int）。
            y (int): 线的起始纵坐标（MicroPython 内置类型：int）。
            length (int): 线的宽度（像素数）（MicroPython 内置类型：int）。
            color (int): 颜色值，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        self.fill_rect(x, y, length, 1, color)

    def pixel(self, x: int, y: int, color: int) -> None:
        """
        在指定位置绘制单个像素点。

        Args:
            x (int): 像素点的横坐标。（MicroPython 内置类型：int）
            y (int): 像素点的纵坐标。（MicroPython 内置类型：int）
            color (int): 像素颜色，16-bit 565 编码（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 会调用 _set_window 将窗口限定为单像素区域，然后根据 self.needs_swap 选择像素打包格式发送。
        """
        # 设置窗口区域
        self._set_window(x, y, x, y)
        # 写入像素数据
        self._write(
            None,
            # 将颜色值 color 打包成一个大端字节序或小端字节序的字节串，具体取决于 self.needs_swap 的值
            struct.pack(_ENCODE_PIXEL_SWAPPED if self.needs_swap else _ENCODE_PIXEL, color),
        )

    def blit_buffer(self, buffer: "bytes | bytearray | memoryview", x: int, y: int, width: int, height: int) -> None:
        """
        在指定位置绘制一个缓冲区中的图像。

        Args:
            buffer (bytes | bytearray | memoryview): 要绘制的图像缓冲区，按像素顺序组织（MicroPython 内置类型：bytes/bytearray/memoryview）。
            x (int): 图像在屏幕上的起始横坐标（MicroPython 内置类型：int）。
            y (int): 图像在屏幕上的起始纵坐标（MicroPython 内置类型：int）。
            width (int): 图像的宽度（像素）（MicroPython 内置类型：int）。
            height (int): 图像的高度（像素）（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 假定 buffer 的长度与 width*height*(bytes_per_pixel) 一致。
            - 本方法不会对 buffer 长度做严格校验，调用方需保证数据完整性。
        """
        # 设置窗口区域
        self._set_window(x, y, x + width - 1, y + height - 1)
        # 绘制一个缓冲区中的图像
        self._write(None, buffer)

    def rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """
        绘制矩形边框。

        Args:
            x (int): 矩形左上角横坐标（MicroPython 内置类型：int）。
            y (int): 矩形左上角纵坐标（MicroPython 内置类型：int）。
            w (int): 矩形宽度（像素）（MicroPython 内置类型：int）。
            h (int): 矩形高度（像素）（MicroPython 内置类型：int）。
            color (int): 矩形边框颜色，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        self.hline(x, y, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        self.hline(x, y + h - 1, w, color)

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> None:
        """
        绘制一个填充的矩形。

        Args:
            x (int): 矩形左上角横坐标（MicroPython 内置类型：int）。
            y (int): 矩形左上角纵坐标（MicroPython 内置类型：int）。
            width (int): 矩形宽度（像素）（MicroPython 内置类型：int）。
            height (int): 矩形高度（像素）（MicroPython 内置类型：int）。
            color (int): 矩形填充颜色，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 使用常量 _BUFFER_SIZE 将像素数量分块发送以节省内存。
            - 根据 self.needs_swap 选择打包像素的字节序格式 _ENCODE_PIXEL 或 _ENCODE_PIXEL_SWAPPED。
        """
        # 设置窗口区域
        self._set_window(x, y, x + width - 1, y + height - 1)
        # 计算矩形的像素数量，并将其分成大小为 _BUFFER_SIZE 的块
        # divmod() 函数把除数和余数运算结果结合起来，返回一个包含商和余数的元组
        # chunks 是完整块的个数，rest 是剩余不足一个块的像素数
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        # 将颜色值 color 打包成一个像素值
        # 如果 self.needs_swap 为真，则使用 _ENCODE_PIXEL_SWAPPED 格式打包
        # 否则，使用 _ENCODE_PIXEL 格式打包
        pixel = struct.pack(_ENCODE_PIXEL_SWAPPED if self.needs_swap else _ENCODE_PIXEL, color)
        # DC拉高，表示发送数据
        self.dc.on()
        # 如果存在完整块，则执行以下操作
        if chunks:
            # 创建一个包含多个像素值的字节串
            data = pixel * _BUFFER_SIZE
            # 将当前块的数据写入设备
            for _ in range(chunks):
                self._write(None, data)
        # 如果存在剩余不足一个块的像素，则执行以下操作
        if rest:
            # 将剩余像素的数据写入设备
            self._write(None, pixel * rest)

    def fill(self, color: int) -> None:
        """
        使用指定颜色填充整个屏幕。

        Args:
            color (int): 填充颜色，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        """
        绘制一条直线（Bresenham 算法实现）。

        Args:
            x0 (int): 起点横坐标（MicroPython 内置类型：int）。
            y0 (int): 起点纵坐标（MicroPython 内置类型：int）。
            x1 (int): 终点横坐标（MicroPython 内置类型：int）。
            y1 (int): 终点纵坐标（MicroPython 内置类型：int）。
            color (int): 线段颜色，16-bit 565 编码（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 若线段斜率大于 1，会交换 x/y 以减少循环次数（steep 优化）。
        """
        # 判断直线斜率是否大于1，如果是则交换x0和y0，以优化计算过程
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        # 确保x0小于等于x1，以便按顺序处理点
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        # 计算dx和dy，分别表示x轴和y轴上的增量
        dx = x1 - x0
        dy = abs(y1 - y0)
        # 初始化误差值err，用于计算每一步的y坐标
        err = dx // 2
        # 根据斜率确定y轴的步长，确保y坐标递增或递减
        ystep = 1 if y0 < y1 else -1
        # 当x0小于等于x1时，循环绘制直线
        while x0 <= x1:
            # 如果斜率大于1，则按y0、x0的顺序绘制点；否则按x0、y0的顺序绘制点
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            # 更新误差值err
            err -= dy
            # 如果误差值小于0，说明需要增加y坐标，更新y0并调整误差值
            if err < 0:
                y0 += ystep
                err += dx
            # 增加x坐标，准备绘制下一个点
            x0 += 1

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        """
        设置垂直滚动显示的区域（Top Fixed Area / Vertical Scroll Area / Bottom Fixed Area）。

        示例（对于 135x240 屏幕）：tfa=40, vsa=240, bfa=40。

        Args:
            tfa (int): 顶部固定区域高度（像素）（MicroPython 内置类型：int）。
            vsa (int): 垂直滚动区域高度（像素）（MicroPython 内置类型：int）。
            bfa (int): 底部固定区域高度（像素）（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        # 将屏幕的垂直滚动起始地址、垂直滚动结束地址和缓冲区地址写入到 ST7789 液晶屏的寄存器中
        self._write(_ST7789_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa: int) -> None:
        """
        设置垂直滚动起始地址（Vertical Scroll Start Address），定义从帧内存中哪个行开始显示。

        Args:
            vssa (int): 垂直滚动起始地址（MicroPython 内置类型：int）。

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Example:
            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)
        """
        # 将垂直滚动起始地址写入到 ST7789 液晶屏的寄存器中
        self._write(_ST7789_VSCSAD, struct.pack(">H", vssa))

    # 使用Viper代码发射器
    @micropython.viper
    # 静态方法修饰器，静态方法通常用于实现与类相关的功能，但不需要访问实例变量或方法
    @staticmethod
    def _pack8(glyphs, idx: int, fg_color: int, bg_color: int):
        """
        将给定的字符索引、前景色和背景色打包成 8 位像素值的字节数组（用于 8x8 字形或 8x16 的每一半）。
        @micropython.viper 不支持你在函数签名里使用像 bytearray、联合类型（bytes | bytearray | memoryview）或返回类型注解（-> bytearray）这类高级类型注释

        Args:
            glyphs (bytes | bytearray | memoryview): 字形表，包含字符的字形数据（MicroPython 内置类型：bytes/bytearray/memoryview）。
            idx (int): 要处理的字符在字形表中的起始索引偏移（MicroPython 内置类型：int）。
            fg_color (int): 前景色（用于像素为 1 的位置）（MicroPython 内置类型：int）。
            bg_color (int): 背景色（用于像素为 0 的位置）（MicroPython 内置类型：int）。

        Returns:
            bytearray: 返回一个包含打包后像素值的字节数组（长度 128 字节），可直接用于 blit（MicroPython 内置类型：bytearray）。

        Notes:
            - 本函数使用 viper 优化并假设可用 ptr8/ptr16 类型转换函数以提高速度。
        """
        # 创建一个大小为 128 字节的字节数组 buffer
        buffer = bytearray(128)
        # 需要忽略PyCharm对ptr16和ptr8的警告
        # 将 buffer 转换为指向 16 位整数的指针 bitmap
        bitmap = ptr16(buffer)
        # 将 glyphs 转换为指向 8 位整数的指针 glyph
        glyph = ptr8(glyphs)

        # # 遍历 64 个连续的 8 位像素点
        for i in range(0, 64, 8):
            # # 从 glyph 中获取当前字符的字节数据
            byte = glyph[idx]
            # 根据字节的每一位设置 bitmap 中对应位置的像素值
            # 如果当前位为 1，则像素值为前景色，否则为背景色
            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            # 处理下一个字符
            idx += 1

        # 返回打包后的像素值字节数组
        return buffer

    @micropython.viper
    @staticmethod
    def _pack16(glyphs, idx: int, fg_color: int, bg_color: int):
        """
        将给定的字符索引、前景色和背景色打包成 16 位像素值的字节数组（用于 16 宽字符，每次打包 128 个 16-bit 像素点 -> 256 字节）。
        @micropython.viper 不支持你在函数签名里使用像 bytearray、联合类型（bytes | bytearray | memoryview）或返回类型注解（-> bytearray）这类高级类型注释

        Args:
            glyphs (bytes | bytearray | memoryview): 字形表（MicroPython 内置类型：bytes/bytearray/memoryview）。
            idx (int): 字形表中的起始字节索引（MicroPython 内置类型：int）。
            fg_color (int): 前景色（MicroPython 内置类型：int）。
            bg_color (int): 背景色（MicroPython 内置类型：int）。

        Returns:
            bytearray: 返回一个包含打包后像素值的字节数组（长度 256 字节），可直接用于 blit（MicroPython 内置类型：bytearray）。
        """

        # 创建一个大小为 256 字节的字节数组 buffer
        buffer = bytearray(256)
        # 需要忽略PyCharm对ptr16和ptr8的警告
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        # 遍历 128 个连续的 16 位像素点
        for i in range(0, 128, 16):
            # 获取当前字符的字形数据
            byte = glyph[idx]

            # 根据字形的每一位设置像素点的颜色
            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            # 更新字符索引
            idx += 1

            # 获取下一个字符的字形数据
            byte = glyph[idx]
            bitmap[i + 8] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 9] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 10] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 11] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 12] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 13] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 14] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 15] = fg_color if byte & _BIT0 else bg_color
            # 更新字符索引
            idx += 1

        return buffer

    def _text8(self, font, text: str, x0: int, y0: int, fg_color: int = WHITE, bg_color: int = BLACK) -> None:
        """
        用于绘制宽度为 8 的字符（高度为 8 或 16）。

        Args:
            font (module | object): 字体模块/对象，需包含 FIRST, LAST, WIDTH, HEIGHT, FONT 常量/属性（MicroPython 内置类型：module/object）。
            text (str): 要绘制的文本字符串。（MicroPython 内置类型：str）
            x0 (int): 开始绘制的列（MicroPython 内置类型：int）。
            y0 (int): 开始绘制的行（MicroPython 内置类型：int）。
            fg_color (int, optional): 前景色（默认 WHITE）。（MicroPython 内置类型：int）
            bg_color (int, optional): 背景色（默认 BLACK）。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """

        # 遍历文本中的每个字符
        for char in text:
            # 将字符转换为ASCII码
            ch = ord(char)
            # 检查字符是否在字体支持的范围内，并且当前位置没有超出屏幕范围
            if font.FIRST <= ch < font.LAST and x0 + font.WIDTH <= self.width and y0 + font.HEIGHT <= self.height:
                # 根据字体的高度选择绘制方式
                if font.HEIGHT == 8:
                    # 绘制8x8像素的字符
                    passes = 1
                    size = 8
                    each = 0
                else:
                    # 绘制16x16像素的字符
                    passes = 2
                    size = 16
                    each = 8
                # 遍历每一行
                for line in range(passes):
                    # 计算当前字符在字体中的索引
                    idx = (ch - font.FIRST) * size + (each * line)
                    # 将字符数据打包成8位二进制格式
                    buffer = self._pack8(font.FONT, idx, fg_color, bg_color)
                    # 在屏幕上绘制打包后的字符数据
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8)
                # 更新下一个字符的起始列
                x0 += 8

    def _text16(self, font, text: str, x0: int, y0: int, fg_color: int = WHITE, bg_color: int = BLACK) -> None:
        """
        用于绘制宽度为 16 的字符（高度为 16 或 32）。

        Args:
            font (module | object): 字体模块/对象，需包含 FIRST, LAST, WIDTH, HEIGHT, FONT 常量/属性（MicroPython 内置类型：module/object）。
            text (str): 要绘制的文本字符串。（MicroPython 内置类型：str）
            x0 (int): 开始绘制的列（MicroPython 内置类型：int）。
            y0 (int): 开始绘制的行（MicroPython 内置类型：int）。
            fg_color (int, optional): 前景色（默认 WHITE）。（MicroPython 内置类型：int）
            bg_color (int, optional): 背景色（默认 BLACK）。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        # 遍历文本中的每个字符
        for char in text:
            # 将字符转换为ASCII码
            ch = ord(char)
            # 检查字符是否在字体支持的范围内，并且当前位置没有超出屏幕范围
            if font.FIRST <= ch < font.LAST and x0 + font.WIDTH <= self.width and y0 + font.HEIGHT <= self.height:
                # 根据字体的高度决定绘制几行
                each = 16
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                # 遍历每一行
                for line in range(passes):
                    # 计算当前字符在字体中的索引
                    idx = (ch - font.FIRST) * size + (each * line)
                    # 将字符数据打包成16位字节的缓冲区
                    buffer = self._pack16(font.FONT, idx, fg_color, bg_color)
                    # 在屏幕上绘制缓冲区
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8)
            # 移动到下一个字符的位置
            x0 += 16

    def text(self, font, text: str, x0: int, y0: int, color: int = WHITE, background: int = BLACK) -> None:
        """
        在指定位置绘制文本。

        Args:
            font (module | object): 要使用的字体模块/对象，需包含 WIDTH, HEIGHT 等属性。（MicroPython 内置类型：module/object）
            text (str): 要写入的文本字符串。（MicroPython 内置类型：str）
            x0 (int): 开始绘制的列（MicroPython 内置类型：int）
            y0 (int): 开始绘制的行（MicroPython 内置类型：int）
            color (int, optional): 前景色（默认 WHITE），为 16-bit 565 编码。（MicroPython 内置类型：int）
            background (int, optional): 背景色（默认 BLACK），为 16-bit 565 编码。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 根据 self.needs_swap 调整前景色和背景色的字节序，然后根据字体宽度选择 _text8 或 _text16。
        """
        # 根据当前是否需要字节序交换，调整前景色和背景色的字节序
        fg_color = color if self.needs_swap else ((color << 8) & 0xFF00) | (color >> 8)
        bg_color = background if self.needs_swap else ((background << 8) & 0xFF00) | (background >> 8)
        # 如果字体宽度为 8 位，则调用 _text8 方法绘制文本
        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, fg_color, bg_color)
        # 否则，调用 _text16 方法绘制文本
        else:
            self._text16(font, text, x0, y0, fg_color, bg_color)

    def bitmap(self, bitmap, x: int, y: int, index: int = 0) -> None:
        """
        在指定位置绘制位图（一次性把整个位图打包到内存并写出）。

        Args:
            bitmap (module | object): 位图模块/对象，需包含 WIDTH, HEIGHT, BPP, PALETTE, BITMAP 等属性。（MicroPython 内置类型：module/object）
            x (int): 绘制起始横坐标。（MicroPython 内置类型：int）
            y (int): 绘制起始纵坐标。（MicroPython 内置类型：int）
            index (int, optional): 位图调色板索引偏移，默认为 0。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Notes:
            - 每个像素占用两个字节（16-bit），生成的缓冲区大小为 width*height*2 字节。
            - 调用方需确保绘制区域不会超出显示范围或接受被截断。
        """
        # 位图宽度
        width = bitmap.WIDTH
        # 位图高度
        height = bitmap.HEIGHT
        # 绘制结束横坐标
        to_col = x + width - 1
        # 绘制结束纵坐标
        to_row = y + height - 1
        # 如果绘制区域超出屏幕范围，则直接返回
        if self.width <= to_col or self.height <= to_row:
            return

        # 位图大小
        bitmap_size = height * width
        # 缓冲区长度，每个像素占用两个字节
        buffer_len = bitmap_size * 2
        # 位图每个像素的位数
        bpp = bitmap.BPP
        # 如果 index > 0，则从对应调色板索引开始，否则从第一个调色板索引开始
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        # 位图调色板
        palette = bitmap.PALETTE
        # 是否需要交换字节序的标志
        needs_swap = self.needs_swap
        # 创建缓冲区
        buffer = bytearray(buffer_len)

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | ((bitmap.BITMAP[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1)
                bs_bit += 1

            # 获取当前像素对应的颜色值
            color = palette[color_index]
            if needs_swap:
                # 将颜色值拆分为两个字节，低字节在前
                buffer[i] = color & 0xFF
                # 高字节在后
                buffer[i + 1] = color >> 8
            else:
                # 将颜色值拆分为两个字节，高字节在前
                buffer[i] = color >> 8
                # 低字节在后
                buffer[i + 1] = color & 0xFF

        # 设置窗口区域
        self._set_window(x, y, to_col, to_row)
        # 将缓冲区中的数据写入屏幕
        self._write(None, buffer)

    def pbitmap(self, bitmap, x: int, y: int, index: int = 0) -> None:
        """
        在指定位置按行逐行绘制位图（节省内存，一次写入一行）。

        Args:
            bitmap (module | object): 位图模块/对象，需包含 WIDTH, HEIGHT, BPP, PALETTE, BITMAP 等属性。（MicroPython 内置类型：module/object）
            x (int): 绘制起始横坐标。（MicroPython 内置类型：int）
            y (int): 绘制起始纵坐标。（MicroPython 内置类型：int）
            index (int, optional): 位图调色板索引偏移，默认为 0。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        # 获取位图的宽度、高度、大小、位深度、起始位、调色板和是否需要交换字节序
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        bitmap_size = height * width
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        palette = bitmap.PALETTE
        needs_swap = self.needs_swap
        # 创建一个大小为位图宽度两倍的字节数组，用于存储每个像素的字节值
        buffer = bytearray(bitmap.WIDTH * 2)

        # 遍历位图的每一行
        for row in range(height):
            # 遍历当前行的每一个像素
            for col in range(width):
                color_index = 0
                # 从 MSB 到 LSB 依次提取像素颜色
                for _ in range(bpp):
                    color_index <<= 1
                    color_index |= (bitmap.BITMAP[bs_bit // 8] & 1 << (7 - (bs_bit % 8))) > 0
                    bs_bit += 1
                color = palette[color_index]
                # 根据当前设备的字节序交换颜色值的高低位
                if needs_swap:
                    buffer[col * 2] = color & 0xFF
                    buffer[col * 2 + 1] = color >> 8 & 0xFF
                else:
                    buffer[col * 2] = color >> 8 & 0xFF
                    buffer[col * 2 + 1] = color & 0xFF
            # 计算当前行绘制结束后的坐标
            to_col = x + width - 1
            to_row = y + row
            # 如果当前坐标在当前设备的显示范围内，则绘制该行
            if self.width > to_col and self.height > to_row:
                self._set_window(x, y + row, to_col, to_row)
                self._write(None, buffer)

    def write(self, font, string: str, x: int, y: int, fg: int = WHITE, bg: int = BLACK) -> None:
        """
        使用转换后的 TrueType 风格字体在显示屏上从指定的列和行开始写入字符串。

        Args:
            font (module | object): 转换后的字体对象，需包含 HEIGHT, MAX_WIDTH, MAP, OFFSET_WIDTH, OFFSETS, WIDTHS, BITMAPS 等属性。（MicroPython 内置类型：module/object）
            string (str): 要写入的文本字符串。（MicroPython 内置类型：str）
            x (int): 开始绘制的列（MicroPython 内置类型：int）
            y (int): 开始绘制的行（MicroPython 内置类型：int）
            fg (int, optional): 前景色，默认为 WHITE。（MicroPython 内置类型：int）
            bg (int, optional): 背景色，默认为 BLACK。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）
        """
        buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
        # 创建一个长度为 `buffer_len` 的字节数组 `buffer` 用于存储字符的像素数据
        buffer = bytearray(buffer_len)
        # 计算前景色和背景色的高位和低位字节
        fg_hi = fg >> 8
        fg_lo = fg & 0xFF

        bg_hi = bg >> 8
        bg_lo = bg & 0xFF

        # 遍历字符串中的每个字符
        for character in string:
            try:
                # 尝试获取当前字符在字体映射表中的索引
                char_index = font.MAP.index(character)
                # 根据索引计算字符的偏移量，并获取字符的位图数据
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                if font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]

                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]
                # 获取字符的宽度
                char_width = font.WIDTHS[char_index]
                # 计算需要写入缓冲区的数据长度
                buffer_needed = char_width * font.HEIGHT * 2

                # 遍历字符的每个像素，并根据位图数据设置缓冲区中的像素值
                for i in range(0, buffer_needed, 2):
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        buffer[i] = fg_hi
                        buffer[i + 1] = fg_lo
                    else:
                        buffer[i] = bg_hi
                        buffer[i + 1] = bg_lo

                    bs_bit += 1
                # 计算字符在显示屏上的结束列和行位置
                to_col = x + char_width - 1
                to_row = y + font.HEIGHT - 1
                # 检查当前字符是否在显示屏的可绘制区域内
                if self.width > to_col and self.height > to_row:
                    # 设置窗口区域并写入缓冲区数据
                    self._set_window(x, y, to_col, to_row)
                    self._write(None, buffer[:buffer_needed])
                # 更新当前字符的行位置
                x += char_width

            except ValueError:
                # 如果遇到无法在字体映射表中找到的字符，则忽略该字符
                pass

    def write_width(self, font, string: str) -> int:
        """
        计算使用指定字体绘制字符串时所占的总宽度（像素）。

        Args:
            font (module | object): 字体模块/对象，需包含 MAP 和 WIDTHS。（MicroPython 内置类型：module/object）
            string (str): 要测量的字符串。（MicroPython 内置类型：str）

        Returns:
            int: 字符串占用的像素宽度。（MicroPython 内置类型：int）
        """
        # 初始化宽度为0
        width = 0

        # 遍历字符串中的每个字符
        for character in string:
            try:
                # 在字库的MAP属性中找到对应的字符索引
                char_index = font.MAP.index(character)
                # 如果成功，将字符宽度累加到总宽度中
                width += font.WIDTHS[char_index]
            # 如果索引不存在（即字符不在字体中），则跳过该字符
            except ValueError:
                pass

        # 返回计算出的宽度
        return width

    @micropython.native
    def polygon(self, points, x: int, y: int, color: int, angle: float = 0.0, center_x: int = 0, center_y: int = 0) -> None:
        """
        绘制闭合多边形。

        Args:
            points (list): 要绘制的点列表，每个点为 (x, y) 二元组。（MicroPython 内置类型：list/tuple）
            x (int): 多边形整体偏移横坐标。（MicroPython 内置类型：int）
            y (int): 多边形整体偏移纵坐标。（MicroPython 内置类型：int）
            color (int): 绘制颜色，16-bit 565 编码。（MicroPython 内置类型：int）
            angle (float, optional): 旋转角度（弧度），默认 0。若为 0 则不做旋转。（MicroPython 内置类型：float）
            center_x (int, optional): 旋转中心的 X 坐标偏移，默认 0。（MicroPython 内置类型：int）
            center_y (int, optional): 旋转中心的 Y 坐标偏移，默认 0。（MicroPython 内置类型：int）

        Returns:
            None: 本方法不返回值。（MicroPython 内置类型：None）

        Raises:
            ValueError: 当 points 中点的数量少于 3 时抛出该异常。
        """
        # 检查多边形点数是否小于 3，如果是则抛出 ValueError 异常
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points.")
        # 如果有旋转角度，计算旋转后的点坐标
        if angle:
            cos_a = cos(angle)
            sin_a = sin(angle)
            rotated = [
                (
                    x + center_x + int((point[0] - center_x) * cos_a - (point[1] - center_y) * sin_a),
                    y + center_y + int((point[0] - center_x) * sin_a + (point[1] - center_y) * cos_a),
                )
                for point in points
            ]
        else:
            # 如果没有旋转角度，直接将点坐标加上偏移量
            rotated = [(x + int((point[0])), y + int((point[1]))) for point in points]

        # 遍历旋转后的点列表，依次绘制相邻两点之间的线段
        for i in range(1, len(rotated)):
            self.line(
                rotated[i - 1][0],
                rotated[i - 1][1],
                rotated[i][0],
                rotated[i][1],
                color,
            )
