# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午1:34
# @Author  : 缪贵成
# @File    : pcf8574.py
# @Description : pcf8574扩展芯片驱动
# @License : CC BY-NC 4.0
# @Reference   :https://github.com/mcauser/micropython-pcf8574/blob/master/src/pcf8574.py

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 硬件相关的模块
from machine import Pin, I2C
# 导入micropython相关的模块
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义PCF8574类
class PCF8574:
    """
    该类控制 PCF8574 I2C GPIO 扩展芯片，提供端口读写、单引脚控制和翻转功能。

    Attributes:
        _i2c (I2C): machine.I2C 实例用于总线通信。
        _address (int): PCF8574 I2C 地址，0x20~0x27。
        _port (bytearray): 当前端口状态缓存。
        _callback (callable): 外部中断触发时调用的回调函数。
        _int_pin (Pin): 可选中断引脚对象。

    Methods:
        check() -> bool: 检查设备是否存在。
        port() -> int: 获取当前端口状态。
        port(value: int) -> None: 设置端口状态。
        pin(pin: int, value: int = None) -> int: 读取或设置单个引脚。
        toggle(pin: int) -> None: 翻转指定引脚状态。

    Notes:
        - 初始化时可选外部中断引脚及回调，ISR-safe 调用需使用 micropython.schedule。
        - 所有 I2C 操作非 ISR-safe，不建议在中断处理函数直接调用。
        - 支持 MicroPython v1.23.0。

    ==========================================

    PCF8574 driver for controlling I2C GPIO expanders. Provides port read/write, single pin control and toggle.

    Attributes:
        _i2c (I2C): machine.I2C instance for bus communications.
        _address (int): I2C address of PCF8574.
        _port (bytearray): Current port status buffer.
        _callback (callable): Optional callback function for external interrupt.
        _int_pin (Pin): Optional interrupt Pin instance.

    Methods:
        check() -> bool: Check if device exists.
        port() -> int: Get port status.
        port(value: int) -> None: Set port status.
        pin(pin: int, value: int = None) -> int: Read or write single pin.
        toggle(pin: int) -> None: Toggle a pin's value.

    Notes:
        - Not ISR-safe, use micropython.schedule when calling from ISR.
        - Supports MicroPython v1.23.0.
    """
    def __init__(self, i2c: I2C, address: int = 0x20,
                 int_pin: int = None,
                 callback: callable = None,
                 trigger: int = Pin.IRQ_FALLING) -> None:
        """
        初始化 PCF8574 实例。

        Args:
            i2c (I2C): I2C 总线对象。
            address (int, optional): I2C 地址，默认 0x20。
            int_pin (int, optional): INT 引脚编号。
            callback (callable, optional): 中断回调函数。

        Raises:
            TypeError: i2c 不是 I2C 或 callback 非可调用对象。
            ValueError: 地址不在 0x20~0x27 范围内。

        Notes:
            - 初始化不会触发 I2C 操作。
            - 中断回调将在 micropython.schedule 调度下执行。

        ==========================================

        Initialize PCF8574 instance.

        Args:
            i2c (I2C): I2C bus object.
            address (int, optional): I2C address, default 0x20.
            int_pin (int, optional): INT pin number.
            callback (callable, optional): Interrupt callback function.
            trigger (int, optional): Trigger type, default falling edge.

        Raises:
            TypeError: If i2c is not I2C or callback not callable.
            ValueError: If address not in 0x20~0x27.

        Notes:
            - Initialization does not perform I2C operations.
            - Callback is scheduled via micropython.schedule.
        """
        # 检查i2c是不是一个I2C对象
        if not isinstance(i2c, I2C):
            raise TypeError("I2C object required.")
        # 检查地址是否在0x20-0x27之间
        if not 0x20 <= address <= 0x27:
            raise ValueError("I2C address must be between 0x20 and 0x27.")

        # 保存 I2C 对象和设备地址
        self._i2c = i2c
        self._address = address
        self._port = bytearray(1)
        self._callback = callback

        # 如果用户指定了 INT 引脚和回调函数，则进行中断配置
        if int_pin is not None and callback is not None:
            # 检查 int_pin 是不是引脚编号
            if not isinstance(int_pin, int):
                raise TypeError("Pin number required.")

            # 检查callback是不是一个函数
            if not callable(callback):
                raise TypeError("Callback function required.")
            # 将指定的引脚设置为输入并启用内部上拉，以检测开漏信号
            # 端口状态发生变化时，将触发中断，调用回调函数
            pin = Pin(int_pin, Pin.IN, Pin.PULL_UP)

            # 定义中断处理器：此函数在中断上下文中运行，应尽量简短
            def _int_handler(p):
                # 调度用户回调，读取端口状态并触发回调
                micropython.schedule(self._scheduled_handler, None)

            # 保存中断引脚对象，防止被垃圾回收
            self._int_pin = pin
            # 注册中断：当 INT 引脚出现下降沿时触发 _int_handler
            self._int_pin.irq(trigger=trigger, handler=_int_handler)

    def _scheduled_handler(self, _: None) -> None:
        """
        调度执行用户回调函数。

        Args:
            _ (None): 占位参数，无实际意义。

        Notes:
            - 在 micropython.schedule 调度下执行，非 ISR-safe。
            - 回调函数接收当前 port 状态。

        ==========================================

        Scheduled handler to call user callback.

        Args:
            _ (None): Placeholder argument.

        Notes:
            - Executed under micropython.schedule, not ISR-safe.
            - Callback receives current port state.
        """
        # 读取当前端口值，清除中断标志
        self._read()
        # 调用用户回调，只传入端口值
        try:
            self._callback(self.port)
        except Exception as e:
            # 避免在调度中抛异常
            print("PCF8574 callback error:", e)

    def check(self) -> bool:
        """
        检查 PCF8574 是否存在于 I2C 总线上。

        Returns:
            bool: 如果设备存在返回 True。

        Raises:
            OSError: 设备未找到。

        Notes:
            - 会进行 I2C 扫描操作，非 ISR-safe。

        ==========================================

        Check if PCF8574 is present on I2C bus.

        Returns:
            bool: True if device exists.

        Raises:
            OSError: Device not found.

        Notes:
            - Performs I2C scan, not ISR-safe.
        """
        # 检查 PCF8574 是否连接在指定的 I2C 地址上
        if self._i2c.scan().count(self._address) == 0:
            raise OSError(f"PCF8574 not found at I2C address {self._address:#x}")
        return True

    @property
    def port(self) -> int:
        """
        获取整个 8 位端口状态。

        Returns:
            int: 当前 8 位端口状态。

        Notes:
            - 会主动读取 I2C 状态，非 ISR-safe。

        ==========================================

        Get current 8-bit port state.

        Returns:
            int: Current port state.

        Notes:
            - Performs I2C read, not ISR-safe.
        """
        # 主动读取，确保最新状态
        self._read()
        # 返回单字节整数值
        return self._port[0]

    @port.setter
    def port(self, value: int) -> None:
        """
        设置整个 8 位端口状态。

        Args:
            value (int): 端口新状态，仅低 8 位有效。

        Notes:
            - 会写入 I2C 总线，非 ISR-safe。

        ==========================================

        Set entire 8-bit port state.

        Args:
            value (int): New port state (only low 8 bits used).

        Notes:
            - Performs I2C write, not ISR-safe.
        """
        # 屏蔽高位，只保留低 8 位
        self._port[0] = value & 0xFF
        # 将新状态写入设备
        self._write()

    def pin(self, pin: int, value: int = None) -> int:
        """
        读取或设置指定引脚状态。

        Args:
            pin (int): 引脚编号 0~7。
            value (int, optional): 设置引脚状态，0=低，1=高。默认为 None 读取。

        Returns:
            int: 读取时返回。当前引脚状态；写入时返回 None

        Raises:
            ValueError: 引脚编号不合法。
            OSError: I2C 写操作失败。

        Notes:
            - I2C 操作非 ISR-safe。

        ==========================================

        Read or set individual pin state.

        Args:
            pin (int): Pin number 0~7.
            value (int, optional): Set pin state (0=Low, 1=High). None to read.

        Returns:
            int: Pin state when reading; None when writing.

        Raises:
            ValueError: Invalid pin number.
            OSError: I2C write failed.

        Notes:
            - I2C operations are not ISR-safe.
        """
        # 校验引脚范围
        pin = self._validate_pin(pin)
        if value is None:
            # 刷新端口状态
            self._read()
            return (self._port[0] >> pin) & 1
        # 更新端口寄存器对应位
        if value:
            self._port[0] |= 1 << pin
        else:
            self._port[0] &= ~(1 << pin)
        # 写回设备
        self._write()

    def toggle(self, pin: int) -> None:
        """
        翻转指定引脚状态。

        Args:
            pin (int): 引脚编号 0~7。

        Raises:
            ValueError: 引脚编号不合法。
            OSError: I2C 写操作失败。

        Notes:
            - I2C 操作非 ISR-safe。

        ==========================================

        Toggle the state of a pin.

        Args:
            pin (int): Pin number 0~7.

        Raises:
            ValueError: Invalid pin number.
            OSError: I2C write failed.

        Notes:
            - I2C operations are not ISR-safe.
        """
        # 校验引脚范围
        pin = self._validate_pin(pin)
        # 位异或实现翻转
        self._port[0] ^= 1 << pin
        self._write()

    def _validate_pin(self, pin: int) -> int:
        """
        校验引脚编号是否合法。

        Args:
            pin (int): 引脚编号。

        Returns:
            int: 合法的引脚编号。

        Raises:
            ValueError: 如果引脚编号不在 0~7 范围。

        Notes:
            - 仅进行编号检查，不涉及 I2C 操作。

        ==========================================

        Validate pin number.

        Args:
            pin (int): Pin number.

        Returns:
            int: Validated pin number.

        Raises:
            ValueError: If pin not in 0~7.

        Notes:
            - Only checks pin number, no I2C operation.
        """
        #  校验引脚编号是否在 0-7 范围。
        if not 0 <= pin <= 7:
            raise ValueError(f"Invalid pin {pin}. Use 0-7.")
        return pin

    def _read(self) -> None:
        """
        从 PCF8574 读取端口状态。

        Notes:
            - 执行 I2C 读取操作，非 ISR-safe。

        ==========================================

        Read port state from PCF8574.

        Notes:
            - Performs I2C read, not ISR-safe.
        """
        self._i2c.readfrom_into(self._address, self._port)

    def _write(self) -> None:
        """
        将端口状态写入 PCF8574。

        Notes:
            - 执行 I2C 写操作，非 ISR-safe。

        ==========================================

        Write port state to PCF8574.

        Notes:
            - Performs I2C write, not ISR-safe.
        """
        self._i2c.writeto(self._address, self._port)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
