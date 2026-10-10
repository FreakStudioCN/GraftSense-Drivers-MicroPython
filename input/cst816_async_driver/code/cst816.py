# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : FreakStudio
# @File    : cst816.py
# @Description : CST816/CST816S/CST816T/CST816D touch driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython

micropython.alloc_emergency_exception_buf(100)

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


import time
from machine import Pin

# ======================================== 全局变量 ============================================

# CST816 默认 I2C 地址（与常见 FT 系列芯片的 0x38 不同）
DEFAULT_ADDRESS = const(0x15)

# 寄存器地址定义
REG_GESTURE = const(0x01)  # 手势寄存器
REG_FINGER_NUM = const(0x02)  # 触摸点数寄存器
REG_XH = const(0x03)  # X 坐标高字节
REG_CHIP_ID = const(0xA7)  # 芯片 ID 寄存器
REG_FW_VERSION = const(0xA9)  # 固件版本寄存器

# 手势类型常量
GESTURE_NONE = const(0)  # 无手势
GESTURE_UP = const(1)  # 上滑
GESTURE_DOWN = const(2)  # 下滑
GESTURE_LEFT = const(3)  # 左滑
GESTURE_RIGHT = const(4)  # 右滑
GESTURE_CLICK = const(5)  # 单击
GESTURE_DOUBLE_CLICK = const(11)  # 双击
GESTURE_LONG_PRESS = const(12)  # 长按

# I2C 复用缓冲区（减少内存分配）
_BUF = bytearray(6)

# ======================================== 功能函数 ============================================

# （本驱动无独立功能函数，所有逻辑封装在 CST816 类中）

# ======================================== 自定义类 ============================================


