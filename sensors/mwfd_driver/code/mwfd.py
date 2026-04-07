# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午2:30
# @Author  : hogeiha
# @File    : mwfd.py
# @Description : MWFD水流气泡探测器Pico专用驱动，支持状态读取和中断配置
# @License : MIT
__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class MWFD:
    """
    MWFD水流气泡探测器 Pico 专用驱动
    中文简介
    Attributes:
        _pin (Pin): 输入的Pin对象，用于读取传感器电平
        _irq (Optional[任何]): 中断对象，存储中断配置信息
        _callback (Optional[可调用对象]): 用户注册的中断回调函数

    Methods:
        read(): 读取传感器状态，返回布尔值
        irq(): 设置或关闭中断，支持自定义回调与触发方式

    Notes:
        传入的Pin实例必须已初始化为输入模式。
        中断回调函数会接收一个布尔参数表示传感器状态。

    ==========================================
    English description
    Attributes:
        _pin (Pin): Input Pin object for reading sensor level
        _irq (Optional[Any]): IRQ object storing interrupt configuration
        _callback (Optional[Callable]): User registered interrupt callback

    Methods:
        read(): Read sensor status and return a boolean
        irq(): Enable or disable interrupt with custom callback and trigger

    Notes:
        The passed Pin instance must already be initialized as input.
        The interrupt callback will receive a boolean argument indicating sensor status.
    """

    def __init__(self, input_pin: Pin) -> None:
        """
        初始化驱动
        中文简介
        Args:
            input_pin (Pin): 已配置为输入模式的 Pin 实例

        Raises:
            TypeError: 传入参数类型不是 Pin 类型
            ValueError: 传入参数为 None

        Notes:
            无

        ==========================================
        English description
        Args:
            input_pin (Pin): Pin instance already configured as input

        Raises:
            TypeError: The argument is not of Pin type
            ValueError: The argument is None

        Notes:
            None
        """
        # 显式检查 None 参数
        if input_pin is None:
            raise ValueError("input_pin cannot be None")
        # 校验参数类型
        if not isinstance(input_pin, Pin):
            raise TypeError("must pass machine.Pin type instance")

        self._pin: Pin = input_pin
        self._irq = None
        self._callback = None

    def read(self) -> bool:
        """
        读取传感器状态
        中文简介
        Args:
            无

        Returns:
            bool: True=气泡/缺液 | False=正常液体

        Notes:
            无

        ==========================================
        English description
        Args:
            None

        Returns:
            bool: True=bubble/lack of liquid | False=normal liquid

        Notes:
            None
        """
        return self._pin.value() == 1

    def irq(self, callback=None, trigger: int = Pin.IRQ_RISING | Pin.IRQ_FALLING) -> None:
        """
        设置或关闭中断
        中文简介
        Args:
            callback (可选可调用对象): 状态变化回调函数，传 None 则关闭中断
            trigger (int): 触发方式，默认双边沿触发 (Pin.IRQ_RISING | Pin.IRQ_FALLING)

        Returns:
            None

        Notes:
            回调函数会接收一个布尔参数（传感器状态）。
            关闭中断时只需将 callback 设为 None。

        ==========================================
        English description
        Args:
            callback (Optional[Callable]): Status change callback, set None to disable interrupt
            trigger (int): Trigger mode, default both edges (Pin.IRQ_RISING | Pin.IRQ_FALLING)

        Returns:
            None

        Notes:
            The callback will receive a boolean argument (sensor status).
            To disable interrupt, simply set callback to None.
        """
        # 关闭原有中断
        if self._irq:
            self._irq.disable()
            self._irq = None

        # 无回调 = 关闭中断
        if callback is None:
            self._callback = None
            return

        # 绑定中断
        self._callback = callback

        def _handler(pin) -> None:
            self._callback(self.read())

        self._irq = self._pin.irq(trigger=trigger, handler=_handler)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
