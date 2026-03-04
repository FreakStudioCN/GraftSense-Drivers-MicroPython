# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午6:00
# @Author  : mattytrentini
# @File    : sh1106.py
# @Description : SH1106 OLED显示屏驱动 支持I2C/SPI接口 实现旋转/翻转/图形绘制等功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "mattytrentini"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython"

# ======================================== 导入相关模块 =========================================
from micropython import const
import time
import framebuf

# ======================================== 全局变量 ============================================

# 设置对比度指令
_SET_CONTRAST = const(0x81)
# 设置显示正显/反显指令
_SET_NORM_INV = const(0xa6)
# 设置显示开关指令
_SET_DISP = const(0xae)
# 设置扫描方向指令
_SET_SCAN_DIR = const(0xc0)
# 设置段重映射指令
_SET_SEG_REMAP = const(0xa0)
# 低列地址设置指令
_LOW_COLUMN_ADDRESS = const(0x00)
# 高列地址设置指令
_HIGH_COLUMN_ADDRESS = const(0x10)
# 设置页地址指令
_SET_PAGE_ADDRESS = const(0xB0)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class SH1106(framebuf.FrameBuffer):
    """
    SH1106 OLED显示屏基础驱动类
    SH1106 OLED Display Base Driver Class

    基于framebuf.FrameBuffer实现SH1106 OLED显示屏的核心控制功能，支持90/180/270度旋转、
    屏幕翻转、对比度调节、图形绘制等功能，提供I2C/SPI接口的统一抽象层
    Implement core control functions of SH1106 OLED display based on framebuf.FrameBuffer, support 90/180/270 degree rotation,
    screen flip, contrast adjustment, graphics drawing and other functions, provide unified abstraction layer for I2C/SPI interface

    Attributes:
        width (int): 显示屏宽度(像素)
        height (int): 显示屏高度(像素)
        external_vcc (bool): 是否使用外部VCC供电
        flip_en (bool): 翻转使能标志，True-开启翻转
        rotate90 (bool): 90度旋转使能标志，True-开启90度旋转
        pages (int): 显示屏页数(高度/8)
        bufsize (int): 帧缓冲区大小(字节)
        renderbuf (bytearray): 渲染缓冲区，用于图形绘制
        displaybuf (bytearray): 显示缓冲区，用于最终输出
        pages_to_update (int): 需要更新的页掩码
        delay (int): 上电延时时间(ms)

    Methods:
        __init__(width, height, external_vcc, rotate=0): 初始化SH1106驱动
        write_cmd(*args, **kwargs): 发送指令（抽象方法）
        write_data(*args, **kwargs): 发送数据（抽象方法）
        init_display(): 初始化显示屏
        poweroff(): 关闭显示电源
        poweron(): 开启显示电源
        flip(flag=None, update=True): 翻转显示
        sleep(value): 设置休眠模式
        contrast(contrast): 设置显示对比度
        invert(invert): 设置显示反显
        show(full_update=False): 更新显示内容
        pixel(x, y, color=None): 绘制像素点
        text(text, x, y, color=1): 绘制文本
        line(x0, y0, x1, y1, color): 绘制直线
        hline(x, y, w, color): 绘制水平线
        vline(x, y, h, color): 绘制垂直线
        fill(color): 填充屏幕
        blit(fbuf, x, y, key=-1, palette=None): 绘制帧缓冲
        scroll(x, y): 滚动显示
        fill_rect(x, y, w, h, color): 填充矩形
        rect(x, y, w, h, color): 绘制矩形边框
        ellipse(x, y, xr, yr, color): 绘制椭圆
        register_updates(y0, y1=None): 注册需要更新的页
        reset(res=None): 重置显示屏
    """

    def __init__(self, width, height, external_vcc, rotate=0):
        """
        初始化SH1106驱动
        Initialize SH1106 driver

        Args:
            width (int): 显示屏宽度(像素)
            height (int): 显示屏高度(像素)
            external_vcc (bool): 是否使用外部VCC供电
            rotate (int, optional): 旋转角度(0/90/180/270)，默认0

        Returns:
            None

        Notes:
            根据旋转角度初始化缓冲区和帧缓冲对象，90/270度旋转使用MONO_HMSB格式，
            0/180度旋转使用MONO_VLSB格式，自动初始化显示参数
        """
        # 保存显示屏宽度
        self.width = width
        # 保存显示屏高度
        self.height = height
        # 保存外部VCC供电标志
        self.external_vcc = external_vcc
        # 设置翻转使能标志（180/270度旋转时开启）
        self.flip_en = rotate == 180 or rotate == 270
        # 设置90度旋转标志（90/270度旋转时开启）
        self.rotate90 = rotate == 90 or rotate == 270
        # 计算显示屏页数（每页8像素高度）
        self.pages = self.height // 8
        # 计算缓冲区大小
        self.bufsize = self.pages * self.width
        # 创建渲染缓冲区
        self.renderbuf = bytearray(self.bufsize)
        # 初始化需要更新的页掩码
        self.pages_to_update = 0
        # 初始化上电延时
        self.delay = 0

        # 90/270度旋转处理
        if self.rotate90:
            # 创建独立的显示缓冲区
            self.displaybuf = bytearray(self.bufsize)
            # 初始化帧缓冲（高度和宽度交换，使用MONO_HMSB格式）
            super().__init__(self.renderbuf, self.height, self.width,
                             framebuf.MONO_HMSB)
        else:
            # 显示缓冲区复用渲染缓冲区
            self.displaybuf = self.renderbuf
            # 初始化帧缓冲（使用MONO_VLSB格式）
            super().__init__(self.renderbuf, self.width, self.height,
                             framebuf.MONO_VLSB)

        # 绑定翻转方法到rotate属性
        self.rotate = self.flip
        # 初始化显示屏
        self.init_display()

    def write_cmd(self, *args, **kwargs):
        """
        发送指令（抽象方法）
        Send command (abstract method)

        Args:
            *args: 指令参数
            **kwargs: 关键字参数

        Returns:
            None

        Raises:
            NotImplementedError: 未实现异常

        Notes:
            由子类(SH1106_I2C/SH1106_SPI)实现具体的指令发送逻辑
        """
        raise NotImplementedError

    def write_data(self, *args, **kwargs):
        """
        发送数据（抽象方法）
        Send data (abstract method)

        Args:
            *args: 数据参数
            **kwargs: 关键字参数

        Returns:
            None

        Raises:
            NotImplementedError: 未实现异常

        Notes:
            由子类(SH1106_I2C/SH1106_SPI)实现具体的数据发送逻辑
        """
        raise NotImplementedError

    def init_display(self):
        """
        初始化显示屏
        Initialize display

        Args:
            None

        Returns:
            None

        Notes:
            执行重置、清屏、显示更新、上电、翻转设置等初始化操作
        """
        # 重置显示屏
        self.reset()
        # 清屏
        self.fill(0)
        # 更新显示
        self.show()
        # 开启电源
        self.poweron()

        # 设置翻转状态
        self.flip(self.flip_en)

    def poweroff(self):
        """
        关闭显示电源
        Power off display

        Args:
            None

        Returns:
            None

        Notes:
            发送关闭显示指令，显示屏进入低功耗状态
        """
        self.write_cmd(_SET_DISP | 0x00)

    def poweron(self):
        """
        开启显示电源
        Power on display

        Args:
            None

        Returns:
            None

        Notes:
            发送开启显示指令，如有设置延时则等待指定时间
        """
        self.write_cmd(_SET_DISP | 0x01)
        # 上电延时
        if self.delay:
            time.sleep_ms(self.delay)

    def flip(self, flag=None, update=True):
        """
        翻转显示
        Flip display

        Args:
            flag (bool, optional): 翻转标志，None则切换当前状态
            update (bool, optional): 是否立即更新显示，默认True

        Returns:
            None

        Notes:
            根据翻转标志设置垂直/水平镜像，更新段重映射和扫描方向指令
        """
        # 切换翻转状态（如果未指定）
        if flag is None:
            flag = not self.flip_en
        # 计算垂直镜像标志
        mir_v = flag ^ self.rotate90
        # 计算水平镜像标志
        mir_h = flag
        # 设置段重映射
        self.write_cmd(_SET_SEG_REMAP | (0x01 if mir_v else 0x00))
        # 设置扫描方向
        self.write_cmd(_SET_SCAN_DIR | (0x08 if mir_h else 0x00))
        # 更新翻转使能标志
        self.flip_en = flag
        # 立即更新显示
        if update:
            self.show(True)

    def sleep(self, value):
        """
        设置休眠模式
        Set sleep mode

        Args:
            value (bool): 休眠标志，True-休眠，False-唤醒

        Returns:
            None

        Notes:
            value=True时关闭显示，value=False时开启显示
        """
        self.write_cmd(_SET_DISP | (not value))

    def contrast(self, contrast):
        """
        设置显示对比度
        Set display contrast

        Args:
            contrast (int): 对比度值(0-255)

        Returns:
            None

        Notes:
            发送对比度设置指令和具体数值，数值越大对比度越高
        """
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        """
        设置显示反显
        Set display inversion

        Args:
            invert (bool): 反显标志，True-反显，False-正显

        Returns:
            None

        Notes:
            反显模式下像素颜色反转（黑变白，白变黑）
        """
        self.write_cmd(_SET_NORM_INV | (invert & 1))

    def show(self, full_update=False):
        """
        更新显示内容
        Update display content

        Args:
            full_update (bool, optional): 是否全量更新，默认False

        Returns:
            None

        Notes:
            全量更新时刷新所有页，增量更新时仅刷新有变化的页，90/270度旋转时需要转换缓冲区数据
        """
        # 解包显示参数
        (w, p, db, rb) = (self.width, self.pages,
                          self.displaybuf, self.renderbuf)
        # 90/270度旋转数据转换
        if self.rotate90:
            for i in range(self.bufsize):
                db[w * (i % p) + (i // p)] = rb[i]
        # 确定需要更新的页
        if full_update:
            pages_to_update = (1 << self.pages) - 1
        else:
            pages_to_update = self.pages_to_update

        # 逐页更新显示
        for page in range(self.pages):
            if (pages_to_update & (1 << page)):
                # 设置页地址
                self.write_cmd(_SET_PAGE_ADDRESS | page)
                # 设置列地址（低字节）
                self.write_cmd(_LOW_COLUMN_ADDRESS | 2)
                # 设置列地址（高字节）
                self.write_cmd(_HIGH_COLUMN_ADDRESS | 0)
                # 发送页数据
                self.write_data(db[(w * page):(w * page + w)])
        # 重置更新页掩码
        self.pages_to_update = 0

    def pixel(self, x, y, color=None):
        """
        绘制像素点
        Draw pixel

        Args:
            x (int): X坐标
            y (int): Y坐标
            color (int, optional): 颜色值(0-1)，None则读取当前颜色

        Returns:
            int: 当color=None时返回当前像素颜色值

        Notes:
            绘制像素后自动标记对应页为需要更新
        """
        if color is None:
            return super().pixel(x, y)
        else:
            # 绘制像素点
            super().pixel(x, y, color)
            # 计算像素所在页
            page = y // 8
            # 标记该页需要更新
            self.pages_to_update |= 1 << page

    def text(self, text, x, y, color=1):
        """
        绘制文本
        Draw text

        Args:
            text (str): 要显示的文本
            x (int): X坐标
            y (int): Y坐标
            color (int, optional): 颜色值(0-1)，默认1

        Returns:
            None

        Notes:
            绘制文本后注册y到y+7的更新区域
        """
        super().text(text, x, y, color)
        # 注册需要更新的页
        self.register_updates(y, y + 7)

    def line(self, x0, y0, x1, y1, color):
        """
        绘制直线
        Draw line

        Args:
            x0 (int): 起点X坐标
            y0 (int): 起点Y坐标
            x1 (int): 终点X坐标
            y1 (int): 终点Y坐标
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            绘制直线后注册y0到y1的更新区域
        """
        super().line(x0, y0, x1, y1, color)
        # 注册需要更新的页
        self.register_updates(y0, y1)

    def hline(self, x, y, w, color):
        """
        绘制水平线
        Draw horizontal line

        Args:
            x (int): X坐标
            y (int): Y坐标
            w (int): 线宽度
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            绘制水平线后注册y坐标对应的更新区域
        """
        super().hline(x, y, w, color)
        # 注册需要更新的页
        self.register_updates(y)

    def vline(self, x, y, h, color):
        """
        绘制垂直线
        Draw vertical line

        Args:
            x (int): X坐标
            y (int): Y坐标
            h (int): 线高度
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            绘制垂直线后注册y到y+h-1的更新区域
        """
        super().vline(x, y, h, color)
        # 注册需要更新的页
        self.register_updates(y, y + h - 1)

    def fill(self, color):
        """
        填充屏幕
        Fill screen

        Args:
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            填充后标记所有页为需要更新
        """
        super().fill(color)
        # 标记所有页需要更新
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x, y, key=-1, palette=None):
        """
        绘制帧缓冲
        Draw frame buffer

        Args:
            fbuf (framebuf.FrameBuffer): 源帧缓冲
            x (int): X坐标
            y (int): Y坐标
            key (int, optional): 透明色值，默认-1
            palette (optional): 调色板，默认None

        Returns:
            None

        Notes:
            绘制帧缓冲后注册y到y+height的更新区域
        """
        super().blit(fbuf, x, y, key, palette)
        # 注册需要更新的页
        self.register_updates(y, y + self.height)

    def scroll(self, x, y):
        """
        滚动显示
        Scroll display

        Args:
            x (int): X方向偏移
            y (int): Y方向偏移

        Returns:
            None

        Notes:
            滚动后标记所有页为需要更新
        """
        super().scroll(x, y)
        # 标记所有页需要更新
        self.pages_to_update = (1 << self.pages) - 1

    def fill_rect(self, x, y, w, h, color):
        """
        填充矩形
        Fill rectangle

        Args:
            x (int): X坐标
            y (int): Y坐标
            w (int): 矩形宽度
            h (int): 矩形高度
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            填充矩形后注册y到y+h-1的更新区域
        """
        super().fill_rect(x, y, w, h, color)
        # 注册需要更新的页
        self.register_updates(y, y + h - 1)

    def rect(self, x, y, w, h, color):
        """
        绘制矩形边框
        Draw rectangle border

        Args:
            x (int): X坐标
            y (int): Y坐标
            w (int): 矩形宽度
            h (int): 矩形高度
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            绘制矩形边框后注册y到y+h-1的更新区域
        """
        super().rect(x, y, w, h, color)
        # 注册需要更新的页
        self.register_updates(y, y + h - 1)

    def ellipse(self, x, y, xr, yr, color):
        """
        绘制椭圆
        Draw ellipse

        Args:
            x (int): 中心X坐标
            y (int): 中心Y坐标
            xr (int): X轴半径
            yr (int): Y轴半径
            color (int): 颜色值(0-1)

        Returns:
            None

        Notes:
            绘制椭圆后注册y-yr到y+yr-1的更新区域
        """
        super().ellipse(x, y, xr, yr, color)
        # 注册需要更新的页
        self.register_updates(y - yr, y + yr - 1)

    def register_updates(self, y0, y1=None):
        """
        注册需要更新的页
        Register pages to update

        Args:
            y0 (int): 起始Y坐标
            y1 (int, optional): 结束Y坐标，默认None

        Returns:
            None

        Notes:
            根据Y坐标范围计算需要更新的页，并设置对应的掩码位
        """
        # 计算起始页
        start_page = max(0, y0 // 8)
        # 计算结束页
        end_page = max(0, y1 // 8) if y1 is not None else start_page

        # 确保起始页小于等于结束页
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        # 标记需要更新的页
        for page in range(start_page, end_page + 1):
            self.pages_to_update |= 1 << page

    def reset(self, res=None):
        """
        重置显示屏
        Reset display

        Args:
            res (machine.Pin, optional): 复位引脚，默认None

        Returns:
            None

        Notes:
            通过复位引脚执行硬件复位：高电平->低电平(20ms)->高电平(20ms)
        """
        if res is not None:
            # 复位引脚置高
            res(1)
            time.sleep_ms(1)
            # 复位引脚置低
            res(0)
            time.sleep_ms(20)
            # 复位引脚置高
            res(1)
            time.sleep_ms(20)


class SH1106_I2C(SH1106):
    """
    I2C接口SH1106 OLED显示屏驱动类
    I2C Interface SH1106 OLED Display Driver Class

    继承SH1106基础类，实现基于I2C通信协议的指令和数据发送方法
    Inherit SH1106 base class, implement command and data sending methods based on I2C communication protocol

    Attributes:
        i2c (machine.I2C): I2C通信对象
        addr (int): I2C设备地址，默认0x3c
        res (machine.Pin): 复位引脚
        temp (bytearray): 2字节临时缓冲区，用于指令发送

    Methods:
        __init__(width, height, i2c, res=None, addr=0x3c, rotate=0, external_vcc=False, delay=0): 初始化I2C接口SH1106
        write_cmd(cmd): 发送指令
        write_data(buf): 发送数据
        reset(res=None): 重置显示屏
    """

    def __init__(self, width, height, i2c, res=None, addr=0x3c,
                 rotate=0, external_vcc=False, delay=0):
        """
        初始化I2C接口SH1106
        Initialize I2C interface SH1106

        Args:
            width (int): 显示屏宽度
            height (int): 显示屏高度
            i2c (machine.I2C): I2C通信对象
            res (machine.Pin, optional): 复位引脚，默认None
            addr (int, optional): I2C地址，默认0x3c
            rotate (int, optional): 旋转角度，默认0
            external_vcc (bool, optional): 外部VCC供电，默认False
            delay (int, optional): 上电延时，默认0

        Returns:
            None
        """
        # 保存I2C通信对象
        self.i2c = i2c
        # 保存I2C设备地址
        self.addr = addr
        # 保存复位引脚
        self.res = res
        # 初始化2字节指令缓冲区
        self.temp = bytearray(2)
        # 保存上电延时
        self.delay = delay
        # 配置复位引脚
        if res is not None:
            res.init(res.OUT, value=1)
        # 调用父类初始化
        super().__init__(width, height, external_vcc, rotate)

    def write_cmd(self, cmd):
        """
        发送指令
        Send command

        Args:
            cmd (int): 指令字节(0-255)

        Returns:
            None

        Notes:
            I2C指令格式：0x80 + 指令字节
        """
        # 设置指令标志位
        self.temp[0] = 0x80
        # 设置指令数据
        self.temp[1] = cmd
        # 通过I2C发送指令
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        """
        发送数据
        Send data

        Args:
            buf (bytes/bytearray): 数据缓冲区

        Returns:
            None

        Notes:
            I2C数据格式：0x40 + 数据字节流
        """
        self.i2c.writeto(self.addr, b'\x40' + buf)

    def reset(self, res=None):
        """
        重置显示屏
        Reset display

        Args:
            res (machine.Pin, optional): 复位引脚，默认None

        Returns:
            None

        Notes:
            调用父类reset方法，使用自身的res引脚
        """
        super().reset(self.res)


class SH1106_SPI(SH1106):
    """
    SPI接口SH1106 OLED显示屏驱动类
    SPI Interface SH1106 OLED Display Driver Class

    继承SH1106基础类，实现基于SPI通信协议的指令和数据发送方法
    Inherit SH1106 base class, implement command and data sending methods based on SPI communication protocol

    Attributes:
        spi (machine.SPI): SPI通信对象
        dc (machine.Pin): 数据/指令引脚
        res (machine.Pin): 复位引脚
        cs (machine.Pin): 片选引脚

    Methods:
        __init__(width, height, spi, dc, res=None, cs=None, rotate=0, external_vcc=False, delay=0): 初始化SPI接口SH1106
        write_cmd(cmd): 发送指令
        write_data(buf): 发送数据
        reset(res=None): 重置显示屏
    """

    def __init__(self, width, height, spi, dc, res=None, cs=None,
                 rotate=0, external_vcc=False, delay=0):
        """
        初始化SPI接口SH1106
        Initialize SPI interface SH1106

        Args:
            width (int): 显示屏宽度
            height (int): 显示屏高度
            spi (machine.SPI): SPI通信对象
            dc (machine.Pin): 数据/指令引脚
            res (machine.Pin, optional): 复位引脚，默认None
            cs (machine.Pin, optional): 片选引脚，默认None
            rotate (int, optional): 旋转角度，默认0
            external_vcc (bool, optional): 外部VCC供电，默认False
            delay (int, optional): 上电延时，默认0

        Returns:
            None
        """
        # 配置数据/指令引脚
        dc.init(dc.OUT, value=0)
        # 配置复位引脚
        if res is not None:
            res.init(res.OUT, value=0)
        # 配置片选引脚
        if cs is not None:
            cs.init(cs.OUT, value=1)
        # 保存SPI通信对象
        self.spi = spi
        # 保存数据/指令引脚
        self.dc = dc
        # 保存复位引脚
        self.res = res
        # 保存片选引脚
        self.cs = cs
        # 保存上电延时
        self.delay = delay
        # 调用父类初始化
        super().__init__(width, height, external_vcc, rotate)

    def write_cmd(self, cmd):
        """
        发送指令
        Send command

        Args:
            cmd (int): 指令字节(0-255)

        Returns:
            None

        Notes:
            SPI指令发送：DC引脚置低，可选CS引脚控制片选
        """
        if self.cs is not None:
            # 片选置高
            self.cs(1)
            # DC引脚置低（指令模式）
            self.dc(0)
            # 片选置低
            self.cs(0)
            # 发送指令
            self.spi.write(bytearray([cmd]))
            # 片选置高
            self.cs(1)
        else:
            # DC引脚置低（指令模式）
            self.dc(0)
            # 发送指令
            self.spi.write(bytearray([cmd]))

    def write_data(self, buf):
        """
        发送数据
        Send data

        Args:
            buf (bytes/bytearray): 数据缓冲区

        Returns:
            None

        Notes:
            SPI数据发送：DC引脚置高，可选CS引脚控制片选
        """
        if self.cs is not None:
            # 片选置高
            self.cs(1)
            # DC引脚置高（数据模式）
            self.dc(1)
            # 片选置低
            self.cs(0)
            # 发送数据
            self.spi.write(buf)
            # 片选置高
            self.cs(1)
        else:
            # DC引脚置高（数据模式）
            self.dc(1)
            # 发送数据
            self.spi.write(buf)

    def reset(self, res=None):
        """
        重置显示屏
        Reset display

        Args:
            res (machine.Pin, optional): 复位引脚，默认None

        Returns:
            None

        Notes:
            调用父类reset方法，使用自身的res引脚
        """
        super().reset(self.res)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================