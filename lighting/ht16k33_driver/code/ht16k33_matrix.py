# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:16
# @Author  : mcauser
# @File    : main.py
# @Description : HT16K33点阵屏驱动 实现HT16K33芯片控制各类点阵屏的基础功能 参考自:https://github.com/mcauser/deshipu-micropython-ht16k33
# @License : MIT
__version__ = "0.1.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入硬件控制模块，用于I2C通信
import machine

# 导入micropython的const方法，用于定义常量
from micropython import const

# ======================================== 全局变量 ============================================

# HT16K33芯片闪烁命令基础地址，取值0x80
_HT16K33_BLINK_CMD = const(0x80)
# HT16K33芯片显示开启标志位，取值0x01
_HT16K33_BLINK_DISPLAYON = const(0x01)
# HT16K33芯片亮度调节命令基础地址，取值0xE0
_HT16K33_CMD_BRIGHTNESS = const(0xE0)
# HT16K33芯片振荡器开启命令，取值0x21
_HT16K33_OSCILATOR_ON = const(0x21)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class HT16K33:
    """
        HT16K33芯片的基础类，用于所有基于HT16K33芯片的扩展板和功能模块
        Attributes:
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            __init__: 初始化HT16K33芯片的通信参数和默认配置
            _write_cmd: 向HT16K33芯片发送单个命令字节
            blink_rate: 获取或设置芯片的显示闪烁速率
            brightness: 获取或设置芯片的显示亮度
            show: 将缓存中的显示数据发送到芯片，更新实际显示
            fill: 用指定颜色填充整个显示缓存
            _pixel: 设置显示缓存中单个像素点的颜色

        Notes:
            该类为基础类，通常不直接实例化，而是通过子类实现具体的点阵屏控制
    ==========================================
    Base class for all HT16K33-based backpacks and wings
    Attributes:
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            __init__: Initialize the communication parameters and default configuration of HT16K33 chip
            _write_cmd: Send a single command byte to HT16K33 chip
            blink_rate: Get or set the display blink rate of the chip
            brightness: Get or set the display brightness of the chip
            show: Send the display data in the buffer to the chip to update the actual display
            fill: Fill the entire display buffer with the specified color
            _pixel: Set the color of a single pixel in the display buffer

    Notes:
            This class is a base class and is usually not instantiated directly, but implements specific dot matrix screen control through subclasses
    """

    def __init__(self, i2c: machine.I2C, address: int = 0x70) -> None:
        """
        初始化HT16K33芯片的通信参数和默认配置
        Args:
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片建立I2C通信连接
            address (int): HT16K33芯片的I2C地址，可选参数，默认值为0x70

        Raises:
            ValueError: i2c参数为None或address超出0x00-0x7F范围时触发
            TypeError: i2c非machine.I2C类型或address非整数类型时触发

        Notes:
            初始化过程会开启芯片振荡器、设置默认闪烁速率为0（不闪烁）、默认亮度为15（最大亮度），并清空显示缓存


        ==========================================
        Initialize the communication parameters and default configuration of HT16K33 chip
        Args:
            i2c (machine.I2C): I2C communication object for establishing I2C communication connection with HT16K33 chip
            address (int): I2C address of HT16K33 chip, optional parameter, default value is 0x70

        Raises:
            ValueError: Triggered when i2c parameter is None or address is out of 0x00-0x7F range
            TypeError: Triggered when i2c is not machine.I2C type or address is not integer type

        Notes:
            The initialization process will turn on the chip oscillator, set the default blink rate to 0 (no blink), default brightness to 15 (maximum brightness), and clear the display buffer
        """
        # 检查i2c参数是否为None
        if i2c is None:
            raise ValueError("I2C communication object cannot be None")
        # 检查i2c参数类型是否为machine.I2C
        if not isinstance(i2c, machine.I2C):
            raise TypeError(f"machine.I2C expected for i2c, got {type(i2c).__name__}")
        # 检查address参数是否为None
        if address is None:
            raise ValueError("I2C address cannot be None")
        # 检查address参数类型是否为整数
        if not isinstance(address, int):
            raise TypeError(f"Integer expected for address, got {type(address).__name__}")
        # 检查address参数取值范围（I2C地址范围0x00-0x7F）
        if address < 0x00 or address > 0x7F:
            raise ValueError(f"I2C address must be between 0x00 and 0x7F, got {hex(address)}")

        self.i2c: machine.I2C = i2c
        self.address: int = address
        self._temp: bytearray = bytearray(1)
        self.buffer: bytearray = bytearray(16)
        self.fill(False)
        self._write_cmd(_HT16K33_OSCILATOR_ON)
        self.blink_rate(0)
        self.brightness(15)

    def _write_cmd(self, byte: int) -> None:
        """
        向HT16K33芯片发送单个命令字节
        Args:
            byte (int): 要发送的命令字节，为8位整数（0-255）

        Raises:
            ValueError: byte参数为None或超出0-255范围时触发
            TypeError: byte非整数类型时触发

        Notes:
            该方法为内部方法，用于封装I2C命令发送逻辑，外部无需直接调用


        ==========================================
        Send a single command byte to HT16K33 chip
        Args:
            byte (int): The command byte to be sent, an 8-bit integer (0-255)

        Raises:
            ValueError: Triggered when byte parameter is None or out of 0-255 range
            TypeError: Triggered when byte is not integer type

        Notes:
            This method is an internal method used to encapsulate the I2C command sending logic, and does not need to be called directly externally
        """
        # 检查byte参数是否为None
        if byte is None:
            raise ValueError("Command byte cannot be None")
        # 检查byte参数类型是否为整数
        if not isinstance(byte, int):
            raise TypeError(f"Integer expected for command byte, got {type(byte).__name__}")
        # 检查byte参数取值范围（8位字节范围0-255）
        if byte < 0 or byte > 255:
            raise ValueError(f"Command byte must be between 0 and 255, got {byte}")

        self._temp[0] = byte
        self.i2c.writeto(self.address, self._temp)

    def blink_rate(self, rate: int | None = None) -> int | None:
        """
        获取或设置HT16K33芯片的显示闪烁速率
        Args:
            rate (int | None): 闪烁速率值，可选参数，为0-2的整数（仅低2位有效）；若为None则返回当前闪烁速率

        Raises:
            ValueError: rate非None且超出0-2范围时触发
            TypeError: rate非None且非整数类型时触发

        Notes:
            闪烁速率仅支持特定值：0表示不闪烁，1表示2Hz闪烁，2表示1Hz闪烁


        ==========================================
        Get or set the display blink rate of HT16K33 chip
        Args:
            rate (int | None): Blink rate value, optional parameter, an integer from 0 to 2 (only the lower 2 bits are valid); if None, return the current blink rate

        Raises:
            ValueError: Triggered when rate is not None and out of 0-2 range
            TypeError: Triggered when rate is not None and not integer type

        Notes:
            The blink rate only supports specific values: 0 means no blink, 1 means 2Hz blink, 2 means 1Hz blink
        """
        if rate is None:
            return self._blink_rate

        # 检查rate参数类型是否为整数
        if not isinstance(rate, int):
            raise TypeError(f"Integer expected for blink rate, got {type(rate).__name__}")
        # 检查rate参数取值范围（0-2）
        if rate < 0 or rate > 2:
            raise ValueError(f"Blink rate must be between 0 and 2, got {rate}")

        rate = rate & 0x02
        self._blink_rate = rate
        self._write_cmd(_HT16K33_BLINK_CMD | _HT16K33_BLINK_DISPLAYON | rate << 1)

    def brightness(self, brightness: int | None = None) -> int | None:
        """
        获取或设置HT16K33芯片的显示亮度
        Args:
            brightness (int | None): 亮度值，可选参数，为0-15的整数（仅低4位有效）；若为None则返回当前亮度

        Raises:
            ValueError: brightness非None且超出0-15范围时触发
            TypeError: brightness非None且非整数类型时触发

        Notes:
            亮度值范围为0（最暗）到15（最亮），超出范围会被按位与0x0F截断


        ==========================================
        Get or set the display brightness of HT16K33 chip
        Args:
            brightness (int | None): Brightness value, optional parameter, an integer from 0 to 15 (only the lower 4 bits are valid); if None, return the current brightness

        Raises:
            ValueError: Triggered when brightness is not None and out of 0-15 range
            TypeError: Triggered when brightness is not None and not integer type

        Notes:
            The brightness value ranges from 0 (darkest) to 15 (brightest), and values outside the range will be truncated by AND with 0x0F
        """
        if brightness is None:
            return self._brightness

        # 检查brightness参数类型是否为整数
        if not isinstance(brightness, int):
            raise TypeError(f"Integer expected for brightness, got {type(brightness).__name__}")
        # 检查brightness参数取值范围（0-15）
        if brightness < 0 or brightness > 15:
            raise ValueError(f"Brightness must be between 0 and 15, got {brightness}")

        brightness = brightness & 0x0F
        self._brightness = brightness
        self._write_cmd(_HT16K33_CMD_BRIGHTNESS | brightness)

    def show(self) -> None:
        """
        将显示缓存中的数据发送到HT16K33芯片，更新实际显示内容
        Args:
            无
            None

        Raises:
            无
            None

        Notes:
            修改显示缓存后必须调用该方法才能让修改生效


        ==========================================
        Send the data in the display buffer to the HT16K33 chip to update the actual display content
        Args:
            None

        Raises:
            None

        Notes:
            This method must be called after modifying the display buffer for the changes to take effect
        """
        self.i2c.writeto_mem(self.address, 0x00, self.buffer)

    def fill(self, color: bool) -> None:
        """
        用指定颜色填充整个显示缓存
        Args:
            color (bool): 填充颜色值，True表示填充（亮），False表示清空（灭）

        Raises:
            ValueError: color参数为None时触发
            TypeError: color非整数类型时触发

        Notes:
            填充时会将缓存的16个字节全部设置为0xFF（亮）或0x00（灭）


        ==========================================
        Fill the entire display buffer with the specified color
        Args:
            color (int): Fill color value, non-zero means fill (on), 0 means clear (off)

        Raises:
            ValueError: Triggered when color parameter is None
            TypeError: Triggered when color is not integer type

        Notes:
            When filling, all 16 bytes of the buffer will be set to 0xFF (on) or 0x00 (off)
        """
        # 检查color参数是否为None
        if color is None:
            raise ValueError("Fill color cannot be None")
        # 检查color参数类型是否为整数
        if not isinstance(color, bool):
            raise TypeError(f"Integer expected for fill color, got {type(color).__name__}")

        fill = 0xFF if color else 0x00
        for i in range(16):
            self.buffer[i] = fill

    def _pixel(self, x: int, y: int, color: int | None = None) -> bool | None:
        """
        设置或获取显示缓存中单个像素点的颜色
        Args:
            x (int): 像素点的x轴坐标
            y (int): 像素点的y轴坐标
            color (int | None): 像素点颜色值，可选参数；非0表示亮，0表示灭，None则返回当前像素状态

        Raises:
            ValueError: x/y参数为None或color非None且超出合理范围时触发
            TypeError: x/y非整数类型或color非None且非整数类型时触发

        Notes:
            该方法为内部方法，用于底层像素操作，外部通过子类的pixel方法调用


        ==========================================
        Set or get the color of a single pixel in the display buffer
        Args:
            x (int): X-axis coordinate of the pixel
            y (int): Y-axis coordinate of the pixel
            color (int | None): Pixel color value, optional parameter; non-zero means on, 0 means off, None returns the current pixel state

        Raises:
            ValueError: Triggered when x/y parameter is None or color is not None and out of reasonable range
            TypeError: Triggered when x/y is not integer type or color is not None and not integer type

        Notes:
            This method is an internal method for low-level pixel operations, and is called externally through the pixel method of subclasses
        """
        # 检查x参数是否为None
        if x is None:
            raise ValueError("X coordinate cannot be None")
        # 检查x参数类型是否为整数
        if not isinstance(x, int):
            raise TypeError(f"Integer expected for x coordinate, got {type(x).__name__}")
        # 检查y参数是否为None
        if y is None:
            raise ValueError("Y coordinate cannot be None")
        # 检查y参数类型是否为整数
        if not isinstance(y, int):
            raise TypeError(f"Integer expected for y coordinate, got {type(y).__name__}")
        # 检查color参数类型（若不为None）
        if color is not None and not isinstance(color, int):
            raise TypeError(f"Integer expected for pixel color, got {type(color).__name__}")

        mask = 1 << x
        if color is None:
            return bool((self.buffer[y] | self.buffer[y + 1] << 8) & mask)
        if color:
            self.buffer[y * 2] |= mask & 0xFF
            self.buffer[y * 2 + 1] |= mask >> 8
        else:
            self.buffer[y * 2] &= ~(mask & 0xFF)
            self.buffer[y * 2 + 1] &= ~(mask >> 8)


