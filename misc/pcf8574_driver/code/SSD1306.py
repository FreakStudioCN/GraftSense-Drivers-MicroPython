# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : SSD1306.py
# @Description : 主要定义了SSD 1306类

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# micropython相关模块
from micropython import const
# 帧缓冲区相关的模块
import framebuf
# 硬件相关的模块
from machine import I2C

# ======================================== 全局变量 ============================================

# 常量定义，用于控制 OLED 屏幕的各种操作
SET_CONTRAST        = const(0x81)  # 设置对比度，范围为 0x00 - 0xFF
SET_ENTIRE_ON       = const(0xA4)  # 设置整个屏幕亮起
SET_NORM_INV        = const(0xA6)  # 设置正常/反相显示模式，正常模式中高电平电亮而低电平熄灭
SET_DISP            = const(0xAE)  # 控制屏幕开关
SET_MEM_ADDR        = const(0x20)  # 设置页面寻址模式
SET_COL_ADDR        = const(0x21)  # 设置列地址
SET_PAGE_ADDR       = const(0x22)  # 设置页地址
SET_DISP_START_LINE = const(0x40)  # 设置起始行
SET_SEG_REMAP       = const(0xA0)  # 设置段重映射
SET_MUX_RATIO       = const(0xA8)  # 设置显示行数
SET_COM_OUT_DIR     = const(0xC0)  # 设置 COM 输出方向
SET_DISP_OFFSET     = const(0xD3)  # 设置显示偏移
SET_COM_PIN_CFG     = const(0xDA)  # 设置 COM 引脚配置
SET_DISP_CLK_DIV    = const(0xD5)  # 设置显示时钟分频
SET_PRECHARGE       = const(0xD9)  # 设置预充电周期
SET_VCOM_DESEL      = const(0xDB)  # 设置 VCOMH 电压
SET_CHARGE_PUMP     = const(0x8D)  # 设置电荷泵

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class SSD1306(framebuf.FrameBuffer):
    """
    SSD1306 OLED 显示驱动类，用于在 OLED 屏幕上绘制和显示数据。

    该类继承自 `framebuf.FrameBuffer`，通过 I2C 或 SPI 与 SSD1306 OLED 控制器通信，
    支持基本的显示控制操作，包括开关机、对比度调整、反显模式和图形绘制。

    Attributes:
        width (int): 屏幕宽度（像素）。
        height (int): 屏幕高度（像素）。
        external_vcc (bool): 是否使用外部电源供电。
        buffer (bytearray): 屏幕显存缓冲区，用于存储要显示的数据。
        pages (int): 屏幕页数，等于 height // 8。

    Methods:
        __init__(width: int, height: int, external_vcc: bool) -> None: 初始化屏幕参数。
        init_display() -> None: 发送初始化命令并清屏。
        poweroff() -> None: 关闭显示屏以节省功耗。
        poweron() -> None: 打开显示屏。
        contrast(contrast: int) -> None: 设置屏幕对比度 (0–255)。
        invert(invert: bool) -> None: 设置反相显示或正常显示。
        show() -> None: 将缓冲区数据刷新到屏幕。
        write_cmd(cmd: int) -> None: 向屏幕发送命令字节（需子类实现）。
        write_data(buf: bytearray) -> None: 向屏幕发送数据字节（需子类实现）。

    Notes:
        SSD1306 常见分辨率为 128x64 或 128x32。
        显示缓冲区大小等于 width × height ÷ 8。
        `write_cmd` 和 `write_data` 由具体子类实现（I2C 或 SPI）。
        `framebuf.MONO_VLSB` 模式：单色显示，最低位在前（小端位序）。

    ==========================================

    SSD1306 OLED driver class for rendering graphics and text on OLED screens.

    This class inherits from `framebuf.FrameBuffer`, providing communication
    with SSD1306 OLED controller via I2C or SPI. Supports display operations
    such as power control, contrast adjustment, inversion, and framebuffer drawing.

    Attributes:
        width (int): Screen width in pixels.
        height (int): Screen height in pixels.
        external_vcc (bool): Whether to use external VCC supply.
        buffer (bytearray): Framebuffer storing screen data.
        pages (int): Number of display pages (height // 8).

    Methods:
        __init__(width: int, height: int, external_vcc: bool) -> None: Initialize display parameters.
        init_display() -> None: Send initialization sequence and clear screen.
        poweroff() -> None: Turn display OFF (save power).
        poweron() -> None: Turn display ON.
        contrast(contrast: int) -> None: Set display contrast (0–255).
        invert(invert: bool) -> None: Set inverted or normal display mode.
        show() -> None: Update display with framebuffer content.
        write_cmd(cmd: int) -> None: Send command byte to display (must be implemented in subclass).
        write_data(buf: bytearray) -> None: Send data buffer to display (must be implemented in subclass).

    Notes:
        Common resolutions: 128x64, 128x32.
        Framebuffer size = width × height ÷ 8.
        `write_cmd` and `write_data` are hardware-specific (I2C/SPI).
        `framebuf.MONO_VLSB`: monochrome mode, least significant bit first.
    """

    def __init__(self, width: int, height: int, external_vcc: bool) -> None:
        """
        初始化 SSD1306 OLED 显示。

        Args:
            width (int): 屏幕宽度（像素）。
            height (int): 屏幕高度（像素）。
            external_vcc (bool): 是否使用外部电源供电。

        Notes:
            初始化时会创建显示缓冲区，并自动调用 `init_display()` 完成硬件设置。

        ==========================================

        Initialize SSD1306 OLED display.

        Args:
            width (int): Screen width in pixels.
            height (int): Screen height in pixels.
            external_vcc (bool): Whether to use external VCC supply.

        Notes:
            A framebuffer is allocated, and `init_display()` is called automatically.
        """
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        # 用于存储要显示在屏幕上的图像数据的字节数组
        self.buffer = bytearray(self.pages * self.width)
        # 父类framebuf.FrameBuffer初始化
        # framebuf.FrameBuffer类的构造方法
        # framebuf.FrameBuffer.__init__(self, buffer, width, height, format, stride, mapper)
        # 添加self.buffer到数据缓冲区来保存 I2C 数据/命令字节
        # framebuf.MONO_VLSB：表示使用单色（黑白）显示，并且最低位在前（小端字节序）
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self) -> None:
        """
        初始化屏幕显示。

        执行一系列命令以配置 SSD1306 的显示模式、时钟分频、对比度、充电泵等参数。
        初始化后会清空屏幕并刷新显示。

        Notes:
            `write_cmd()` 必须由子类实现（I2C 或 SPI）。
            初始化完成后屏幕点亮并显示空白内容。

        ==========================================

        Initialize display settings.

        Sends a sequence of commands to configure SSD1306 controller
        (addressing mode, scan direction, contrast, charge pump, etc.).
        Clears screen and refreshes display.

        Notes:
            `write_cmd()` must be implemented by subclass (I2C or SPI).
            Screen is turned ON and cleared after initialization.
        """
        for cmd in (
            SET_DISP | 0x00,            # 关屏
            SET_MEM_ADDR,               # 设置页面寻址模式
            0x00,                       # 水平地址自动递增
            # 分辨率和布局设置
            SET_DISP_START_LINE | 0x00, #设置GDDRAM起始行 0
            SET_SEG_REMAP | 0x01,       # 列地址 127 映射到 SEG0
            SET_MUX_RATIO,              # 设置显示行数
            self.height - 1,            # 显示128行
            SET_COM_OUT_DIR | 0x08,     # 从 COM[N] 到 COM0 扫描
            SET_DISP_OFFSET,            #设置垂直显示偏移(向上)
            0x00,                       # 偏移0行
            SET_COM_PIN_CFG,            # 设置 COM 引脚配置
            0x02 if self.width > 2 * self.height else 0x12, # 序列COM配置,禁用左右反置
            # 时序和驱动方案设置
            SET_DISP_CLK_DIV,           # 设置时钟分频
            0x80,                       #  无分频,第8级OSC频率
            SET_PRECHARGE,              # 设置预充电周期
            0x22 if self.external_vcc else 0xF1,            # 禁用外部供电
            SET_VCOM_DESEL,             # 设置VCOMH电压
            0x30,                       # 0.83*Vcc
            # 显示设置
            SET_CONTRAST,
            0xFF,                       # 设置为最大对比度，级别为255
            SET_ENTIRE_ON,              # 输出随 RAM 内容变化
            SET_NORM_INV,               # 非反转显示
            SET_CHARGE_PUMP,            # 充电泵设置
            0x10 if self.external_vcc else 0x14, # 启用电荷泵
            SET_DISP | 0x01,            # 开屏
        ):
            # 逐个发送指令
            # write_cmd(cmd)方法用于向OLED屏幕发送指令
            # 由继承SSD1306类的子类进行实现，根据通信方式不同，实现方式不同
            # write_cmd可通过SPI外设或I2C外设进行发送
            self.write_cmd(cmd)
        # 清除屏幕
        self.fill(0)
        # 将缓冲区中的数据显示在OLED屏幕上
        self.show()

    def poweroff(self) -> None:
        """
        关闭显示屏。

        Notes:
            屏幕关闭以节省功耗，但缓冲区内容仍然保留。

        ==========================================

        Turn display OFF.

        Notes:
            Saves power. Framebuffer content is preserved.
        """
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self) -> None:
        """
        打开显示屏。

        Notes:
            屏幕重新点亮并显示缓冲区中的数据。

        ==========================================

        Turn display ON.

        Notes:
            Restores display content from framebuffer.
        """

        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast: int) -> None:
        """
        设置屏幕对比度。

        Args:
            contrast (int): 对比度值，范围 0–255。

        Notes:
            较高的值使显示更亮，但可能缩短使用寿命。

        ==========================================

        Set display contrast.

        Args:
            contrast (int): Contrast value (0–255).

        Notes:
            Higher values increase brightness but may reduce lifespan.
        """

        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert: bool) -> None:
        """
        设置屏幕反显模式。

        Args:
            invert (bool): True → 反显模式，False → 正常模式。

        ==========================================

        Set inverted display mode.

        Args:
            invert (bool): True → inverted mode, False → normal mode.
        """

        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self) -> None:
        """
        刷新屏幕显示。

        将缓冲区中的数据写入 SSD1306 并更新屏幕。
        若修改了缓冲区内容，必须调用此方法才能生效。

        Notes:
            - 宽度为 64 的屏幕需要偏移列地址。
            - `write_data()` 必须由子类实现。

        ==========================================

        Update display.

        Transfers framebuffer content to SSD1306.
        Must be called after modifying the buffer to apply changes.

        Notes:
            - For width=64 displays, column address is shifted.
            - `write_data()` must be implemented by subclass.
        """

        # 计算显示区域的起始列和结束列
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # 宽度为 64 像素的屏幕需要将显示位置左移 32 像素
            x0 += 32
            x1 += 32

        # 向OLED屏幕发送列地址设置命令
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)

        # 向OLED屏幕发送页地址设置命令
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)

        # 向OLED屏幕发送数据显示命令，将缓冲区中的数据写入屏幕
        self.write_data(self.buffer)

    def write_cmd(self, cmd: int) -> None:
        """
        向 SSD1306 发送命令。

        Args:
            cmd (int): 要发送的命令字节。

        Raises:
            NotImplementedError: 该方法需由子类实现（I2C 或 SPI）。

        ==========================================

        Send command byte to SSD1306.

        Args:
            cmd (int): Command byte to send.

        Raises:
            NotImplementedError: Must be implemented in subclass (I2C or SPI).
        """

        pass

    def write_data(self, buf: bytearray) -> None:
        """
        向 SSD1306 发送数据。

        Args:
            buf (bytearray): 要发送的数据缓冲区。

        Raises:
            NotImplementedError: 该方法需由子类实现（I2C 或 SPI）。

        ==========================================

        Send data buffer to SSD1306.

        Args:
            buf (bytearray): Data buffer to send.

        Raises:
            NotImplementedError: Must be implemented in subclass (I2C or SPI).
        """

        pass

