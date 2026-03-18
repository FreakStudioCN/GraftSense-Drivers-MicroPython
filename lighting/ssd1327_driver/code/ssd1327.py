# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午4:52
# @Author  : mcauser
# @File    : ssd1327.py
# @Description : SSD1327 OLED显示屏I2C驱动 适用于MicroPython，实现OLED屏幕初始化、显示控制、灰度调节、旋转反转等功能 参考自:https://github.com/mcauser/micropython-ssd1327
# @License : MIT
__version__ = "0.1.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from micropython import const
import framebuf
import machine  # 导入machine模块用于I2C类型注解

# ======================================== 全局变量 ============================================

# 设置列地址命令
SET_COL_ADDR: int = const(0x15)
# 关闭滚动命令
SET_SCROLL_DEACTIVATE: int = const(0x2E)
# 设置行地址命令
SET_ROW_ADDR: int = const(0x75)
# 设置对比度命令
SET_CONTRAST: int = const(0x81)
# 设置段重映射命令
SET_SEG_REMAP: int = const(0xA0)
# 设置显示起始行命令
SET_DISP_START_LINE: int = const(0xA1)
# 设置显示偏移命令
SET_DISP_OFFSET: int = const(0xA2)
# 设置显示模式命令（0xA4正常, 0xA5全亮, 0xA6全灭, 0xA7反转）
SET_DISP_MODE: int = const(0xA4)
# 设置多路复用率命令
SET_MUX_RATIO: int = const(0xA8)
# 功能选择A命令
SET_FN_SELECT_A: int = const(0xAB)
# 设置显示开关命令（0xAE关闭, 0xAF开启）
SET_DISP: int = const(0xAE)
# 设置相位长度命令
SET_PHASE_LEN: int = const(0xB1)
# 设置显示时钟分频命令
SET_DISP_CLK_DIV: int = const(0xB3)
# 设置第二预充电周期命令
SET_SECOND_PRECHARGE: int = const(0xB6)
# 设置灰度表命令
SET_GRAYSCALE_TABLE: int = const(0xB8)
# 设置线性灰度模式命令
SET_GRAYSCALE_LINEAR: int = const(0xB9)
# 设置预充电电压命令
SET_PRECHARGE: int = const(0xBC)
# 设置VCOM解选电压命令
SET_VCOM_DESEL: int = const(0xBE)
# 功能选择B命令
SET_FN_SELECT_B: int = const(0xD5)
# 设置命令锁命令
SET_COMMAND_LOCK: int = const(0xFD)

