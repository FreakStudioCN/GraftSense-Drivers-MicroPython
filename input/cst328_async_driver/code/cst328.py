# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : cst328.py
# @Description : CST328 I2C capacitive touch driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ISR 紧急异常缓冲区（MicroPython 专用）
try:
    import micropython

    micropython.alloc_emergency_exception_buf(100)
except ImportError:
    pass

# const() 函数兼容性处理
try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time
from machine import Pin
import machine

# ======================================== 导入相关模块 =========================================
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================


class CST328:
    """
    CST328 I2C 电容触摸驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _rst_pin (Pin): 复位引脚，可为 None
        _irq_pin (Pin): 中断引脚，可为 None
        _callback (callable): 中断回调函数
        _trigger (int): 中断触发条件
        _width (int): 触摸屏逻辑宽度（像素）
        _height (int): 触摸屏逻辑高度（像素）
        _triggered (bool): 触摸事件标志位（ISR 设置）
        _buf (bytearray): I2C 读取复用缓冲区
        _debug (bool): 调试输出开关

    Methods:
        reset(): 硬件复位触摸控制器
        touched(): 检测当前是否被触摸
        read_point(): 读取当前触摸点坐标
        set_size(width, height): 设置触摸屏逻辑尺寸
        get_size(): 获取触摸屏逻辑尺寸
        set_debug(debug): 设置调试模式
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入的 I2C 实例，不在内部创建
        - 中断引脚可选，支持外部注入中断回调
        - 复位引脚可选，传入后 __init__ 自动执行硬件复位
        - 触摸数据寄存器使用 16 位地址访问（0xD000）
    ==========================================
    CST328 I2C capacitive touch driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _rst_pin (Pin): Reset pin, can be None
        _irq_pin (Pin): Interrupt pin, can be None
        _callback (callable): Interrupt callback function
        _trigger (int): Interrupt trigger condition
        _width (int): Touch screen logical width (pixels)
        _height (int): Touch screen logical height (pixels)
        _triggered (bool): Touch event flag (set by ISR)
        _buf (bytearray): Reusable I2C read buffer
        _debug (bool): Debug output switch

    Methods:
        reset(): Hardware reset the touch controller
        touched(): Check if currently touched
        read_point(): Read current touch point coordinates
        set_size(width, height): Set touch screen logical size
        get_size(): Get touch screen logical size
        set_debug(debug): Set debug mode
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance
        - Interrupt pin is optional, supports external callback injection
        - Reset pin is optional; auto-reset on init if provided
        - Touch data register uses 16-bit addressing (0xD000)
    """

    # 类级常量
    I2C_DEFAULT_ADDR = const(0x1A)
    _TOUCH_DATA_REG = const(0xD000)
    _TOUCH_DATA_LEN = const(27)
    _GESTURE_MASK = const(0x0F)
    _GESTURE_VALID = const(0x06)

    __slots__ = ("_i2c", "_address", "_rst_pin", "_irq_pin", "_callback", "_trigger", "_width", "_height", "_triggered", "_buf", "_debug")

    def __init__(
        self, i2c, address=I2C_DEFAULT_ADDR, rst_pin=None, irq_pin=None, callback=None, trigger=Pin.IRQ_FALLING, width=320, height=240, debug=False
    ):
        """
        初始化 CST328 触摸驱动

        Args:
            i2c (I2C): I2C 总线实例，必须支持 writeto/readfrom
            address (int): I2C 设备地址，默认 0x1A
            rst_pin (Pin): 复位引脚，可为 None
            irq_pin (Pin): 中断引脚，可为 None
            callback (callable): 中断回调函数，签名 callback(pin)，设为 None 使用内置回调
            trigger (int): 中断触发条件，默认 Pin.IRQ_FALLING
            width (int): 触摸屏逻辑宽度（像素），默认 320
            height (int): 触摸屏逻辑高度（像素），默认 240
            debug (bool): 是否启用调试输出，默认 False

        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: I2C 通信失败（复位时触发）

        Notes:
            - 传入 rst_pin 会在初始化时执行硬件复位
            - 传入 irq_pin 会自动注册中断（使用内置或外部回调）
        ==========================================
        Initialize CST328 touch driver.

        Args:
            i2c (I2C): I2C bus instance, must support writeto/readfrom
            address (int): I2C device address, default 0x1A
            rst_pin (Pin): Reset pin, can be None
            irq_pin (Pin): Interrupt pin, can be None
            callback (callable): Interrupt callback, signature callback(pin)
            trigger (int): Interrupt trigger, default Pin.IRQ_FALLING
            width (int): Touch screen logical width (pixels), default 320
            height (int): Touch screen logical height (pixels), default 240
            debug (bool): Enable debug output, default False

        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: I2C communication failed (during reset)

        Notes:
            - Hardware reset performed on init if rst_pin is provided
            - Interrupt registered automatically if irq_pin is provided
        """
        # I2C 总线实例校验
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide writeto()")
        if not hasattr(i2c, "readfrom"):
            raise ValueError("i2c must provide readfrom()")
        self._i2c = i2c

        # I2C 地址参数校验
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address).__name__)
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be 0x08~0x77, got 0x%02X" % address)
        self._address = address

        # 复位引脚校验与存储
        if rst_pin is not None:
            if not hasattr(rst_pin, "value"):
                raise ValueError("rst_pin must be a Pin instance or None")
        self._rst_pin = rst_pin

        # 中断引脚校验与存储
        if irq_pin is not None:
            if not hasattr(irq_pin, "irq"):
                raise ValueError("irq_pin must be a Pin instance or None")
        self._irq_pin = irq_pin

        # 中断回调校验
        if callback is not None:
            if not callable(callback):
                raise ValueError("callback must be callable or None")
        self._callback = callback

        # 中断触发条件校验
        if not isinstance(trigger, int):
            raise ValueError("trigger must be int, got %s" % type(trigger).__name__)
        self._trigger = trigger

        # 触摸屏尺寸参数校验
        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be positive int, got %s" % width)
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be positive int, got %s" % height)
        self._width = width
        self._height = height

        # 调试开关
        self._debug = bool(debug)

        # 触摸事件标志位（ISR 设置，主循环读取）
        self._triggered = True

        # I2C 读取复用缓冲区
        self._buf = bytearray(self._TOUCH_DATA_LEN)

        # 传入复位引脚则执行硬件复位
        if self._rst_pin is not None:
            self.reset()

        # 传入中断引脚则注册中断（优先使用外部回调，否则使用内置 ISR-safe 回调）
        if self._irq_pin is not None:
            handler = self._callback if self._callback is not None else self._irq_handler
            self._irq_pin.irq(handler=handler, trigger=self._trigger)

    # ==================== 公共方法 ====================

    def reset(self):
        """
        硬件复位触摸控制器

        Raises:
            RuntimeError: 复位引脚未配置或硬件复位失败

        Notes:
            - 修改硬件引脚状态，具有副作用
            - 复位完成后设置触摸标志位，允许后续读取
            - ISR-safe: 否
        ==========================================
        Hardware reset the touch controller.

        Raises:
            RuntimeError: Reset pin not configured or hardware reset failed

        Notes:
            - Modifies hardware pin state, has side effects
            - Sets touch flag after reset to allow subsequent reads
            - ISR-safe: No
        """
        if self._rst_pin is None:
            raise RuntimeError("Reset pin is not configured")
        try:
            self._rst_pin.value(1)
            time.sleep_ms(10)
            self._rst_pin.value(0)
            time.sleep_ms(10)
            self._rst_pin.value(1)
            time.sleep_ms(100)
        except OSError as e:
            raise RuntimeError("Hardware reset failed: %s" % str(e))
        self._triggered = True

    def touched(self) -> bool:
        """
        检测当前是否被触摸

        Returns:
            bool: True 表示当前有触摸，False 表示无触摸

        Notes:
            - 内部调用 read_point() 判断
            - ISR-safe: 否
        ==========================================
        Check if currently touched.

        Returns:
            bool: True if currently touched, False otherwise

        Notes:
            - Internally calls read_point()
            - ISR-safe: No
        """
        return self.read_point() is not None

    def read_point(self) -> dict:
        """
        读取当前触摸点坐标

        Returns:
            dict: {"x": x, "y": y} 触摸坐标，无触摸或读取失败返回 None

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 返回格式固定为 {"x": x, "y": y}
            - 使用中断标志位优化，无中断时不重复读取
            - ISR-safe: 否（主循环调用，涉及阻塞 I2C I/O）
        ==========================================
        Read current touch point coordinates.

        Returns:
            dict: {"x": x, "y": y} touch coordinates, None if no touch

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Return format is fixed as {"x": x, "y": y}
            - Uses interrupt flag to avoid repeated reads when no IRQ
            - ISR-safe: No (main loop, involves blocking I2C I/O)
        """
        # 禁用中断保护共享变量读取与清除
        state = machine.disable_irq()
        triggered = self._triggered
        self._triggered = False
        machine.enable_irq(state)

        # 无中断引脚且标志位未置位则跳过
        if not triggered and self._irq_pin is not None:
            return None

        # 读取触摸数据
        try:
            data = self._read_reg16(self._TOUCH_DATA_REG, self._TOUCH_DATA_LEN)
        except RuntimeError:
            return None

        # 校验手势标志位
        if (data[0] & self._GESTURE_MASK) != self._GESTURE_VALID:
            return None

        # 解析触摸坐标
        x = (data[1] << 4) | ((data[3] >> 4) & 0x0F)
        y = (data[2] << 4) | (data[3] & 0x0F)

        return {"x": x, "y": y}

    def set_size(self, width, height):
        """
        设置触摸屏逻辑尺寸

        Args:
            width (int): 触摸屏宽度（像素），必须 > 0
            height (int): 触摸屏高度（像素），必须 > 0

        Raises:
            ValueError: 参数类型或值无效

        Notes:
            - 仅修改逻辑坐标映射，不影响硬件
            - ISR-safe: 否
        ==========================================
        Set touch screen logical size.

        Args:
            width (int): Touch screen width (pixels), must be > 0
            height (int): Touch screen height (pixels), must be > 0

        Raises:
            ValueError: Invalid parameter type or value

        Notes:
            - Only modifies logical coordinate mapping
            - ISR-safe: No
        """
        if not isinstance(width, int) or width <= 0:
            raise ValueError("width must be positive int, got %s" % width)
        if not isinstance(height, int) or height <= 0:
            raise ValueError("height must be positive int, got %s" % height)
        self._width = width
        self._height = height

    def get_size(self) -> tuple:
        """
        获取触摸屏逻辑尺寸

        Returns:
            tuple: (width, height) 触摸屏尺寸（像素）

        Notes:
            - ISR-safe: 是（只读访问）
        ==========================================
        Get touch screen logical size.

        Returns:
            tuple: (width, height) touch screen size (pixels)

        Notes:
            - ISR-safe: Yes (read-only access)
        """
        return (self._width, self._height)

    def set_debug(self, debug):
        """
        设置调试模式

        Args:
            debug (bool): True 启用调试输出，False 禁用

        Notes:
            - ISR-safe: 否
        ==========================================
        Set debug mode.

        Args:
            debug (bool): True to enable debug output, False to disable

        Notes:
            - ISR-safe: No
        """
        self._debug = bool(debug)

    def deinit(self):
        """
        释放硬件资源

        Notes:
            - 取消中断引脚的回调注册
            - ISR-safe: 否
        ==========================================
        Release hardware resources.

        Notes:
            - Unregisters interrupt pin callback
            - ISR-safe: No
        """
        if self._irq_pin is not None and hasattr(self._irq_pin, "irq"):
            self._irq_pin.irq(handler=None)
        self._log("CST328 deinitialized")

    # ==================== 私有方法 ====================

    def _log(self, msg):
        """
        调试日志输出

        Args:
            msg (str): 日志消息

        Notes:
            - 仅在 _debug 为 True 时输出
            - ISR-safe: 否（涉及 print）
        ==========================================
        Debug log output.

        Args:
            msg (str): Log message

        Notes:
            - Outputs only when _debug is True
            - ISR-safe: No (involves print)
        """
        if self._debug:
            print("[CST328] %s" % msg)

    def _irq_handler(self, pin):
        """
        内置中断回调（ISR-safe）

        Args:
            pin (Pin): 触发中断的引脚实例

        Notes:
            - 仅设置触摸标志位，不分配内存，不执行 I/O
            - ISR-safe: 是
        ==========================================
        Internal interrupt handler (ISR-safe).

        Args:
            pin (Pin): Pin instance that triggered the interrupt

        Notes:
            - Only sets touch flag, no memory allocation, no I/O
            - ISR-safe: Yes
        """
        self._triggered = True

    def _read_reg16(self, reg, length, retries=1, delay_ms=5):
        """
        通过 16 位寄存器地址读取数据

        Args:
            reg (int): 16 位寄存器地址
            length (int): 读取字节数
            retries (int): I2C 通信重试次数，默认 1（共 2 次尝试）
            delay_ms (int): 重试间隔（毫秒），默认 5

        Returns:
            bytearray: 读取到的数据缓冲区

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 使用 writeto（不发送 STOP）+ readfrom 模式访问 16 位寄存器
            - 内置重试机制，应对瞬态 I2C 错误
            - ISR-safe: 否（涉及阻塞 I2C I/O）
        ==========================================
        Read data via 16-bit register address.

        Args:
            reg (int): 16-bit register address
            length (int): Number of bytes to read
            retries (int): I2C retry count, default 1 (2 total attempts)
            delay_ms (int): Retry interval (milliseconds), default 5

        Returns:
            bytearray: Read data buffer

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Uses writeto (no STOP) + readfrom for 16-bit register access
            - Built-in retry mechanism for transient I2C errors
            - ISR-safe: No (involves blocking I2C I/O)
        """
        for attempt in range(retries + 1):
            try:
                # 写入 16 位寄存器地址（不发送 STOP）
                self._i2c.writeto(
                    self._address,
                    bytes(((reg >> 8) & 0xFF, reg & 0xFF)),
                    False,
                )
                # 读取数据
                return self._i2c.readfrom(self._address, length)
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C read failed at reg 0x%04X" % reg)
                time.sleep_ms(delay_ms)


# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