class Matrix16x8(HT16K33):
    """
        16x8点阵屏的控制类，继承自HT16K33基础类
        Attributes:
            继承自HT16K33类的所有属性
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            pixel: 设置或获取16x8点阵屏上单个像素点的颜色

        Notes:
            该类适配16x8规格的点阵屏，会对像素坐标进行映射转换以匹配硬件布局
    ==========================================
    Control class for 16x8 dot matrix screen, inherited from HT16K33 base class
    Attributes:
            All attributes inherited from HT16K33 class
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            pixel: Set or get the color of a single pixel on the 16x8 dot matrix screen

    Notes:
            This class is adapted to 16x8 dot matrix screens, and will map and convert pixel coordinates to match the hardware layout
    """

    def pixel(self, x: int, y: int, color: int | None = None) -> bool | None:
        """
        设置或获取16x8点阵屏上单个像素点的颜色
        Args:
            x (int): 像素点的x轴坐标，范围0-15
            y (int): 像素点的y轴坐标，范围0-7
            color (int | None): 像素点颜色值，可选参数；非0表示亮，0表示灭，None则返回当前像素状态

        Raises:
            ValueError: x/y参数为None时触发
            TypeError: x/y非整数类型或color非None且非整数类型时触发

        Notes:
            坐标超出0-15（x）或0-7（y）范围时，方法直接返回，不执行任何操作


        ==========================================
        Set or get the color of a single pixel on the 16x8 dot matrix screen
        Args:
            x (int): X-axis coordinate of the pixel, range 0-15
            y (int): Y-axis coordinate of the pixel, range 0-7
            color (int | None): Pixel color value, optional parameter; non-zero means on, 0 means off, None returns the current pixel state

        Raises:
            ValueError: Triggered when x/y parameter is None
            TypeError: Triggered when x/y is not integer type or color is not None and not integer type

        Notes:
            When the coordinates are outside the range of 0-15 (x) or 0-7 (y), the method returns directly without performing any operations
        """
        # 检查x参数是否为None
        if x is None:
            raise ValueError("X coordinate cannot be None")
        # 检查x参数类型是否为整数
        if not isinstance(x, int):
            raise TypeError(f"Integer expected for x coordinate, got {type(x).__name__}")
        # 检查y参数是否为None
        if y is None:
            raise ValueError("Y coordinate cannot be None")
        # 检查y参数类型是否为整数
        if not isinstance(y, int):
            raise TypeError(f"Integer expected for y coordinate, got {type(y).__name__}")
        # 检查color参数类型（若不为None）
        if color is not None and not isinstance(color, int):
            raise TypeError(f"Integer expected for pixel color, got {type(color).__name__}")

        if not 0 <= x <= 15:
            return
        if not 0 <= y <= 7:
            return
        if x >= 8:
            x -= 8
            y += 8
        return super()._pixel(y, x, color)


