# Python env   :               
# -*- coding: utf-8 -*-        
# @Time    : 2025/7/3 下午4:58   
# @Author  : 李清水            
# @File    : PCF8574.py       
# @Description : 参考代码为https://github.com/mcauser/micropython-pcf8574/blob/master/src/pcf8574.py

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
    PCF8574类，用于通过I2C总线操作PCF8574芯片，实现控制8个GPIO引脚。
    该类封装了对PCF8574芯片的I2C通信，提供了设置和读取端口状态、操作单独引脚、翻转引脚等功能。
    另外，支持通过外部中断引脚进行事件触发，并能够注册回调函数处理触发事件。

    Attributes:
        i2c (I2C): I2C实例，用于与PCF8574进行通信。
        address (int): I2C设备地址，默认值为0x20，范围0x20~0x27。
        _port (bytearray): 用于存储当前端口状态的缓存。
        _callback (callable): 可选的回调函数，当中断触发时调用。
        _int_pin (Pin): 可选的中断引脚实例，用于触发外部中断。

    Methods:
        __init__(...): 初始化 PCF8574 类实例。
        check(): 检查 PCF8574 是否在 I2C 总线上。
        port: 属性，用于读取或设置8位端口状态。
        pin(pin, value=None): 获取或设置指定引脚的状态。
        toggle(pin): 翻转指定引脚的高低电平。
        _validate_pin(pin): 验证引脚编号的有效性。
        _read(): 从 I2C 读取端口状态。
        _write(): 将端口状态写入 I2C。
        _scheduled_handler(_): 间接处理中断时执行用户回调。
    """
    def __init__(self, i2c: I2C, address: int = 0x20,
                 int_pin: int = None,
                 callback: callable = None,
                 trigger: int = Pin.IRQ_FALLING) -> None:
        """
        初始化 PCF8574 实例。

        Args:
            i2c (I2C): I2C 总线对象。
            address (int, optional): I2C 地址，默认 0x20，范围为 0x20~0x27。
            int_pin (int, optional): INT 引脚编号。
            callback (callable, optional): 外部中断触发时调用的回调函数。
            trigger (int, optional): 中断触发类型，默认为下降沿触发。

        Raises:
            TypeError: 如果 i2c 不是 I2C 类型或 callback 不是函数。
            ValueError: 如果 address 不在合法范围内。
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
        实际回调执行函数，由 micropython.schedule 调度执行。

        Args:
            _ (None): 无实际意义，仅作为占位符。

        Returns:
            None
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
        检查 PCF8574 是否在 I2C 总线上。

        Returns:
            bool: 如果设备存在，返回 True。

        Raises:
            OSError: 如果设备未在 I2C 总线上找到。
        """
        # 检查 PCF8574 是否连接在指定的 I2C 地址上
        if self._i2c.scan().count(self._address) == 0:
            raise OSError(f"PCF8574 not found at I2C address {self._address:#x}")
        return True

    @property
    def port(self) -> int:
        """
        获取当前端口值（读取引脚状态）。

        Returns:
            int: 当前 8 位端口状态。
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
        """
        # 屏蔽高位，只保留低 8 位
        self._port[0] = value & 0xFF
        # 将新状态写入设备
        self._write()

    def pin(self, pin: int, value: int = None) -> int:
        """
        读取或设置某一个引脚的状态。

        Args:
            pin (int): 引脚编号，范围 0~7。
            value (int, optional): 若提供，设置该引脚状态（0 或 1）。

        Returns:
            int: 若未提供 value，则返回当前引脚状态。

        Raises:
            ValueError: 如果 pin 超出范围。
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
        翻转指定引脚的当前状态。

        Args:
            pin (int): 引脚编号，范围 0~7。

        Returns:
            None

        Raises:
            ValueError: 如果 pin 超出范围。
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
            ValueError: 如果 pin 不在 0~7 范围内。
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
        """
        self._i2c.readfrom_into(self._address, self._port)

    def _write(self) -> None:
        """
        将当前端口状态写入 PCF8574。

        Returns:
            None
        """
        self._i2c.writeto(self._address, self._port)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================