# 命令寄存器标识
REG_CMD: int = const(0x80)
# 数据寄存器标识
REG_DATA: int = const(0x40)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class SSD1327:
    """
    SSD1327 OLED显示屏基础驱动类
    Attributes:
        width (int): OLED屏幕宽度，默认128
        height (int): OLED屏幕高度，默认128
        buffer (bytearray): 屏幕显示缓冲区，存储4位灰度图像数据
        framebuf (framebuf.FrameBuffer): 帧缓冲对象，用于绘图操作
        col_addr (tuple[int, int]): 列地址范围，适配不同尺寸屏幕
        row_addr (tuple[int, int]): 行地址范围，适配不同尺寸屏幕
        offset (int): 显示偏移量，适配不同尺寸屏幕

    Methods:
        __init__(width=128, height=128): 初始化驱动类，创建缓冲区和帧缓冲对象
        init_display(): 初始化OLED显示屏，发送配置命令
        poweroff(): 关闭OLED电源，进入低功耗状态
        poweron(): 打开OLED电源，恢复显示
        contrast(contrast): 设置屏幕对比度
        rotate(rotate): 旋转屏幕显示方向
        invert(invert): 反转屏幕显示颜色
        show(): 更新屏幕显示，写入缓冲区数据
        fill(col): 填充整个屏幕为指定灰度值
        pixel(x, y, col): 在指定坐标绘制像素点
        line(x1, y1, x2, y2, col): 绘制直线
        scroll(dx, dy): 滚动屏幕显示内容（软件滚动）
        text(string, x, y, col=15): 显示文本字符串
        write_cmd(cmd): 发送命令的抽象方法，子类需实现
        write_data(data_buf): 发送数据的抽象方法，子类需实现

    Notes:
        基础驱动类定义了SSD1327的核心功能接口，需通过I2C/SPI子类实现具体通信逻辑

    ==========================================

    SSD1327 OLED display basic driver class
    Attributes:
        width (int): OLED screen width, default 128
        height (int): OLED screen height, default 128
        buffer (bytearray): Screen display buffer, stores 4-bit grayscale image data
        framebuf (framebuf.FrameBuffer): Frame buffer object for drawing operations
        col_addr (tuple[int, int]): Column address range, adapted to different screen sizes
        row_addr (tuple[int, int]): Row address range, adapted to different screen sizes
        offset (int): Display offset, adapted to different screen sizes

    Methods:
        __init__(width=128, height=128): Initialize driver class, create buffer and frame buffer object
        init_display(): Initialize OLED display, send configuration commands
        poweroff(): Turn off OLED power, enter low power state
        poweron(): Turn on OLED power, resume display
        contrast(contrast): Set screen contrast
        rotate(rotate): Rotate screen display direction
        invert(invert): Invert screen display color
        show(): Update screen display, write buffer data
        fill(col): Fill the entire screen with specified grayscale value
        pixel(x, y, col): Draw pixel at specified coordinates
        line(x1, y1, x2, y2, col): Draw line
        scroll(dx, dy): Scroll screen display content (software scroll)
        text(string, x, y, col=15): Display text string
        write_cmd(cmd): Abstract method for sending commands, need to be implemented in subclass
        write_data(data_buf): Abstract method for sending data, need to be implemented in subclass

    Notes:
        The basic driver class defines the core functional interfaces of SSD1327, and the specific communication logic needs to be implemented through I2C/SPI subclasses
    """

    def __init__(self, width: int = 128, height: int = 128) -> None:
        """
        初始化SSD1327驱动类
        Args:
            width (int, optional): OLED屏幕宽度，默认128
            height (int, optional): OLED屏幕高度，默认128

        Raises:
            无

        Notes:
            创建4位灰度显示缓冲区（每个字节存储2个像素），初始化帧缓冲对象，配置地址和偏移参数

        ==========================================

        Initialize SSD1327 driver class
        Args:
            width (int, optional): OLED screen width, default 128
            height (int, optional): OLED screen height, default 128

        Raises:
            None

        Notes:
            Create 4-bit grayscale display buffer (2 pixels per byte), initialize frame buffer object, configure address and offset parameters
        """
        self.width: int = width
        self.height: int = height
        # 创建显示缓冲区，4位灰度模式下缓冲区大小为宽度*高度//2
        self.buffer: bytearray = bytearray(self.width * self.height // 2)
        # 创建帧缓冲对象，使用GS4_HMSB 4位灰度高位优先格式
        self.framebuf: framebuf.FrameBuffer = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.GS4_HMSB)

        # 计算列地址范围，适配不同宽度屏幕
        self.col_addr: tuple[int, int] = ((128 - self.width) // 4, 63 - ((128 - self.width) // 4))
        # 96x96     (8, 55)
        # 128x128   (0, 63)

        # 初始化行地址范围
        self.row_addr: tuple[int, int] = (0, self.height - 1)
        # 96x96     (0, 95)
        # 128x128   (0, 127)

        # 计算显示偏移量，适配不同高度屏幕
        self.offset: int = 128 - self.height
        # 96x96     32
        # 128x128   0

        # 打开屏幕电源
        self.poweron()
        # 初始化显示屏配置
        self.init_display()

    def init_display(self) -> None:
        """
        初始化OLED显示屏，发送配置命令
        Args:
            无

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            依次发送解锁、显示关闭、分辨率配置、时序配置、显示参数等命令，最后清空屏幕

        ==========================================

        Initialize OLED display, send configuration commands
        Args:
            None

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            Send unlock, display off, resolution configuration, timing configuration, display parameter commands in sequence, finally clear screen
        """
        for cmd in (
            SET_COMMAND_LOCK,
            0x12,  # 解锁命令（0x12为解锁参数）
            SET_DISP,  # 关闭显示
            # 分辨率和布局配置
            SET_DISP_START_LINE,
            0x00,  # 设置显示起始行为0
            SET_DISP_OFFSET,
            self.offset,  # 设置垂直偏移量（0~127）
            # 设置段重映射参数
            SET_SEG_REMAP,
            0x51,
            SET_MUX_RATIO,
            self.height - 1,  # 设置多路复用率
            # 时序和驱动方案配置
            SET_FN_SELECT_A,
            0x01,  # 启用内部VDD稳压器
            SET_PHASE_LEN,
            0x51,  # 相位1:1个DCLK，相位2:5个DCLKs
            SET_DISP_CLK_DIV,
            0x01,  # 分频比1，振荡器频率0
            SET_PRECHARGE,
            0x08,  # 设置预充电电压等级为VCOMH
            SET_VCOM_DESEL,
            0x07,  # 设置VCOMH COM deselect voltage level: 0.86*Vcc
            SET_SECOND_PRECHARGE,
            0x01,  # 第二预充电周期1个DCLK
            SET_FN_SELECT_B,
            0x62,  # 启用enternal VSL，Enable second precharge
            # 显示配置
            SET_GRAYSCALE_LINEAR,  # 使用线性灰度查找表
            SET_CONTRAST,
            0x7F,  # 设置中等对比度（0x7f）
            SET_DISP_MODE,  # 设置正常显示模式
            SET_COL_ADDR,
            self.col_addr[0],
            self.col_addr[1],  # 设置列地址范围
            SET_ROW_ADDR,
            self.row_addr[0],
            self.row_addr[1],  # 设置行地址范围
            SET_SCROLL_DEACTIVATE,  # 关闭滚动功能
            SET_DISP | 0x01,
        ):  # 打开显示（0xAF）
            self.write_cmd(cmd)
        # 清空屏幕缓冲区
        self.fill(0)
        # 将空缓冲区写入屏幕
        self.write_data(self.buffer)

    def poweroff(self) -> None:
        """
        关闭OLED电源，进入低功耗状态
        Args:
            无

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            禁用内部VDD稳压器并关闭显示，降低功耗

        ==========================================

        Turn off OLED power, enter low power state
        Args:
            None

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            Disable internal VDD regulator and turn off display to reduce power consumption
        """
        self.write_cmd(SET_FN_SELECT_A)
        self.write_cmd(0x00)  # 禁用内部VDD稳压器，节省功耗
        self.write_cmd(SET_DISP)  # 关闭显示

    def poweron(self) -> None:
        """
        打开OLED电源，恢复显示
        Args:
            无

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            启用内部VDD稳压器并打开显示

        ==========================================

        Turn on OLED power, resume display
        Args:
            None

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            Enable internal VDD regulator and turn on display
        """
        self.write_cmd(SET_FN_SELECT_A)
        self.write_cmd(0x01)  # 启用内部VDD稳压器
        self.write_cmd(SET_DISP | 0x01)  # 打开显示

    def contrast(self, contrast: int) -> None:
        """
        设置OLED屏幕对比度
        Args:
            contrast (int): 对比度值，范围0~255

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            对比度值越大显示越亮，0为最低，255为最高

        ==========================================

        Set OLED screen contrast
        Args:
            contrast (int): Contrast value, range 0~255

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            The larger the contrast value, the brighter the display, 0 is the lowest, 255 is the highest
        """
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)  # 0-255

    def rotate(self, rotate: bool) -> None:
        """
        旋转屏幕显示方向
        Args:
            rotate (bool): True为旋转显示，False为正常显示

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            旋转前关闭电源，修改偏移和重映射参数后重新开机

        ==========================================

        Rotate screen display direction
        Args:
            rotate (bool): True for rotated display, False for normal display

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            Turn off power before rotation, modify offset and remap parameters then power on again
        """
        self.poweroff()
        self.write_cmd(SET_DISP_OFFSET)
        self.write_cmd(self.height if rotate else self.offset)  # 根据旋转状态设置偏移量
        self.write_cmd(SET_SEG_REMAP)
        self.write_cmd(0x42 if rotate else 0x51)  # 根据旋转状态设置段重映射参数
        self.poweron()

    def invert(self, invert: bool) -> None:
        """
        反转屏幕显示颜色
        Args:
            invert (bool): True为反转显示，False为正常显示

        Raises:
            NotImplementedError: 若子类未实现write_cmd方法则抛出

        Notes:
            正常显示：灰度0为黑，15为白；反转显示：灰度0为白，15为黑

        ==========================================

        Invert screen display color
        Args:
            invert (bool): True for inverted display, False for normal display

        Raises:
            NotImplementedError: Thrown if write_cmd method is not implemented by subclass

        Notes:
            Normal display: grayscale 0 is black, 15 is white; Inverted display: grayscale 0 is white, 15 is black
        """
        self.write_cmd(SET_DISP_MODE | (invert & 1) << 1 | (invert & 1))  # 0xA4=Normal, 0xA7=Inverted

    def show(self) -> None:
        """
        更新屏幕显示，写入缓冲区数据
        Args:
            无

        Raises:
            NotImplementedError: 若子类未实现write_cmd/write_data方法则抛出

        Notes:
            先设置行列地址范围，再发送缓冲区数据到屏幕

        ==========================================

        Update screen display, write buffer data
        Args:
            None

        Raises:
            NotImplementedError: Thrown if write_cmd/write_data method is not implemented by subclass

        Notes:
            Set column and row address range first, then send buffer data to screen
        """
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(self.col_addr[0])
        self.write_cmd(self.col_addr[1])
        self.write_cmd(SET_ROW_ADDR)
        self.write_cmd(self.row_addr[0])
        self.write_cmd(self.row_addr[1])
        self.write_data(self.buffer)

    def fill(self, col: int) -> None:
        """
        填充整个屏幕为指定灰度值
        Args:
            col (int): 灰度值，范围0~15（4位灰度）

        Raises:
            无

        Notes:
            调用帧缓冲对象的fill方法填充缓冲区

        ==========================================

        Fill the entire screen with specified grayscale value
        Args:
            col (int): Grayscale value, range 0~15 (4-bit grayscale)

        Raises:
            None

        Notes:
            Call fill method of frame buffer object to fill buffer
        """
        self.framebuf.fill(col)

    def pixel(self, x: int, y: int, col: int) -> None:
        """
        在指定坐标绘制像素点
        Args:
            x (int): 像素点X坐标
            y (int): 像素点Y坐标
            col (int): 灰度值，范围0~15（4位灰度）

        Raises:
            无

        Notes:
            调用帧缓冲对象的pixel方法绘制单个像素

        ==========================================

        Draw pixel at specified coordinates
        Args:
            x (int): Pixel X coordinate
            y (int): Pixel Y coordinate
            col (int): Grayscale value, range 0~15 (4-bit grayscale)

        Raises:
            None

        Notes:
            Call pixel method of frame buffer object to draw single pixel
        """
        self.framebuf.pixel(x, y, col)

    def line(self, x1: int, y1: int, x2: int, y2: int, col: int) -> None:
        """
        绘制直线
        Args:
            x1 (int): 直线起点X坐标
            y1 (int): 直线起点Y坐标
            x2 (int): 直线终点X坐标
            y2 (int): 直线终点Y坐标
            col (int): 灰度值，范围0~15（4位灰度）

        Raises:
            无

        Notes:
            调用帧缓冲对象的line方法绘制直线

        ==========================================

        Draw line
        Args:
            x1 (int): Line start X coordinate
            y1 (int): Line start Y coordinate
            x2 (int): Line end X coordinate
            y2 (int): Line end Y coordinate
            col (int): Grayscale value, range 0~15 (4-bit grayscale)

        Raises:
            None

        Notes:
            Call line method of frame buffer object to draw line
        """
        self.framebuf.line(x1, y1, x2, y2, col)

    def scroll(self, dx: int, dy: int) -> None:
        """
        滚动屏幕显示内容（软件滚动）
        Args:
            dx (int): X轴滚动偏移量（正数向右，负数向左）
            dy (int): Y轴滚动偏移量（正数向下，负数向上）

        Raises:
            无

        Notes:
            调用帧缓冲对象的scroll方法实现软件滚动，需调用show更新显示

        ==========================================

        Scroll screen display content (software scroll)
        Args:
            dx (int): X-axis scroll offset (positive to right, negative to left)
            dy (int): Y-axis scroll offset (positive to down, negative to up)

        Raises:
            None

        Notes:
            Call scroll method of frame buffer object to implement software scroll, need to call show to update display
        """
        self.framebuf.scroll(dx, dy)
        # software scroll

    def text(self, string: str, x: int, y: int, col: int = 15) -> None:
        """
        显示文本字符串
        Args:
            string (str): 要显示的文本字符串（仅ASCII）
            x (int): 文本起始X坐标
            y (int): 文本起始Y坐标
            col (int, optional): 灰度值，默认15（最亮），范围0~15

        Raises:
            无

        Notes:
            调用帧缓冲对象的text方法显示文本，仅支持ASCII字符

        ==========================================

        Display text string
        Args:
            string (str): Text string to display (ASCII only)
            x (int): Text start X coordinate
            y (int): Text start Y coordinate
            col (int, optional): Grayscale value, default 15 (brightest), range 0~15

        Raises:
            None

        Notes:
            Call text method of frame buffer object to display text, only supports ASCII characters
        """
        self.framebuf.text(string, x, y, col)

    def write_cmd(self, cmd: int) -> None:
        """
        发送命令的抽象方法（子类需实现）
        Args:
            cmd (int): 要发送的命令字节

        Raises:
            NotImplementedError: 调用该抽象方法时抛出

        Notes:
            基础类中未实现，需在I2C/SPI子类中重写

        ==========================================

        Abstract method for sending commands (need to be implemented in subclass)
        Args:
            cmd (int): Command byte to send

        Raises:
            NotImplementedError: Thrown when calling this abstract method

        Notes:
            Not implemented in base class, need to be overridden in I2C/SPI subclasses
        """
        raise NotImplementedError

    def write_data(self, data_buf: bytearray) -> None:
        """
        发送数据的抽象方法（子类需实现）
        Args:
            data_buf (bytearray): 要发送的显示缓冲区数据

        Raises:
            NotImplementedError: 调用该抽象方法时抛出

        Notes:
            基础类中未实现，需在I2C/SPI子类中重写

        ==========================================

        Abstract method for sending data (need to be implemented in subclass)
        Args:
            data_buf (bytearray): Display buffer data to send

        Raises:
            NotImplementedError: Thrown when calling this abstract method

        Notes:
            Not implemented in base class, need to be overridden in I2C/SPI subclasses
        """
        raise NotImplementedError