class CST816:
    """
    CST816 系列 I2C 电容触摸控制器驱动类。

    支持 CST816/CST816S/CST816T/CST816D 型号，通过 I2C 接口读取触摸坐标、
    手势和触摸点数。

    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _addr (int): 设备 I2C 地址（默认 0x15）
        _reset_pin (Pin): 复位引脚实例（可选）
        _irq_pin (Pin): 中断引脚实例（可选）
        _width (int): 触摸屏宽度
        _height (int): 触摸屏高度
        _triggered (bool): 中断触发标志位（ISR 设置，主循环读取）
        _debug (bool): 调试日志开关

    Methods:
        reset(): 硬件复位设备
        read_chip_id(): 读取芯片 ID
        read_revision(): 读取固件版本号
        get_touch_count(): 获取当前触摸点数
        get_gesture(): 获取手势类型
        read_point(): 读取触摸点坐标和手势信息
        touched(): 判断是否正在触摸
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - CST816 系列在屏幕未触摸时可能不响应 I2C，读取方法可能返回 None 或 0
        - ISR 回调仅设置标志位，不做内存分配或 I/O 操作
        - 默认 I2C 地址为 0x15（非 FT 系列常见的 0x38）
    ==========================================
    CST816 series I2C capacitive touch controller driver.

    Supports CST816/CST816S/CST816T/CST816D models. Reads touch coordinates,
    gestures, and touch point count over I2C.

    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _addr (int): Device I2C address (default 0x15)
        _reset_pin (Pin): Reset pin instance (optional)
        _irq_pin (Pin): Interrupt pin instance (optional)
        _width (int): Touch screen width
        _height (int): Touch screen height
        _triggered (bool): Interrupt flag (set by ISR, read by main loop)
        _debug (bool): Debug log switch

    Methods:
        reset(): Hardware reset the device
        read_chip_id(): Read chip ID
        read_revision(): Read firmware revision
        get_touch_count(): Get current touch point count
        get_gesture(): Get gesture type
        read_point(): Read touch point coordinates and gesture info
        touched(): Check if screen is being touched
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance, does not create bus internally
        - CST816 series may not respond to I2C when screen is untouched; read methods may return None or 0
        - ISR callback only sets flag, no memory allocation or I/O
        - Default I2C address is 0x15 (not the common 0x38 used by FT series)
    """

    # 默认触摸分辨率
    DEFAULT_WIDTH = const(240)
    DEFAULT_HEIGHT = const(240)

    __slots__ = ("_i2c", "_addr", "_reset_pin", "_irq_pin", "_width", "_height", "_triggered", "_debug")

    def __init__(
        self,
        i2c,
        address=DEFAULT_ADDRESS,
        reset_pin=None,
        irq_pin=None,
        callback=None,
        trigger=Pin.IRQ_FALLING,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        debug=False,
    ):
        """
        初始化 CST816 触摸控制器驱动实例。

        Args:
            i2c (I2C): I2C 总线实例（必须先由调用者初始化）
            address (int): 设备 I2C 地址，默认 0x15
            reset_pin (Pin): 复位引脚实例（可选）
            irq_pin (Pin): 中断引脚实例（可选）
            callback (callable): 外部中断回调函数（可选，不提供则使用内部 ISR）
            trigger (int): 中断触发条件，默认 Pin.IRQ_FALLING
            width (int): 触摸屏宽度，默认 240
            height (int): 触摸屏高度，默认 240
            debug (bool): 是否开启调试日志，默认关闭

        Returns:
            None

        Raises:
            ValueError: 参数类型或值不合法

        Notes:
            - ISR-safe: 否（注册中断回调）
            - 若提供 callback，中断发生时调用 callback；否则内部 ISR 设置 _triggered 标志位
        ==========================================
        Initialize CST816 touch controller driver instance.

        Args:
            i2c (I2C): I2C bus instance (must be initialized by caller first)
            address (int): Device I2C address, default 0x15
            reset_pin (Pin): Reset pin instance (optional)
            irq_pin (Pin): Interrupt pin instance (optional)
            callback (callable): External interrupt callback (optional, uses internal ISR if not provided)
            trigger (int): Interrupt trigger condition, default Pin.IRQ_FALLING
            width (int): Touch screen width, default 240
            height (int): Touch screen height, default 240
            debug (bool): Enable debug logging, default disabled

        Returns:
            None

        Raises:
            ValueError: Invalid parameter type or value

        Notes:
            - ISR-safe: No (registers interrupt callback)
            - If callback is provided, it is called on interrupt; otherwise internal ISR sets _triggered flag
        """
        # 参数校验：I2C 总线实例
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem()")
        # 参数校验：I2C 地址
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0 or address > 127:
            raise ValueError("address must be 0~127")
        # 参数校验：复位引脚
        if reset_pin is not None:
            if not hasattr(reset_pin, "value"):
                raise ValueError("reset_pin must be a Pin instance")
        # 参数校验：中断引脚
        if irq_pin is not None:
            if not hasattr(irq_pin, "irq"):
                raise ValueError("irq_pin must be a Pin instance")
        # 参数校验：外部中断回调
        if callback is not None:
            if not callable(callback):
                raise ValueError("callback must be callable")
        # 参数校验：中断触发条件
        if not isinstance(trigger, int):
            raise ValueError("trigger must be int")
        # 参数校验：触摸屏宽度
        if not isinstance(width, int):
            raise ValueError("width must be int")
        if width <= 0:
            raise ValueError("width must be > 0")
        # 参数校验：触摸屏高度
        if not isinstance(height, int):
            raise ValueError("height must be int")
        if height <= 0:
            raise ValueError("height must be > 0")
        # 参数校验：调试开关
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        # 保存实例属性
        self._i2c = i2c
        self._addr = address
        self._reset_pin = reset_pin
        self._irq_pin = irq_pin
        self._width = width
        self._height = height
        self._triggered = True
        self._debug = debug

        # 执行硬件复位（若提供了复位引脚）
        if reset_pin is not None:
            self.reset()

        # 注册中断回调（若提供了中断引脚）
        if irq_pin is not None:
            if callback is not None:
                irq_pin.irq(handler=callback, trigger=trigger)
            else:
                irq_pin.irq(handler=self._irq_handler, trigger=trigger)

    def reset(self):
        """
        硬件复位设备。

        通过复位引脚发送低-高脉冲复位触摸控制器。

        Args:
            无

        Returns:
            None

        Raises:
            ValueError: 未提供复位引脚

        Notes:
            - ISR-safe: 否（操作 GPIO）
            - 复位后 _triggered 标志置为 True
        ==========================================
        Hardware reset the device.

        Sends a low-high pulse on the reset pin to reset the touch controller.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: No reset pin configured

        Notes:
            - ISR-safe: No (GPIO operation)
            - Sets _triggered flag to True after reset
        """
        if self._reset_pin is None:
            raise ValueError("No reset pin configured")
        # 拉低复位引脚
        self._reset_pin.value(0)
        # 保持低电平 5ms
        time.sleep_ms(5)
        # 拉高复位引脚
        self._reset_pin.value(1)
        # 等待设备启动稳定
        time.sleep_ms(50)
        # 复位后标记为已触发
        self._triggered = True

    def read_chip_id(self):
        """
        读取芯片 ID。

        Args:
            无

        Returns:
            int: 芯片 ID 值
            None: 设备未响应（可能未触摸屏幕）

        Notes:
            - ISR-safe: 否（I2C 操作）
            - CST816 系列在屏幕未触摸时可能不响应 I2C，此时返回 None
        ==========================================
        Read the chip ID.

        Args:
            None

        Returns:
            int: Chip ID value
            None: Device not responding (screen may be untouched)

        Notes:
            - ISR-safe: No (I2C operation)
            - CST816 series may not respond to I2C when screen is untouched; returns None in that case
        """
        try:
            return self._i2c.readfrom_mem(self._addr, REG_CHIP_ID, 1)[0]
        except OSError:
            return None

    def read_revision(self):
        """
        读取固件版本号。

        Args:
            无

        Returns:
            int: 固件版本号
            None: 设备未响应（可能未触摸屏幕）

        Notes:
            - ISR-safe: 否（I2C 操作）
            - CST816 系列在屏幕未触摸时可能不响应 I2C，此时返回 None
        ==========================================
        Read the firmware revision number.

        Args:
            None

        Returns:
            int: Firmware revision number
            None: Device not responding (screen may be untouched)

        Notes:
            - ISR-safe: No (I2C operation)
            - CST816 series may not respond to I2C when screen is untouched; returns None in that case
        """
        try:
            return self._i2c.readfrom_mem(self._addr, REG_FW_VERSION, 1)[0]
        except OSError:
            return None

    def get_touch_count(self):
        """
        获取当前触摸点数。

        Args:
            无

        Returns:
            int: 触摸点数（0 表示无触摸或设备未响应）

        Notes:
            - ISR-safe: 否（I2C 操作）
            - CST816 系列在屏幕未触摸时可能不响应 I2C，此时返回 0
        ==========================================
        Get the current touch point count.

        Args:
            None

        Returns:
            int: Number of touch points (0 means no touch or device not responding)

        Notes:
            - ISR-safe: No (I2C operation)
            - CST816 series may not respond to I2C when screen is untouched; returns 0 in that case
        """
        try:
            return self._i2c.readfrom_mem(self._addr, REG_FINGER_NUM, 1)[0]
        except OSError:
            return 0

    def get_gesture(self):
        """
        获取手势类型。

        Args:
            无

        Returns:
            int: 手势类型（GESTURE_NONE/GESTURE_UP/GESTURE_DOWN 等）
                 GESTURE_NONE 也表示设备未响应

        Notes:
            - ISR-safe: 否（I2C 操作）
            - CST816 系列在屏幕未触摸时可能不响应 I2C，此时返回 GESTURE_NONE
        ==========================================
        Get the gesture type.

        Args:
            None

        Returns:
            int: Gesture type (GESTURE_NONE/GESTURE_UP/GESTURE_DOWN etc.)
                 GESTURE_NONE also indicates device not responding

        Notes:
            - ISR-safe: No (I2C operation)
            - CST816 series may not respond to I2C when screen is untouched; returns GESTURE_NONE in that case
        """
        try:
            return self._i2c.readfrom_mem(self._addr, REG_GESTURE, 1)[0]
        except OSError:
            return GESTURE_NONE

    def read_point(self):
        """
        读取触摸点坐标和手势信息。

        Args:
            无

        Returns:
            dict: {"x": int, "y": int, "gesture": int, "event": int}
            None: 无触摸或无新数据

        Notes:
            - ISR-safe: 否（I2C 操作、字典创建）
            - 使用模块级复用缓冲区 _BUF
            - 读取后重置 _triggered 标志
            - CST816 系列在屏幕未触摸时可能不响应 I2C，此时返回 None
            - 单击事件（gesture=5, event=1）表示手指抬起，返回 None
        ==========================================
        Read touch point coordinates and gesture information.

        Args:
            None

        Returns:
            dict: {"x": int, "y": int, "gesture": int, "event": int}
            None: No touch or no new data

        Notes:
            - ISR-safe: No (I2C operation, dict creation)
            - Uses module-level reusable buffer _BUF
            - Resets _triggered flag after reading
            - CST816 series may not respond to I2C when screen is untouched; returns None in that case
            - Click event (gesture=5, event=1) indicates finger lift, returns None
        """
        # 无中断触发且配置了中断引脚时，跳过读取
        if not self._triggered and self._irq_pin is not None:
            return None
        # 清除触发标志
        self._triggered = False
        # 一次性读取 6 字节触摸数据（从手势寄存器开始）
        try:
            self._i2c.readfrom_mem_into(self._addr, REG_GESTURE, _BUF)
        except OSError:
            return None
        # 解析手势类型
        gesture = _BUF[0]
        # 解析触摸点数
        points = _BUF[1]
        # 解析事件类型（高 2 位）
        event = _BUF[2] >> 6
        # 无触摸点，或单击抬手事件，返回 None
        if points == 0 or (gesture == GESTURE_CLICK and event == 1):
            return None
        # 解析 X 坐标（高 4 位 + 低 8 位）
        x = ((_BUF[2] & 0x0F) << 8) | _BUF[3]
        # 解析 Y 坐标（高 4 位 + 低 8 位）
        y = ((_BUF[4] & 0x0F) << 8) | _BUF[5]
        return {"x": x, "y": y, "gesture": gesture, "event": event}

    def touched(self):
        """
        判断屏幕是否正在被触摸。

        Args:
            无

        Returns:
            bool: True 表示有触摸点，False 表示无触摸

        Notes:
            - ISR-safe: 否（调用 get_touch_count 包含 I2C 操作）
        ==========================================
        Check whether the screen is currently being touched.

        Args:
            None

        Returns:
            bool: True if touch points detected, False otherwise

        Notes:
            - ISR-safe: No (calls get_touch_count which includes I2C operation)
        """
        return self.get_touch_count() > 0

    def deinit(self):
        """
        释放硬件资源。

        注销中断回调，释放 IRQ 引脚资源。

        Args:
            无

        Returns:
            None

        Notes:
            - ISR-safe: 否
            - 调用后中断功能停止，但 I2C 总线仍由调用者管理
        ==========================================
        Release hardware resources.

        Unregisters interrupt callback and releases IRQ pin resources.

        Args:
            None

        Returns:
            None

        Notes:
            - ISR-safe: No
            - After calling, interrupt is disabled but I2C bus remains managed by caller
        """
        # 注销中断回调
        if self._irq_pin is not None and hasattr(self._irq_pin, "irq"):
            self._irq_pin.irq(handler=None)

    def _log(self, msg):
        """
        内部调试日志输出。

        Args:
            msg (str): 日志消息

        Notes:
            - ISR-safe: 否（涉及 print 和字符串拼接）
            - 仅在 _debug 为 True 时输出
        ==========================================
        Internal debug logging.

        Args:
            msg (str): Log message

        Notes:
            - ISR-safe: No (involves print and string concatenation)
            - Only outputs when _debug is True
        """
        if self._debug:
            print("[CST816] %s" % msg)

    def _irq_handler(self, pin):
        """
        内部中断处理函数（ISR 安全）。

        仅设置 _triggered 标志位，不做内存分配或 I/O 操作。

        Args:
            pin (Pin): 触发中断的引脚实例

        Notes:
            - ISR-safe: 是（仅设置标志位，无内存分配）
        ==========================================
        Internal interrupt handler (ISR-safe).

        Only sets the _triggered flag; no memory allocation or I/O.

        Args:
            pin (Pin): The pin instance that triggered the interrupt

        Notes:
            - ISR-safe: Yes (only sets flag, no memory allocation)
        """
        self._triggered = True


# ======================================== 初始化配置 ==========================================
# （驱动文件初始化配置区留空，硬件初始化由调用者完成）

# ========================================  主程序  ===========================================
# （驱动文件主程序区留空，测试代码请使用 main.py）
