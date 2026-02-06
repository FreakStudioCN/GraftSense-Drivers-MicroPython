# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/9/25 上午8:18   
# @Author  : 李清水            
# @File    : pcf8575.py
# @Description : 自定义PCF8575类，通过I2C总线操作
# 参考代码：https://github.com/mcauser/micropython-pcf8575

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PCF8575:
    """
    PCF8575类，用于通过I2C总线操作PCF8575芯片，实现控制16个GPIO引脚。

    该类封装了对PCF8575芯片的I2C通信，提供了设置和读取端口状态、操作单独引脚、翻转引脚等功能。
    另外，支持通过外部中断引脚进行事件触发，并能够注册回调函数处理触发事件。

    Attributes:
        i2c (I2C): I2C实例，用于与PCF8575进行通信。
        address (int): I2C设备地址，默认值为0x20。
        interrupt_pin (Pin): 可选的中断引脚实例，用于触发外部中断。
        callback (callable): 可选的回调函数，当中断触发时调用。

    Methods:
        __init__(self, i2c, address=0x20, interrupt_pin=None, callback=None):
            初始化 PCF8575 类实例。

        check(self):
            检查 PCF8575 是否在 I2C 总线上。

        port(self):
            获取端口的当前状态。

        port(self, value):
            设置端口的状态。

        pin(self, pin, value=None):
            获取或设置指定引脚的状态。

        toggle(self, pin):
            翻转指定引脚的高低电平。

        _validate_pin(self, pin):
            验证引脚编号的有效性。

        _read(self):
            从 I2C 读取端口状态。

        _write(self):
            将端口状态写入 I2C。

        _interrupt_handler(self, pin):
            中断处理函数，当外部中断引脚触发时调用回调函数。
    """

    def __init__(self, i2c: I2C, address: int = 0x20, interrupt_pin: Pin = None, callback: callable = None):
        """
        初始化 PCF8575 类实例。

        此方法初始化 I2C 总线，设置设备的地址，初始化端口状态，并配置中断引脚和回调函数（如果提供）。

        Args:
            i2c (I2C): I2C 实例，用于与 PCF8575 进行通信。
            address (int): I2C 地址，默认值为 0x20，表示设备的地址。
            interrupt_pin (Pin): 中断引脚实例，用于触发外部中断。当中断引脚状态发生变化时，触发中断并调用回调函数。
            callback (callable): 可选的回调函数，当外部中断引脚发生变化时调用。
        """
        # 保存 I2C 实例
        self._i2c = i2c
        # 保存 I2C 地址
        self._address = address
        # 初始化端口数据为 2 字节的字节数组
        self._port = bytearray(2)

        # 保存中断引脚和回调函数
        self.interrupt_pin = interrupt_pin
        self.callback = callback

        # 如果提供了中断引脚，设置引脚为输入、内部上拉并添加下降沿中断处理
        if self.interrupt_pin:
            self.interrupt_pin.init(Pin.IN, Pin.PULL_UP)
            self.interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._interrupt_handler)

    def check(self) -> bool:
        """
        检查 PCF8575 是否在 I2C 总线上。

        Args:
            None

        Returns:
            bool: 如果设备存在，返回 True；否则，抛出 OSError 异常。

        Raises:
            OSError: 如果设备未在 I2C 总线上找到。
        """
        # 检查设备是否存在
        if self._i2c.scan().count(self._address) == 0:
            # 抛出错误
            raise OSError(f"PCF8575 not found at I2C address {self._address:#x}")
        return True

    @property
    def port(self) -> int:
        """
        获取端口的当前状态。

        Args:
            None

        Returns:
            int: 端口状态的整数值。
        """
        # 读取当前端口状态
        self._read()
        # 返回合并后的端口值
        return self._port[0] | (self._port[1] << 8)

    @port.setter
    def port(self, value: int) -> None:
        """
        设置端口的状态。

        Args:
            value (int): 要设置的端口状态（一次性设置16个引脚）。

        Returns:
            None
        """
        # 设置低八个引脚状态
        self._port[0] = value & 0xFF
        # 设置高八个引脚状态
        self._port[1] = (value >> 8) & 0xFF
        # 写入新的端口状态
        self._write()

    def pin(self, pin: int, value: bool = None) -> int:
        """
        获取或设置指定引脚的状态。

        Args:
            pin (int): 引脚编号（0-7 或 10-17）。
            value (bool): 设置引脚状态（True 为高，False 为低）。如果为 None，则获取引脚状态。

        Returns:
            int: 如果 `value` 为 None，返回引脚的当前状态；否则，返回 None。
        """
        # 验证引脚编号
        pin = self._validate_pin(pin)

        # 如果 value 为 None，返回引脚当前状态
        if value is None:
            # 读取端口状态
            self._read()
            # 返回引脚状态
            # pin // 8 计算所在的字节索引，pin % 8 计算引脚在字节中的位置
            # 用 & 1 获取引脚的高低电平
            return (self._port[pin // 8] >> (pin % 8)) & 1

        # 设置引脚状态
        if value:
            # 设置引脚为高
            self._port[pin // 8] |= 1 << (pin % 8)
        else:
            # 设置引脚为低
            self._port[pin // 8] &= ~(1 << (pin % 8))
            # 写入新的端口状态
        self._write()

    def toggle(self, pin: int) -> None:
        """
        翻转指定引脚的高低电平。

        Args:
            pin (int): 引脚编号（0-7 或 10-17）。

        Returns:
            None
        """
        # 验证引脚编号
        pin = self._validate_pin(pin)
        # 切换引脚状态
        self._port[pin // 8] ^= 1 << (pin % 8)
        # 写入新的端口状态
        self._write()

    def _validate_pin(self, pin: int) -> int:
        """
        验证引脚编号的有效性。

        Args:
            pin (int): 引脚编号。

        Returns:
            int: 有效的引脚编号。

        Raises:
            ValueError: 如果引脚编号无效。
        """

        # pin 有效范围 0..7 和 10-17 (偏移到 8-15)
        # 第一位：端口 (0-1)
        # 第二位：IO (0-7)
        if not 0 <= pin <= 7 and not 10 <= pin <= 17:
            # 抛出错误
            raise ValueError(f"Invalid pin {pin}. Use 0-7 or 10-17.")

        # 调整引脚编号，当引脚编号大于等于 10 时，减去 2
        if pin >= 10:
            pin -= 2

        # 返回有效引脚编号
        return pin

    def _read(self) -> None:
        """
        从 I2C 读取端口状态。

        Args:
            None

        Returns:
            None
        """
        # 从 I2C 读取数据到端口
        self._i2c.readfrom_into(self._address, self._port)

    def _write(self) -> None:
        """
        将端口状态写入 I2C。

        Args:
            None

        Returns:
            None
        """
        # 将端口数据写入 I2C
        self._i2c.writeto(self._address, self._port)

    def _interrupt_handler(self, pin: Pin) -> None:
        """
        中断处理函数，当外部中断引脚触发时调用回调函数。

        Args:
            pin (Pin): 触发中断的引脚。

        Returns:
            None
        """
        if self.callback:
            self.callback(pin)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================