class SSD1306_I2C(SSD1306):
    """
    基于 I2C 接口的 SSD1306 OLED 显示类。

    继承自 `SSD1306`，通过 I2C 总线与 OLED 屏幕通信，提供显示控制和绘图功能。

    Attributes:
        i2c (I2C): I2C 总线对象，用于屏幕通信。
        addr (int): OLED 屏幕的 I2C 地址。
        temp (bytearray): 临时缓冲区，用于发送命令。
        write_list (list): I2C 写入缓冲区列表（包含数据控制字节和数据缓冲区）。

    Methods:
        __init__(i2c: I2C, addr: int, width: int, height: int, external_vcc: bool) -> None: 初始化 I2C 接口和屏幕。
        write_cmd(cmd: int) -> None: 发送命令字节到屏幕。
        write_data(buf: bytearray) -> None: 发送数据缓冲区到屏幕。

    ==========================================

    SSD1306 OLED display class using I2C interface.

    Inherits from `SSD1306`, communicates with OLED display via I2C bus,
    provides display control and drawing functionalities.

    Attributes:
        i2c (I2C): I2C bus object for communication.
        addr (int): OLED display I2C address.
        temp (bytearray): Temporary buffer for command transmission.
        write_list (list): I2C write list containing control byte and data buffer.

    Methods:
        __init__(i2c: I2C, addr: int, width: int, height: int, external_vcc: bool) -> None: Initialize I2C interface and display.
        write_cmd(cmd: int) -> None: Send command byte to display.
        write_data(buf: bytearray) -> None: Send data buffer to display.
    """

    def __init__(self, i2c: I2C, addr: int, width: int, height: int, external_vcc: bool) -> None:
        """
        初始化 I2C 接口与 SSD1306 显示屏。

        Args:
            i2c (I2C): I2C 总线对象。
            addr (int): OLED 屏幕 I2C 地址。
            width (int): 屏幕宽度（像素）。
            height (int): 屏幕高度（像素）。
            external_vcc (bool): 是否使用外部电源供电。

        Notes:
            - `temp` 用于发送命令（带有控制字节 0x80）。
            - `write_list` 用于发送数据（控制字节 0x40 + 数据缓冲区）。
            - 初始化完成后，会自动调用父类构造函数并完成显示设置。

        ==========================================

        Initialize I2C interface and SSD1306 display.

        Args:
            i2c (I2C): I2C bus object.
            addr (int): OLED display I2C address.
            width (int): Screen width in pixels.
            height (int): Screen height in pixels.
            external_vcc (bool): Whether to use external VCC.

        Notes:
            - `temp` is used for command transfer (with control byte 0x80).
            - `write_list` is used for data transfer (control byte 0x40 + data buffer).
            - Calls parent constructor to complete initialization.
        """

        self.i2c = i2c
        self.addr = addr
        # 用于临时存储数据的字节数组
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd: int) -> None:
        """
        发送命令字节到 SSD1306 显示屏。

        Args:
            cmd (int): 要发送的命令字节。

        Notes:
            - 使用控制字节 `0x80` 表示写入命令。
            - 通过 `i2c.writeto()` 发送。

        ==========================================

        Send command byte to SSD1306 display.

        Args:
            cmd (int): Command byte to send.

        Notes:
            - Uses control byte `0x80` for command transfer.
            - Sent via `i2c.writeto()`.
        """

        # 0x80表示写入的数据是命令
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf: bytearray) -> None:
        """
        发送数据缓冲区到 SSD1306 显示屏。

        Args:
            buf (bytearray): 要发送的数据字节。

        Notes:
            - 使用控制字节 `0x40` 表示写入数据。
            - 通过 `i2c.writevto()` 发送。

        ==========================================

        Send data buffer to SSD1306 display.

        Args:
            buf (bytearray): Data buffer to send.

        Notes:
            - Uses control byte `0x40` for data transfer.
            - Sent via `i2c.writevto()`.
        """

        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================