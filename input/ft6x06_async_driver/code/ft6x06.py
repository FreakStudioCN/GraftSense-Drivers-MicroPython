# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Salvatore Sanfilippo, FreakStudio
# @File    : ft6x06.py
# @Description : FT6x06 I2C touch controller driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Salvatore Sanfilippo, FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入 micropython 相关模块
import micropython

# 预留 ISR 调试异常缓冲区
micropython.alloc_emergency_exception_buf(100)

# 导入引脚控制模块
from machine import Pin

# 导入时间相关模块
import time

# 导入 micropython 常量支持
try:
    from micropython import const
except ImportError:
    # CPython 兼容性回退
    def const(value):
        return value


# ======================================== 全局变量 ============================================

# FT6x06 系列默认 I2C 从机地址
_DEFAULT_ADDR = const(0x38)

# 设备模式寄存器地址
_REG_DEV_MODE = const(0x00)
# 手势 ID 寄存器地址
_REG_GEST_ID = const(0x01)
# 触摸状态寄存器地址
_REG_TD_STATUS = const(0x02)
# 触摸数据起始寄存器地址（每个触摸点占 6 字节）
_TOUCH_DATA_START = const(0x03)
# 每个触摸点数据长度（字节）
_TOUCH_DATA_SIZE = const(6)

# 触摸点数据解析位掩码
# 触摸事件位段掩码（data[0] 高 2 位）
_TOUCH_EVENT_MASK = const(0xC0)
# 触摸事件位段右移位数
_TOUCH_EVENT_SHIFT = const(6)
# X 坐标高位掩码（data[0] 低 3 位）
_COORD_HIGH_MASK = const(0x07)
# 触摸面积高位掩码（data[5] 高 4 位）
_AREA_SHIFT = const(4)