class SSD1327_I2C(SSD1327):
    """
    SSD1327 OLED显示屏I2C通信驱动子类
    Attributes:
        i2c (machine.I2C): I2C通信对象（已初始化）
        addr (int): OLED屏幕I2C地址，默认0x3c
        cmd_arr (bytearray): 命令发送缓冲区
        data_list (list[bytes | bytearray | None]): 数据发送列表，用于批量传输

    Methods:
        __init__(width, height, i2c, addr=0x3c): 初始化I2C驱动子类
        write_cmd(cmd): 通过I2C发送命令
        write_data(data_buf): 通过I2C发送数据缓冲区

    Notes:
        实现I2C通信协议的SSD1327驱动，适配标准I2C接口的OLED屏幕

    ==========================================

    SSD1327 OLED display I2C communication driver subclass
    Attributes:
        i2c (machine.I2C): I2C communication object (initialized)
        addr (int): OLED screen I2C address, default 0x3c
        cmd_arr (bytearray): Command transmission buffer
        data_list (list[bytes | bytearray | None]): Data transmission list for batch transfer

    Methods:
        __init__(width, height, i2c, addr=0x3c): Initialize I2C driver subclass
        write_cmd(cmd): Send command via I2C
        write_data(data_buf): Send data buffer via I2C

    Notes:
        Implements SSD1327 driver with I2C communication protocol, adapted to OLED screens with standard I2C interface
    """

    def __init__(self, width: int, height: int, i2c: machine.I2C, addr: int = 0x3C) -> None:
        """
        初始化SSD1327 I2C驱动子类
        Args:
            width (int): OLED屏幕宽度
            height (int): OLED屏幕高度
            i2c (machine.I2C): I2C通信对象（已初始化）
            addr (int, optional): OLED屏幕I2C地址，默认0x3c

        Raises:
            无

        Notes:
            初始化I2C参数，创建命令和数据传输缓冲区，调用父类初始化方法

        ==========================================

        Initialize SSD1327 I2C driver subclass
        Args:
            width (int): OLED screen width
            height (int): OLED screen height
            i2c (machine.I2C): I2C communication object (initialized)
            addr (int, optional): OLED screen I2C address, default 0x3c

        Raises:
            None

        Notes:
            Initialize I2C parameters, create command and data transmission buffers, call parent class initialization method
        """
        self.i2c: machine.I2C = i2c
        self.addr: int = addr
        # 创建命令缓冲区：寄存器标识+命令存储位
        self.cmd_arr: bytearray = bytearray([REG_CMD, 0])  # Co=1, D/C#=0
        # 创建数据传输列表：寄存器标识+数据缓冲区
        self.data_list: list[bytes | bytearray | None] = [bytes((REG_DATA,)), None]
        # 调用父类初始化方法
        super().__init__(width, height)

    def write_cmd(self, cmd: int) -> None:
        """
        通过I2C发送命令
        Args:
            cmd (int): 要发送的命令字节

        Raises:
            OSError: I2C通信失败时抛出

        Notes:
            将命令写入缓冲区后通过I2C发送到指定地址

        ==========================================

        Send command via I2C
        Args:
            cmd (int): Command byte to send

        Raises:
            OSError: Thrown when I2C communication fails

        Notes:
            Write command to buffer then send to specified address via I2C
        """
        self.cmd_arr[1] = cmd
        self.i2c.writeto(self.addr, self.cmd_arr)

    def write_data(self, data_buf: bytearray) -> None:
        """
        通过I2C发送数据缓冲区
        Args:
            data_buf (bytearray): 要发送的显示缓冲区数据

        Raises:
            OSError: I2C通信失败时抛出

        Notes:
            使用writevto批量发送寄存器标识和数据，提高传输效率

        ==========================================

        Send data buffer via I2C
        Args:
            data_buf (bytearray): Display buffer data to send

        Raises:
            OSError: Thrown when I2C communication fails

        Notes:
            Use writevto to batch send register identifier and data to improve transmission efficiency
        """
        self.data_list[1] = data_buf
        self.i2c.writevto(self.addr, self.data_list)