class Matrix8x8(HT16K33):
    """
        8x8点阵屏的控制类，继承自HT16K33基础类
        Attributes:
            继承自HT16K33类的所有属性
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            pixel: 设置或获取8x8点阵屏上单个像素点的颜色

        Notes:
            该类适配8x8规格的点阵屏，会对x轴坐标进行偏移转换以匹配硬件布局
    ==========================================
    Control class for 8x8 dot matrix screen, inherited from HT16K33 base class
    Attributes:
            All attributes inherited from HT16K33 class
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            pixel: Set or get the color of a single pixel on the 8x8 dot matrix screen

    Notes:
            This class is adapted to 8x8 dot matrix screens, and will offset and convert the x-axis coordinates to match the hardware layout
    """

    def pixel(self, x: int, y: int, color: int | None = None) -> bool | None:
        """
        设置或获取8x8点阵屏上单个像素点的颜色
        Args:
            x (int): 像素点的x轴坐标，范围0-7
            y (int): 像素点的y轴坐标，范围0-7
            color (int | None): 像素点颜色值，可选参数；非0表示亮，0表示灭，None则返回当前像素状态

        Raises:
            ValueError: x/y参数为None时触发
            TypeError: x/y非整数类型或color非None且非整数类型时触发

        Notes:
            坐标超出0-7范围时，方法直接返回，不执行任何操作；x轴坐标会进行(x-1)%8的偏移转换


        ==========================================
        Set or get the color of a single pixel on the 8x8 dot matrix screen
        Args:
            x (int): X-axis coordinate of the pixel, range 0-7
            y (int): Y-axis coordinate of the pixel, range 0-7
            color (int | None): Pixel color value, optional parameter; non-zero means on, 0 means off, None returns the current pixel state

        Raises:
            ValueError: Triggered when x/y parameter is None
            TypeError: Triggered when x/y is not integer type or color is not None and not integer type

        Notes:
            When the coordinates are outside the range of 0-7, the method returns directly without performing any operations; the x-axis coordinate will be offset and converted by (x-1)%8
        """
        # 检查x参数是否为None
        if x is None:
            raise ValueError("X coordinate cannot be None")
        # 检查x参数类型是否为整数
        if not isinstance(x, int):
            raise TypeError(f"Integer expected for x coordinate, got {type(x).__name__}")
        # 检查y参数是否为None
        if y is None:
            raise ValueError("Y coordinate cannot be None")
        # 检查y参数类型是否为整数
        if not isinstance(y, int):
            raise TypeError(f"Integer expected for y coordinate, got {type(y).__name__}")
        # 检查color参数类型（若不为None）
        if color is not None and not isinstance(color, int):
            raise TypeError(f"Integer expected for pixel color, got {type(color).__name__}")

        if not 0 <= x <= 7:
            return
        if not 0 <= y <= 7:
            return
        x = (x - 1) % 8
        return super()._pixel(x, y, color)


