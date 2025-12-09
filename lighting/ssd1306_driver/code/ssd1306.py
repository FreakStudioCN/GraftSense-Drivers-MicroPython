# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : SSD1306.py
# @Description : 主要定义了SSD 1306类以及相关方法，代码参考自：https://github.com/stlehmann/micropython-ssd1306
# @License : MIT

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

# SSD1306 OLED屏幕类
class SSD1306(framebuf.FrameBuffer):
    """
    SSD1306 OLED屏幕类，用于控制和显示数据在OLED屏幕上。

    该类继承自 `framebuf.FrameBuffer` 类，能够通过I2C或SPI与OLED屏幕通信，
    并执行各种显示操作，包括初始化、开关显示、调整对比度、绘制图形等。

    Attributes:
        width (int): 屏幕的宽度（像素）。
        height (int): 屏幕的高度（像素）。
        external_vcc (bool): 是否使用外部电源。
        buffer (bytearray): 存储屏幕显示数据的缓冲区。
        pages (int): 屏幕的页数，通常为height // 8。

    Methods:
        __init__(width: int, height: int, external_vcc: bool) -> None:
            初始化OLED屏幕并配置显示参数。
        init_display() -> None:
            初始化显示设置。
        poweroff() -> None:
            关闭OLED显示。
        poweron() -> None:
            打开OLED显示。
        contrast(contrast: int) -> None:
            设置OLED屏幕对比度。
        invert(invert: bool) -> None:
            设置OLED显示反相或正常显示模式。
        show() -> None:
            将缓存中的数据更新到屏幕上。
        write_cmd(cmd: int) -> None:
            向OLED发送命令字节。
        write_data(buf: bytearray) -> None:
            向OLED发送数据字节。
    """

    def __init__(self, width: int, height: int, external_vcc: bool) -> None:
        """
        初始化OLED屏幕显示。

        Args:
            width (int): 屏幕宽度（像素）。
            height (int): 屏幕高度（像素）。
            external_vcc (bool): 是否使用外部电源。
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
        初始化OLED屏幕的显示设置。

        初始化屏幕时会发送一系列命令来设置显示模式、行数、对比度等显示参数。
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
        关闭OLED显示。

        将屏幕显示关闭以节省功耗。
        """

        self.write_cmd(SET_DISP | 0x00)

    def poweron(self) -> None:
        """
        打开OLED显示。

        重新激活OLED显示屏。
        """

        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast: int) -> None:
        """
        设置OLED屏幕的对比度。

        Args:
            contrast (int): 对比度值，范围0到255。
        """

        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert: bool) -> None:
        """
        设置OLED屏幕为正常或反相显示模式。

        Args:
            invert (bool): 如果为True，则显示模式为反相；否则为正常显示。
        """

        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self) -> None:
        """
        将缓冲区中的数据更新到屏幕上。

        将存储在缓存中的图形数据发送到OLED屏幕显示出来。
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
        向OLED屏幕发送命令。

        Args:
            cmd (int): 要发送的命令字节。
        """

        pass

    def write_data(self, buf: bytearray) -> None:
        """
        向OLED屏幕发送数据。

        Args:
            buf (bytearray): 要发送的数据字节。
        """

        pass

class SSD1306_I2C(SSD1306):
    """
    基于I2C接口的SSD1306 OLED屏幕类，继承自 `SSD1306` 类。

    使用I2C总线与SSD1306 OLED屏幕进行通信，提供显示控制和图形绘制功能。

    Attributes:
        i2c (I2C): 用于与屏幕通信的I2C对象。
        addr (int): OLED屏幕的I2C地址。

    Methods:
        __init__(i2c: I2C, addr: int, width: int, height: int, external_vcc: bool) -> None:
            初始化I2C接口并配置OLED屏幕。
        write_cmd(cmd: int) -> None:
            向OLED发送命令。
        write_data(buf: bytearray) -> None:
            向OLED发送数据。
    """

    def __init__(self, i2c: I2C, addr: int, width: int, height: int, external_vcc: bool) -> None:
        """
        初始化I2C接口和OLED屏幕。

        Args:
            i2c (I2C): 用于与屏幕通信的I2C对象。
            addr (int): OLED屏幕的I2C地址。
            width (int): 屏幕宽度（像素）。
            height (int): 屏幕高度（像素）。
            external_vcc (bool): 是否使用外部电源。
        """

        self.i2c = i2c
        self.addr = addr
        # 用于临时存储数据的字节数组
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd: int) -> None:
        """
        向OLED屏幕发送命令字节。

        Args:
            cmd (int): 要发送的命令字节。
        """

        # 0x80表示写入的数据是命令
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf: bytearray) -> None:
        """
        向OLED屏幕发送数据字节。

        Args:
            buf (bytearray): 要发送的数据字节。
        """

        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================