class SEEED_OLED_96X96(SSD1327_I2C):
    """
    适配Seeed Studio 96x96 SSD1327 OLED屏幕的I2C驱动子类
    Attributes:
        继承自SSD1327_I2C类的所有属性

    Methods:
        __init__(i2c): 初始化96x96 OLED屏幕I2C驱动
        lookup(table): 设置灰度查找表

    Notes:
        专门适配Seeed Studio 96x96尺寸的SSD1327 OLED屏幕

    ==========================================

    I2C driver subclass adapted for Seeed Studio 96x96 SSD1327 OLED screen
    Attributes:
        Inherits all attributes from SSD1327_I2C class

    Methods:
        __init__(i2c): Initialize 96x96 OLED screen I2C driver
        lookup(table): Set grayscale lookup table

    Notes:
        Specially adapted for Seeed Studio 96x96 size SSD1327 OLED screen
    """

    def __init__(self, i2c: machine.I2C) -> None:
        """
        初始化96x96 SSD1327 OLED屏幕I2C驱动
        Args:
            i2c (machine.I2C): I2C通信对象（已初始化）

        Raises:
            无

        Notes:
            调用父类初始化方法，指定屏幕尺寸为96x96

        ==========================================

        Initialize 96x96 SSD1327 OLED screen I2C driver
        Args:
            i2c (machine.I2C): I2C communication object (initialized)

        Raises:
            None

        Notes:
            Call parent class initialization method, specify screen size as 96x96
        """
        super().__init__(96, 96, i2c)

    def lookup(self, table: list[int]) -> None:
        """
        设置灰度查找表
        Args:
            table (list[int]): 灰度表数组，包含15个元素（对应灰度1~15）

        Raises:
            OSError: I2C通信失败时抛出

        Notes:
            GS0无预充电和电流驱动，仅设置1~15的灰度值

        ==========================================

        Set grayscale lookup table
        Args:
            table (list[int]): Grayscale table array, containing 15 elements (corresponding to grayscale 1~15)

        Raises:
            OSError: Thrown when I2C communication fails

        Notes:
            GS0 has no pre-charge and current drive, only set grayscale values 1~15
        """
        # GS0 has no pre-charge and current drive
        self.write_cmd(SET_GRAYSCALE_TABLE)
        for i in range(0, 15):
            self.write_cmd(table[i])


