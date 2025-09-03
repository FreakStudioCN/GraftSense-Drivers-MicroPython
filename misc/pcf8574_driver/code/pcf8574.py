# Python env   :               
# -*- coding: utf-8 -*-        
# @Time    : 2025/7/3 下午4:58   
# @Author  : 李清水            
# @File    : PCF8574.py       
# @Description : 参考代码为https://github.com/mcauser/micropython-pcf8574/blob/master/src/pcf8574.py

__version__ = "0.1.0"
__author__ = "李清水"
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

class PCF8574:
    """
    PCF8574 I/O 扩展芯片 I2C 驱动类，用于扩展微控制器的 GPIO 引脚。

    该类通过 I2C 总线与 PCF8574 芯片通信，支持 8 位 GPIO 的输入与输出控制，
    并提供端口级和引脚级操作接口。可选支持外部中断引脚，用于检测引脚状态变化。

    Attributes:
        _i2c (I2C): I2C 总线对象。
        _address (int): 设备 I2C 地址，范围 0x20–0x27。
        _port (bytearray): 当前端口状态缓存（8 位）。
        _callback (callable): 可选，外部中断触发时执行的用户回调函数。
        _int_pin (Pin): 可选，中断引脚对象，用于硬件事件检测。

    Methods:
        __init__(i2c, address=0x20, int_pin=None, callback=None, trigger=Pin.IRQ_FALLING) -> None:
            初始化 PCF8574 实例，配置 I2C 地址、中断引脚及回调函数。
        check() -> bool:
            检测设备是否在 I2C 总线上响应。
        port (property):
            获取或设置整个 8 位端口的值。
        pin(pin: int, value: Optional[int] = None) -> int:
            读取或设置指定引脚的电平状态。
        toggle(pin: int) -> None:
            翻转指定引脚的当前状态。
        _validate_pin(pin: int) -> int:
            验证引脚编号是否合法（0–7）。
        _read() -> None:
            从设备读取端口状态并更新缓存。
        _write() -> None:
            将缓存中的端口状态写入设备。
        _scheduled_handler(_) -> None:
            在中断调度时调用用户定义的回调函数。

    Notes:
        - PCF8574 提供 8 位 GPIO，通过 I2C 控制。
        - 地址范围通常为 0x20–0x27，取决于 A0–A2 引脚配置。
        - 输出为开漏结构，需外接上拉电阻。
        - 可结合外部中断引脚实现事件驱动的 GPIO 检测。

    ==========================================

    PCF8574 I/O expander driver class for I2C communication.

    This class provides GPIO expansion via the PCF8574 chip, allowing control
    of 8 input/output pins over I2C. Supports port-wide and per-pin operations,
    with optional interrupt pin handling for event-driven applications.

    Attributes:
        _i2c (I2C): I2C bus object.
        _address (int): Device I2C address (0x20–0x27).
        _port (bytearray): Cached port state (8 bits).
        _callback (callable): Optional user callback triggered by external interrupt.
        _int_pin (Pin): Optional interrupt pin for hardware event detection.

    Methods:
        __init__(i2c, address=0x20, int_pin=None, callback=None, trigger=Pin.IRQ_FALLING) -> None:
            Initialize PCF8574 instance with I2C address, optional interrupt pin and callback.
        check() -> bool:
            Verify device presence on the I2C bus.
        port (property):
            Get or set the full 8-bit port value.
        pin(pin: int, value: Optional[int] = None) -> int:
            Read or set the state of a specific GPIO pin.
        toggle(pin: int) -> None:
            Toggle the state of a given GPIO pin.
        _validate_pin(pin: int) -> int:
            Ensure pin number is valid (0–7).
        _read() -> None:
            Read current port state from device into cache.
        _write() -> None:
            Write cached port state to device.
        _scheduled_handler(_) -> None:
            Dispatch user-defined callback during interrupt scheduling.

    Notes:
        - Provides 8 GPIO pins via I2C control.
        - Address range typically 0x20–0x27 (set by A0–A2).
        - Outputs are open-drain, external pull-up resistors required.
        - External interrupt pin enables event-driven GPIO monitoring.
    """

    def __init__(self, i2c: I2C, address: int = 0x20,
                 int_pin: int = None,
                 callback: callable = None,
                 trigger: int = Pin.IRQ_FALLING) -> None:
        """
        初始化 PCF8574 实例。

        Args:
            i2c (I2C): I2C 总线对象。
            address (int, optional): I2C 地址，默认 0x20，范围 0x20~0x27。
            int_pin (int, optional): INT 引脚编号。
            callback (callable, optional): 外部中断触发时调用的回调函数。
            trigger (int, optional): 中断触发类型，默认下降沿触发。

        Raises:
            TypeError: 如果 i2c 不是 I2C 类型，或 int_pin 不是整数，或 callback 不是函数。
            ValueError: 如果 address 超出范围 0x20~0x27。

        Notes:
            INT 引脚为开漏输出，需外部或内部上拉电阻。
            回调函数在调度上下文中运行，避免阻塞或长时间操作。

        ==========================================

        Initialize PCF8574 instance.

        Args:
            i2c (I2C): I2C bus object.
            address (int, optional): I2C address, default 0x20, valid 0x20~0x27.
            int_pin (int, optional): INT pin number.
            callback (callable, optional): Callback triggered on external interrupt.
            trigger (int, optional): Interrupt trigger type, default falling edge.

        Raises:
            TypeError: If i2c is not I2C, int_pin not int, or callback not callable.
            ValueError: If address out of 0x20~0x27 range.

        Notes:
            INT pin is open-drain, requires pull-up resistor.
            Callback runs in scheduled context, avoid blocking.
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
        执行用户回调，由 micropython.schedule 调度。

        Args:
            _ (None): 占位参数，无实际意义。

        Returns:
            None

        Notes:
            在调度上下文执行，安全性高于中断上下文。
            用户回调异常会被捕获并打印。

        ==========================================

        Execute user callback, scheduled by micropython.schedule.

        Args:
            _ (None): Placeholder argument, unused.

        Returns:
            None

        Notes:
            Runs in scheduled context, safer than IRQ context.
            User callback exceptions are caught and printed.
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
            bool: 如果设备存在，返回 True。

        Raises:
            OSError: 如果在指定地址未检测到设备。

        ==========================================

        Check whether PCF8574 is present on the I2C bus.

        Returns:
            bool: True if device found.

        Raises:
            OSError: If device not found at given address.
        """
        # 检查 PCF8574 是否连接在指定的 I2C 地址上
        if self._i2c.scan().count(self._address) == 0:
            raise OSError(f"PCF8574 not found at I2C address {self._address:#x}")
        return True

    @property
    def port(self) -> int:
        """
        获取当前端口值。

        Returns:
            int: 当前 8 位端口状态。

        ==========================================

        Get current port value.

        Returns:
            int: Current 8-bit port state.
        """
        # 主动读取，确保最新状态
        self._read()
        # 返回单字节整数值
        return self._port[0]

    @port.setter
    def port(self, value: int) -> None:
        """
        设置端口输出值。

        Args:
            value (int): 新的端口值，仅低 8 位有效。

        Returns:
            None

        ==========================================

        Set port output value.

        Args:
            value (int): New port value, only low 8 bits effective.

        Returns:
            None
        """
        # 屏蔽高位，只保留低 8 位
        self._port[0] = value & 0xFF
        # 将新状态写入设备
        self._write()

    def pin(self, pin: int, value: int = None) -> int:
        """
        读取或设置单个引脚状态。

        Args:
            pin (int): 引脚编号 0~7。
            value (int, optional): 若提供，则设置引脚状态（0/1）。

        Returns:
            int: 如果未提供 value，返回当前引脚状态。

        Raises:
            ValueError: 如果引脚超出 0~7。

        ==========================================

        Read or set single pin state.

        Args:
            pin (int): Pin index 0~7.
            value (int, optional): If given, set pin state (0/1).

        Returns:
            int: If value not given, return current pin state.

        Raises:
            ValueError: If pin out of range 0~7.
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
        翻转引脚状态。

        Args:
            pin (int): 引脚编号 0~7。

        Returns:
            None

        Raises:
            ValueError: 如果引脚超出范围。

        ==========================================

        Toggle pin state.

        Args:
            pin (int): Pin index 0~7.

        Returns:
            None

        Raises:
            ValueError: If pin out of range.
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
            ValueError: 如果引脚不在 0~7 范围。

        ==========================================

        Validate pin index.

        Args:
            pin (int): Pin index.

        Returns:
            int: Valid pin index.

        Raises:
            ValueError: If pin not in 0~7 range.
        """
        #  校验引脚编号是否在 0-7 范围。
        if not 0 <= pin <= 7:
            raise ValueError(f"Invalid pin {pin}. Use 0-7.")
        return pin

    def _read(self) -> None:
        """
        从 PCF8574 读取当前端口值。

        Returns:
            None

        ==========================================

        Read current port value from PCF8574.

        Returns:
            None
        """
        self._i2c.readfrom_into(self._address, self._port)

    def _write(self) -> None:
        """
        将当前端口值写入 PCF8574。

        Returns:
            None

        ==========================================

        Write current port value to PCF8574.

        Returns:
            None
        """
        self._i2c.writeto(self._address, self._port)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================