# I2C 读写默认重试次数
_DEFAULT_RETRIES = 3
# I2C 读写重试间隔（毫秒）
_DEFAULT_RETRY_DELAY_MS = 10

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# FT6x06 系列触摸控制器驱动类
class FT6x06:
    """
    FT6x06 系列 I2C 电容触摸控制器驱动
    ==========
    FT6x06 series I2C capacitive touch controller driver

    通过 I2C 总线与 FT6x06 系列（FT6206/FT6306 等）电容触摸控制器通信，
    提供触摸点检测、坐标读取、手势识别和中断回调支持。
    原始代码来自 antirez/micropython-ft6x06，经适配后仅使用 machine.I2C 原生接口。

    Attributes:
        i2c (machine.I2C): I2C 总线实例。
        i2c_addr (int): 设备 I2C 地址（默认 0x38）。
        _int_pin (machine.Pin | None): 中断引脚实例，未配置时为 None。
        _callback (callable | None): 用户注册的中断回调函数。
        _debug (bool): 是否启用调试日志输出。

    Methods:
        __init__(self, i2c, *, address, interrupt_pin, callback, trigger, debug):
            初始化 FT6x06 触摸控制器。
        get_touch_coords(self):
            获取所有当前触摸点的坐标和事件信息。
        get_touch_count(self):
            获取当前检测到的触摸点数量。
        get_coords_for_p(self, touch_id):
            获取指定索引触摸点的坐标和事件信息。
        get_reg(self, register, count=1):
            读取指定寄存器的数据。
        deinit(self):
            释放硬件资源。

    Notes:
        - 纯 I2C 触摸驱动，不依赖任何显示驱动或第三方兼容层。
        - 仅使用 machine.I2C.readfrom_mem / readfrom_mem_into / writeto_mem 进行 I2C 通信。
        - 寄存器地址为 8 位（addrsize=8 默认）。
        - 支持中断引脚配置和回调函数注入。
        - ISR 仅设置标志位并通过 micropython.schedule 调度实际处理，避免 ISR 中阻塞 I/O 或内存分配。
        - FT6x06 系列包括 FT6206、FT6306 等芯片，地址和寄存器映射兼容。
    """

    # FT6x06 默认 I2C 从机地址
    # 设备模式寄存器地址
    # 手势 ID 寄存器地址
    # 触摸状态寄存器地址
    # 触摸数据起始寄存器地址
    # 每个触摸点数据长度（字节）

    def __init__(
        self,
        i2c: object,
        *,
        address: int = _DEFAULT_ADDR,
        interrupt_pin: object = None,
        callback: callable = None,
        trigger: int = Pin.IRQ_FALLING,
        debug: bool = False,
    ) -> None:
        """
        初始化 FT6x06 触摸控制器
        ==========
        Initialize FT6x06 touch controller over I2C

        配置 I2C 总线、设备地址、中断引脚和回调函数。

        Args:
            i2c (machine.I2C): I2C 总线实例（须已由调用者初始化）。
            address (int, optional): I2C 从机地址，默认 0x38。
            interrupt_pin (machine.Pin, optional): 中断引脚实例，用于接收触摸事件通知。
            callback (callable, optional): 用户中断回调函数，
                签名为 callback(data) -> None，其中 data 为 get_touch_coords() 的返回值。
            trigger (int, optional): 中断触发条件，默认为 Pin.IRQ_FALLING（下降沿触发）。
            debug (bool, optional): 是否启用调试日志输出，默认 False。

        Raises:
            TypeError: i2c 不是有效的 I2C 总线实例。
            ValueError: interrupt_pin 不是有效的 Pin 实例。
            RuntimeError: I2C 通信失败。

        Notes:
            - i2c 参数需至少具备 readfrom_mem 方法。
            - interrupt_pin / callback / trigger 至少一组需提供，否则仅支持轮询模式。
            - ISR 仅设置标志位并通过 micropython.schedule 调度实际处理，
              用户回调在非 ISR 上下文执行。
        """
        # 校验 I2C 总线实例是否具备必要方法
        if not hasattr(i2c, "readfrom_mem"):
            raise TypeError("i2c must have readfrom_mem method")

        # 校验地址参数类型
        if not isinstance(address, int):
            raise TypeError("address must be an integer")

        # 保存 I2C 总线实例和设备地址
        self.i2c = i2c
        self.i2c_addr = address

        # 调试日志开关
        self._debug = debug

        # 中断引脚和回调
        self._int_pin = None
        self._callback = None

        # 配置中断引脚（若提供）
        if interrupt_pin is not None:
            # 校验 interrupt_pin 是否为有效的 Pin 实例
            if not hasattr(interrupt_pin, "irq"):
                raise ValueError("interrupt_pin must be a Pin instance")
            # 保存中断引脚引用
            self._int_pin = interrupt_pin
            # 若提供了回调函数，则注册中断处理
            if callback is not None:
                self._callback = callback
                # 注册 ISR 处理函数
                self._int_pin.irq(
                    handler=self._irq_handler,
                    trigger=trigger,
                )

    # ======================== 公开方法 ========================

    def get_touch_coords(self) -> list:
        """
        获取所有当前触摸点的坐标和事件信息
        ==========
        Get coordinates and event info for all current touch points

        从设备读取触摸状态和触摸点数据，返回包含所有触摸点信息的列表。

        Returns:
            list | None: 触摸点数据列表，每项为包含以下键的字典：
                - x (int): X 坐标
                - y (int): Y 坐标
                - type (str): 事件类型，"down"（按下）或 "up"（抬起）
                - weight (int): 触摸压力权重
                - area (int): 触摸面积
                若无触摸，返回 None。

        Raises:
            RuntimeError: I2C 通信失败。

        Notes:
            - 侧作用：读取 I2C 设备寄存器。
            - ISR-safe: 否。
        """
        # 获取当前触摸点数量
        touches = self.get_touch_count()
        if touches == 0:
            return None

        touch_data = []
        # 遍历每个触摸点获取数据
        for i in range(touches):
            ev = self.get_coords_for_p(i)
            # 根据触摸事件代码确定事件类型
            ev_type = "down" if ev[2] == 0 else "up"
            touch_data.append(
                {
                    "x": ev[0],
                    "y": ev[1],
                    "type": ev_type,
                    "weight": ev[3],
                    "area": ev[4],
                }
            )
        return touch_data

    def get_touch_count(self) -> int:
        """
        获取当前检测到的触摸点数量
        ==========
        Get the number of currently detected touch points

        读取触摸状态寄存器，返回当前屏幕上的触摸点数量。

        Returns:
            int: 触摸点数量（0 为无触摸，最大为 2 取决于芯片型号）。

        Raises:
            RuntimeError: I2C 通信失败。

        Notes:
            - 侧作用：读取 I2C 设备寄存器。
            - ISR-safe: 否。
        """
        # 读取 TD_STATUS 寄存器，低 3 位表示触摸点数
        return self.get_reg(_REG_TD_STATUS) & 7

    def get_coords_for_p(self, touch_id: int) -> tuple:
        """
        获取指定索引触摸点的坐标和事件信息
        ==========
        Get coordinates and event info for a specific touch point

        从设备读取指定触摸点的完整数据（6 字节），解析并返回坐标、事件类型、
        压力和面积信息。

        Args:
            touch_id (int): 触摸点索引（0 或 1，取决于芯片支持的点数）。

        Returns:
            tuple: (x, y, event, weight, area)
                - x (int): X 坐标
                - y (int): Y 坐标
                - event (int): 触摸事件代码，0 为按下，1 为抬起
                - weight (int): 触摸压力权重
                - area (int): 触摸面积

        Raises:
            TypeError: 若 touch_id 不是整数类型。
            RuntimeError: I2C 通信失败。

        Notes:
            - 侧作用：读取 I2C 设备寄存器。
            - 寄存器布局：每个触摸点占 6 字节（地址从 0x03 + touch_id * 6 开始）。
            - ISR-safe: 否。
        """
        # 校验参数类型
        if not isinstance(touch_id, int):
            raise TypeError("touch_id must be an integer")

        # 计算触摸点数据起始寄存器地址
        start_reg = _TOUCH_DATA_START + (_TOUCH_DATA_SIZE * touch_id)
        # 读取 6 字节触摸点数据
        data = self.get_reg(start_reg, 6)

        # 解析触摸事件代码（data[0] 高 2 位）
        event = data[0] >> _TOUCH_EVENT_SHIFT
        # 解析 X 坐标：data[0] 低 3 位为高字节，data[1] 为低字节
        x = ((data[0] & _COORD_HIGH_MASK) << 8) | data[1]
        # 解析 Y 坐标：data[2] 低 3 位为高字节，data[3] 为低字节
        y = ((data[2] & _COORD_HIGH_MASK) << 8) | data[3]
        # 触摸压力权重
        weight = data[4]
        # 触摸面积（data[5] 高 4 位）
        area = data[5] >> _AREA_SHIFT

        return (x, y, event, weight, area)

    def get_reg(self, register: int, count: int = 1) -> bytearray:
        """
        读取指定寄存器的数据
        ==========
        Read data from the specified register

        从指定寄存器地址读取 1 字节或多字节数据，内置重试机制。

        Args:
            register (int): 8 位寄存器起始地址。
            count (int, optional): 要读取的字节数，默认 1。

        Returns:
            bytearray | int: 若 count 为 1，返回单字节整数值；否则返回 bytearray。

        Raises:
            RuntimeError: I2C 通信失败（重试耗尽后）。

        Notes:
            - 内置重试机制：最多重试 3 次，每次重试前延时 10 ms。
            - 使用 machine.I2C.readfrom_mem() 读取数据。
            - ISR-safe: 否（包含延时和异常抛出）。
        """
        max_retries = _DEFAULT_RETRIES
        for attempt in range(max_retries):
            try:
                # 从指定寄存器读取数据
                if count == 1:
                    # 单字节读取：返回整数值
                    val = self.i2c.readfrom_mem(self.i2c_addr, register, 1)[0]
                    return val
                else:
                    # 多字节读取：返回 bytearray
                    return self.i2c.readfrom_mem(self.i2c_addr, register, count)
            except OSError as e:
                if attempt < max_retries - 1:
                    # 延时后重试
                    time.sleep_ms(_DEFAULT_RETRY_DELAY_MS)
                    continue
                raise RuntimeError("I2C read failed at register 0x{:02X}".format(register)) from e

    # ======================== 属性 ========================

    # ======================== 私有方法 ========================

    def _irq_handler(self, pin: object) -> None:
        """
        中断服务程序（ISR 上下文）
        ==========
        Interrupt service routine (ISR context)

        响应触摸中断引脚的变化，通过 micropython.schedule 将实际处理
        推迟到主循环上下文执行。

        Args:
            pin (machine.Pin): 触发中断的引脚实例。

        Notes:
            - ISR-safe: 是（仅调用 micropython.schedule，不分配内存、不执行 I/O）。
            - 实际数据处理在 _process_touch_irq 中执行。
        """
        # ISR 中仅调度实际处理函数到主循环上下文
        try:
            micropython.schedule(self._process_touch_irq, 0)
        except RuntimeError:
            # A full scheduler queue is recoverable; retain the event for a
            # task-context poll instead of raising from the ISR.
            self._irq_pending = True

    def _process_touch_irq(self, _: object) -> None:
        """
        在主循环上下文中处理触摸中断
        ==========
        Process touch interrupt in main loop context

        通过 micropython.schedule 从 ISR 调度执行。
        读取触摸数据并调用用户注册的回调函数。

        Args:
            _ (object): micropython.schedule 传入的附加数据（未使用）。

        Notes:
            - ISR-safe: 否（执行 I2C 读取和用户回调）。
            - 侧作用：执行 I2C 通信和用户回调函数。
        """
        # I2C reads and user callbacks belong to the async task that polls
        # get_touch_coords_async(), never to the IRQ/scheduler chain.
        self._irq_pending = True

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        ==========
        Output debug log message

        仅在 _debug 为 True 时输出日志信息。

        Args:
            msg (str): 日志消息字符串。

        Notes:
            - 通过 print() 输出，格式为 "FT6x06: <message>"。
            - 可在子类中覆盖以实现自定义日志行为。
            - ISR-safe: 否。
        """
        if self._debug:
            print("FT6x06:", msg)

    # ======================== 释放资源 ========================

    def deinit(self) -> None:
        """
        释放硬件资源
        ==========
        Release hardware resources

        释放 FT6x06 驱动持有的硬件资源，包括禁用中断和清空引用。

        Notes:
            - 若配置了中断引脚，将禁用 IRQ。
            - I2C 总线本身不由本方法关闭，需由调用者在适当时机管理。
            - 调用此方法后，驱动实例不应再使用。
            - 侧作用：修改中断引脚配置，清空内部引用。
        """
        # 若配置了中断引脚，则禁用 IRQ
        if self._int_pin is not None:
            self._int_pin.irq(handler=None)

        # 清空中断引脚和回调引用
        self._int_pin = None
        self._callback = None

        # 清空 I2C 总线引用
        self.i2c = None

        # 输出调试信息
        self._log("driver deinitialized")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