class Matrix8x8x2(HT16K33):
    """
        8x8双色点阵屏的控制类，继承自HT16K33基础类
        Attributes:
            继承自HT16K33类的所有属性
            i2c (machine.I2C): I2C通信对象，用于与HT16K33芯片进行I2C通信
            address (int): HT16K33芯片的I2C地址，默认值为0x70
            _temp (bytearray): 临时字节数组，用于存储单次发送的命令字节
            buffer (bytearray): 显示缓存数组，长度为16，用于存储点阵屏的显示数据
            _blink_rate (int): 闪烁频率参数，存储当前设置的闪烁速率
            _brightness (int): 亮度参数，存储当前设置的亮度值（0-15）

        Methods:
            pixel: 设置或获取8x8双色点阵屏上单个像素点的颜色
            fill: 用指定颜色填充整个8x8双色点阵屏的显示缓存

        Notes:
            该类适配8x8双色点阵屏，颜色值0表示灭，1表示第一种颜色，2表示第二种颜色，3表示两种颜色同时亮
    ==========================================
    Control class for 8x8 bi-color dot matrix screen, inherited from HT16K33 base class
    Attributes:
            All attributes inherited from HT16K33 class
            i2c (machine.I2C): I2C communication object for I2C communication with HT16K33 chip
            address (int): I2C address of HT16K33 chip, default value is 0x70
            _temp (bytearray): Temporary byte array for storing a single command byte to be sent
            buffer (bytearray): Display buffer array with length 16, used to store display data of dot matrix screen
            _blink_rate (int): Blink rate parameter, stores the currently set blink rate
            _brightness (int): Brightness parameter, stores the currently set brightness value (0-15)

    Methods:
            pixel: Set or get the color of a single pixel on the 8x8 bi-color dot matrix screen
            fill: Fill the display buffer of the entire 8x8 bi-color dot matrix screen with the specified color

    Notes:
            This class is adapted to 8x8 bi-color dot matrix screens, color value 0 means off, 1 means first color, 2 means second color, 3 means both colors on
    """

    def pixel(self, x: int, y: int, color: int | None = None) -> int | None:
        """
        设置或获取8x8双色点阵屏上单个像素点的颜色
        Args:
            x (int): 像素点的x轴坐标，范围0-7
            y (int): 像素点的y轴坐标，范围0-7
            color (int | None): 像素颜色值，可选参数；0灭，1第一种颜色，2第二种颜色，3两种颜色，None则返回当前颜色值

        Raises:
            ValueError: x/y参数为None或color非None且超出0-3范围时触发
            TypeError: x/y非整数类型或color非None且非整数类型时触发

        Notes:
            坐标超出0-7范围时，方法直接返回，不执行任何操作；颜色值仅低2位有效


        ==========================================
        Set or get the color of a single pixel on the 8x8 bi-color dot matrix screen
        Args:
            x (int): X-axis coordinate of the pixel, range 0-7
            y (int): Y-axis coordinate of the pixel, range 0-7
            color (int | None): Pixel color value, optional parameter; 0 off, 1 first color, 2 second color, 3 both colors, None returns the current color value

        Raises:
            ValueError: Triggered when x/y parameter is None or color is not None and out of 0-3 range
            TypeError: Triggered when x/y is not integer type or color is not None and not integer type

        Notes:
            When the coordinates are outside the range of 0-7, the method returns directly without performing any operations; only the lower 2 bits of the color value are valid
        """
        # 检查x参数是否为None
        if x is None:
            raise ValueError("X coordinate cannot be None")
        # 检查x参数类型是否为整数
        if not isinstance(x, int):
            raise TypeError(f"Integer expected for x coordinate, got {type(x).__name__}")
        # 检查y参数是否为None
        if y is None:
            raise ValueError("Y coordinate cannot be None")
        # 检查y参数类型是否为整数
        if not isinstance(y, int):
            raise TypeError(f"Integer expected for y coordinate, got {type(y).__name__}")
        # 检查color参数（若不为None）
        if color is not None:
            if not isinstance(color, int):
                raise TypeError(f"Integer expected for pixel color, got {type(color).__name__}")
            # 检查color参数取值范围（0-3）
            if color < 0 or color > 3:
                raise ValueError(f"Bi-color value must be between 0 and 3, got {color}")

        if not 0 <= x <= 7:
            return
        if not 0 <= y <= 7:
            return
        if color is not None:
            super()._pixel(y, x, (color & 0x01))
            super()._pixel(y + 8, x, (color >> 1) & 0x01)
        else:
            return super()._pixel(y, x) | super()._pixel(y + 8, x) << 1

    def fill(self, color: int) -> None:
        """
        用指定颜色填充整个8x8双色点阵屏的显示缓存
        Args:
            color (int): 填充颜色值；0灭，1第一种颜色，2第二种颜色，3两种颜色同时亮

        Raises:
            ValueError: color参数为None或超出0-3范围时触发
            TypeError: color非整数类型时触发

        Notes:
            填充时会分别处理两种颜色的缓存区域，确保双色点阵屏的填充效果符合预期


        ==========================================
        Fill the display buffer of the entire 8x8 bi-color dot matrix screen with the specified color
        Args:
            color (int): Fill color value; 0 off, 1 first color, 2 second color, 3 both colors on

        Raises:
            ValueError: Triggered when color parameter is None or out of 0-3 range
            TypeError: Triggered when color is not integer type

        Notes:
            When filling, the buffer areas of the two colors are processed separately to ensure that the filling effect of the bi-color dot matrix screen meets expectations
        """
        # 检查color参数是否为None
        if color is None:
            raise ValueError("Fill color cannot be None")
        # 检查color参数类型是否为整数
        if not isinstance(color, int):
            raise TypeError(f"Integer expected for fill color, got {type(color).__name__}")
        # 检查color参数取值范围（0-3）
        if color < 0 or color > 3:
            raise ValueError(f"Bi-color fill value must be between 0 and 3, got {color}")

        fill1 = 0xFF if color & 0x01 else 0x00
        fill2 = 0xFF if color & 0x02 else 0x00
        for i in range(8):
            self.buffer[i * 2] = fill1
            self.buffer[i * 2 + 1] = fill2


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
