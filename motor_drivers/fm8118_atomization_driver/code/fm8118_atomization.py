# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/12/23 上午11:20
# @Author  : leeqingshui
# @File    : fm8118_atomization.py
# @Description : 基于FM8118芯片的超声波雾化器驱动模块
# @License : MIT

__version__ = "0.1.1"
__author__ = "leeqingshui"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin

# 导入时间相关模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class FM8118_Atomization:
    """
    该类控制基于 FM8118 芯片的超声波雾化模块，通过 GPIO 引脚实现雾化器开关控制。

    Attributes:
        _pin (Pin): machine.Pin 实例，用于输出高低电平控制雾化器。
        _state (bool): 当前雾化模块的开关状态，True 表示开启，False 表示关闭。

    Methods:
        on() -> None: 打开雾化模块（输出低电平）。
        off() -> None: 关闭雾化模块（执行拉高→拉低→再拉高电平序列）。
        toggle() -> None: 切换雾化模块状态（开->关 或 关->开）。
        is_on() -> bool: 返回当前雾化模块的状态。

    Notes:
        - 该类仅进行简单的 GPIO 控制，不涉及 PWM。
        - 在部分开发板上，雾化模块可能需要外部电源驱动，请注意电源供给。
        - GPIO 操作不是 ISR-safe，不要在中断服务程序中直接调用。

    ==========================================

    Driver class for FM8118-based ultrasonic mist module.
    It controls the module by setting GPIO pin high/low or level sequence.

    Attributes:
        _pin (Pin): machine.Pin instance used for digital output control.
        _state (bool): Current state of mist module. True = ON, False = OFF.

    Methods:
        on() -> None: Turn mist module ON (set pin low).
        off() -> None: Turn mist module OFF (execute high→low→high level sequence).
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
            - 初始化时会将 GPIO 设置为高电平，雾化器处于关闭状态。
            - 仅支持可配置为输出模式的 GPIO。

        ==========================================

        Initialize mist module object.

        Args:
            pin (int): GPIO pin number used to control mist module.

        Notes:
            - Module is set to HIGH level (OFF state) at initialization.
            - Pin must support output mode.
        """
        self._pin = Pin(pin, Pin.OUT)
        # 初始状态为关闭
        self._state = False
        # 初始化时设置为高电平（关闭状态），移除原有的off()调用
        self._pin.value(1)

    def on(self):
        """
        打开雾化模块（输出低电平）。

        Notes:
            - 会更新内部状态为 True。
            - 非 ISR-safe。

        ==========================================

        Turn mist module ON (set pin low).

        Notes:
            - Updates internal state to True.
            - Not ISR-safe.
        """
        # 低电平开启
        self._pin.value(0)
        self._state = True

    def off(self):
        """
        关闭雾化模块（执行拉高→拉低→再拉高电平序列）。

        Notes:
            - 会更新内部状态为 False。
            - 电平切换时添加短暂延时，确保芯片识别电平变化。
            - 非 ISR-safe。

        ==========================================

        Turn mist module OFF (execute high→low→high level sequence).

        Notes:
            - Updates internal state to False.
            - Short delays are added for level transition recognition.
            - Not ISR-safe.
        """
        # 步骤1：拉高电平
        self._pin.value(1)
        # 延时100ms
        time.sleep_ms(100)
        # 步骤2：拉低电平
        self._pin.value(0)
        # 延时100ms
        time.sleep_ms(100)
        # 步骤3：再次拉高电平（最终保持高电平）
        self._pin.value(1)
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
