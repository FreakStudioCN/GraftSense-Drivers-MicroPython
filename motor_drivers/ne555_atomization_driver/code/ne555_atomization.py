# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:20
# @Author  : 缪贵成
# @File    : atomization.py
# @Description : 基于NE555芯片的超声波雾化器驱动模块
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class Atomization:
    """
    该类控制基于 NE555 芯片的超声波雾化模块，通过 GPIO 引脚输出高低电平实现雾化器开关控制。

    Attributes:
        _pin (Pin): machine.Pin 实例，用于输出高低电平控制雾化器。
        _state (bool): 当前雾化模块的开关状态，True 表示开启，False 表示关闭。

    Methods:
        on() -> None: 打开雾化模块（输出高电平）。
        off() -> None: 关闭雾化模块（输出低电平）。
        toggle() -> None: 切换雾化模块状态（开->关 或 关->开）。
        is_on() -> bool: 返回当前雾化模块的状态。

    Notes:
        - 该类仅进行简单的 GPIO 控制，不涉及 PWM。
        - 在部分开发板上，雾化模块可能需要外部电源驱动，请注意电源供给。
        - GPIO 操作不是 ISR-safe，不要在中断服务程序中直接调用。

    ==========================================

    Driver class for NE555-based ultrasonic mist module.
    It controls the module by setting GPIO pin high or low.

    Attributes:
        _pin (Pin): machine.Pin instance used for digital output control.
        _state (bool): Current state of mist module. True = ON, False = OFF.

    Methods:
        on() -> None: Turn mist module ON (set pin high).
        off() -> None: Turn mist module OFF (set pin low).
        toggle() -> None: Toggle mist module state.
        is_on() -> bool: Return current ON/OFF state.

    Notes:
        - This driver only handles simple GPIO switching, no PWM.
        - External power supply may be required depending on the module.
        - GPIO operations are not ISR-safe.
    """

    def __init__(self, pin: int):
        """
        初始化雾化模块对象。

        Args:
            pin (int): 控制雾化器开关的 GPIO 引脚编号。

        Notes:
            - 初始化时会自动关闭雾化器。
            - 仅支持可配置为输出模式的 GPIO。

        ==========================================

        Initialize mist module object.

        Args:
            pin (int): GPIO pin number used to control mist module.

        Notes:
            - Module is set to OFF at initialization.
            - Pin must support output mode.
        """
        self._pin = Pin(pin, Pin.OUT)
        self._state = False
        self.off()

    def on(self):
        """
        打开雾化模块（输出高电平）。

        Notes:
            - 会更新内部状态为 True。
            - 非 ISR-safe。

        ==========================================

        Turn mist module ON (set pin high).

        Notes:
            - Updates internal state to True.
            - Not ISR-safe.
        """
        self._pin.value(1)
        self._state = True

    def off(self):
        """
        关闭雾化模块（输出低电平）。

        Notes:
            - 会更新内部状态为 False。
            - 非 ISR-safe。

        ==========================================

        Turn mist module OFF (set pin low).

        Notes:
            - Updates internal state to False.
            - Not ISR-safe.
        """
        self._pin.value(0)
        self._state = False

    def toggle(self):
        """
        切换雾化模块状态。

        Notes:
            - 如果当前为开，则关闭；如果当前为关，则打开。
            - 内部会调用 on() 或 off()。
            - 非 ISR-safe。

        ==========================================

        Toggle mist module state.

        Notes:
            - If currently ON, turn OFF; if OFF, turn ON.
            - Internally calls on() or off().
            - Not ISR-safe.
        """
        if self._state:
            self.off()
        else:
            self.on()

    def is_on(self) -> bool:
        """
        返回当前雾化模块状态。

        Returns:
            bool: True 表示开启，False 表示关闭。

        Notes:
            - 仅返回内部状态，不直接读取引脚电平。
            - 查询操作是安全的。

        ==========================================

        Return current mist module state.

        Returns:
            bool: True if ON, False if OFF.

        Notes:
            - Returns internal state only, not actual pin read.
            - Query operation is safe.
        """
        return self._state

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