class WS_OLED_128X128(SSD1327_I2C):
    """
    适配128x128 SSD1327 OLED屏幕的I2C驱动子类
    Attributes:
        继承自SSD1327_I2C类的所有属性

    Methods:
        __init__(i2c, addr=0x3c): 初始化128x128 OLED屏幕I2C驱动

    Notes:
        专门适配128x128尺寸的SSD1327 OLED屏幕，默认I2C地址0x3c

    ==========================================

    I2C driver subclass adapted for 128x128 SSD1327 OLED screen
    Attributes:
        Inherits all attributes from SSD1327_I2C class

    Methods:
        __init__(i2c, addr=0x3c): Initialize 128x128 OLED screen I2C driver

    Notes:
        Specially adapted for 128x128 size SSD1327 OLED screen, default I2C address 0x3c
    """

    def __init__(self, i2c: machine.I2C, addr: int = 0x3C) -> None:
        """
        初始化128x128 SSD1327 OLED屏幕I2C驱动
        Args:
            i2c (machine.I2C): I2C通信对象（已初始化）
            addr (int, optional): OLED屏幕I2C地址，默认0x3c

        Raises:
            无

        Notes:
            调用父类初始化方法，指定屏幕尺寸为128x128

        ==========================================

        Initialize 128x128 SSD1327 OLED screen I2C driver
        Args:
            i2c (machine.I2C): I2C communication object (initialized)
            addr (int, optional): OLED screen I2C address, default 0x3c

        Raises:
            None

        Notes:
            Call parent class initialization method, specify screen size as 128x128
        """
        super().__init__(128, 128, i2c, addr)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
