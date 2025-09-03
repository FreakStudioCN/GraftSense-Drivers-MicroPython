# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : ben0i0d
# @File    : e11encoder.py
# @Description : ec11encoder驱动代码

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, Timer

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class EC11Encoder:
    """
    EC11Encoder 类，用于处理 EC11 旋转编码器的信号。6
    该类通过 GPIO 引脚读取旋转编码器的 A 相、B 相信号以及按键信号，
    支持旋转方向检测和按键状态判断。通过定时器消抖确保信号稳定，
    并提供旋转计数和按键状态查询功能。

    Attributes: 
        pin_a (Pin): A 相信号的 GPIO 引脚实例。
        pin_b (Pin): B 相信号的 GPIO 引脚实例。
        pin_btn (Pin): 按键信号的 GPIO 引脚实例。
        rotation_count (int): 旋转计数器，正值表示顺时针，负值表示逆时针。
        button_pressed (bool): 按键状态，True 表示被按下，False 表示未按下。
        debounce_timer_a (Timer): A 相信号的消抖定时器实例。
        debounce_timer_btn (Timer): 按键信号的消抖定时器实例。
        debouncing_a (bool): A 相信号的消抖状态标志。
        debouncing_btn (bool): 按键信号的消抖状态标志。

    Methods:
        __init__(pin_a: int, pin_b: int, pin_btn: int) -> None: 初始化旋转编码器。
        _handle_rotation(pin: Pin) -> None: A 相中断回调，检测方向。
        _check_debounce_a(t: Timer) -> None: A 相消抖处理。
        _handle_button(pin: Pin) -> None: 按键中断回调。
        _check_debounce_btn(t: Timer) -> None: 按键消抖处理。
        get_rotation_count() -> int: 获取旋转计数值。
        reset_rotation_count() -> None: 重置旋转计数器。
        is_button_pressed() -> bool: 获取按键状态。

    Notes:
        - A 相通过上升沿触发中断，结合 B 相电平判断旋转方向。
        - 按键使用下降沿和上升沿触发中断，结合消抖定时器判断状态。
        - 按键按下时会自动清零旋转计数值。
        - 消抖延迟：A 相为 1ms，按键为 5ms。

    ==========================================

    EC11Encoder class for handling signals from an EC11 rotary encoder.

    This class reads encoder signals from GPIO pins (phase A, phase B, and button),
    supports direction detection and button state recognition. Debouncing is applied
    via timers to ensure stable signals. Provides rotation counting and button state queries.

    Attributes:
        pin_a (Pin): GPIO pin instance for phase A signal.
        pin_b (Pin): GPIO pin instance for phase B signal.
        pin_btn (Pin): GPIO pin instance for button signal.
        rotation_count (int): Rotation counter (positive = clockwise, negative = counter-clockwise).
        button_pressed (bool): Button state (True = pressed, False = released).
        debounce_timer_a (Timer): Debounce timer for phase A.
        debounce_timer_btn (Timer): Debounce timer for button input.
        debouncing_a (bool): Debounce flag for phase A.
        debouncing_btn (bool): Debounce flag for button.

    Methods:
        __init__(pin_a: int, pin_b: int, pin_btn: int) -> None: Initialize encoder.
        _handle_rotation(pin: Pin) -> None: Interrupt handler for phase A, detects rotation direction.
        _check_debounce_a(t: Timer) -> None: Debounce handler for phase A.
        _handle_button(pin: Pin) -> None: Interrupt handler for button press/release.
        _check_debounce_btn(t: Timer) -> None: Debounce handler for button.
        get_rotation_count() -> int: Get current rotation count.
        reset_rotation_count() -> None: Reset rotation counter to zero.
        is_button_pressed() -> bool: Get button state.

    Notes:
        - Phase A triggers interrupt on rising edge; phase B level determines rotation direction.
        - Button triggers interrupt on both falling and rising edges, debounced with a timer.
        - Rotation counter is automatically reset when the button is pressed.
        - Debounce delay: 1ms for phase A, 5ms for button.
    """

    def __init__(self, pin_a: int, pin_b: int, pin_btn: int) -> None:
        """
        初始化 EC11 旋转编码器类。

        Args:
            pin_a (int): A 相信号的 GPIO 引脚编号。
            pin_b (int): B 相信号的 GPIO 引脚编号。
            pin_btn (int): 按键信号的 GPIO 引脚编号。

        ==========================================

        Initialize EC11 rotary encoder.

        Args:
            pin_a (int): GPIO pin number for phase A signal.
            pin_b (int): GPIO pin number for phase B signal.
            pin_btn (int): GPIO pin number for button signal.
        """
        # 初始化A相和B相的GPIO引脚，设置为输入模式
        self.pin_a = Pin(pin_a, Pin.IN)
        self.pin_b = Pin(pin_b, Pin.IN)
        # 初始化按键引脚，设置为输入模式，并启用内部上拉电阻
        self.pin_btn = Pin(pin_btn, Pin.IN, Pin.PULL_UP)

        # 初始化计数器，用于记录旋转的步数
        self.rotation_count = 0
        # 按键状态，用于记录按键是否被按下
        self.button_pressed = False

        # 消抖相关：定时器
        # A相消抖定时器
        self.debounce_timer_a   = Timer(-1)
        # 按键消抖定时器
        self.debounce_timer_btn = Timer(-1)

        # 标记是否在进行消抖处理
        # A相消抖标志
        self.debouncing_a = False
        # 按键消抖标志
        self.debouncing_btn = False

        # 为A相引脚设置中断处理，只检测上升沿（避免重复计数）
        self.pin_a.irq(trigger=Pin.IRQ_RISING, handler=self._handle_rotation)
        # 为按键引脚设置中断处理，检测按键的按下（下降沿）和释放（上升沿）
        self.pin_btn.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_button)

    def _handle_rotation(self, pin: Pin) -> None:
        """
        中断回调函数，用于检测 A 相的上升沿并根据 B 相状态判断方向。

        Args:
            pin (Pin): 触发中断的 A 相引脚对象。

        Returns:
            None

        ==========================================

        Interrupt callback for handling phase A rising edge 
        and determining rotation direction using phase B state.

        Args:
            pin (Pin): Phase A pin object that triggered the interrupt.

        Returns:
            None
        """
        # 如果正在消抖中，直接返回
        if self.debouncing_a:
            return

        # 启动消抖定时器，延迟1ms后执行判断
        self.debouncing_a = True
        self.debounce_timer_a.init(mode=Timer.ONE_SHOT, period=1, callback=self._check_debounce_a)

    def _check_debounce_a(self, t: Timer) -> None:
        """
        消抖定时器回调函数，检测 A 相是否稳定在高电平，并更新旋转计数。

        Args:
            t (Timer): 触发回调的定时器实例。

        Returns:
            None

        ==========================================

        Debounce timer callback for phase A.  
        Checks if phase A is stable HIGH and updates rotation count.

        Args:
            t (Timer): Timer instance that triggered the callback.

        Returns:
            None
        """
        # 1ms后A相仍然为高电平，确认有效
        if self.pin_a.value() == 1:
            # 获取B相当前的状态（高或低电平）
            current_state_b = self.pin_b.value()

            # A相上升沿时，判断B相的状态决定旋转方向
            if current_state_b == 0:
                # 顺时针旋转，计数器加1
                self.rotation_count += 1
            else:
                # 逆时针旋转，计数器减1
                self.rotation_count -= 1

        # 重置消抖状态
        self.debouncing_a = False

    def _handle_button(self, pin: Pin) -> None:
        """
        中断回调函数，用于检测按键的按下和释放，启动消抖。

        Args:
            pin (Pin): 触发中断的按键引脚对象。

        Returns:
            None

        ==========================================

        Interrupt callback for button press/release, 
        starts debounce timer.

        Args:
            pin (Pin): Button pin object that triggered the interrupt.

        Returns:
            None
        """
        # 如果正在消抖中，直接返回
        if self.debouncing_btn:
            return

        # 启动消抖定时器，延迟5ms后执行判断
        self.debouncing_btn = True
        self.debounce_timer_btn.init(mode=Timer.ONE_SHOT, period=5, callback=self._check_debounce_btn)

    def _check_debounce_btn(self, t: Timer) -> None:
        """
        按键消抖定时器回调函数，判断按键状态并更新标志。

        Args:
            t (Timer): 触发回调的定时器实例。

        Returns:
            None

        ==========================================

        Debounce timer callback for button.  
        Determines button state and updates the status flag.

        Args:
            t (Timer): Timer instance that triggered the callback.

        Returns:
            None
        """
        if self.pin_btn.value() == 0:
            # 按键按下，更新状态
            self.button_pressed = True
        else:
            # 按键释放，更新状态
            self.button_pressed = False

        # 旋转编码器计数值清零
        self.reset_rotation_count()
        # 重置消抖状态
        self.debouncing_btn = False

    def get_rotation_count(self) -> int:
        """
        获取旋转的总次数（正值表示顺时针，负值表示逆时针）。

        Returns:
            int: 当前旋转的计数值。
        ==========================================

        Get total rotation count (positive = clockwise, negative = counter-clockwise).

        Returns:
            int: Current rotation count.
        """
        return self.rotation_count

    def reset_rotation_count(self) -> None:
        """
        重置旋转计数器，将旋转步数清零。

        Args:
            None

        Returns:
            None
        """
        self.rotation_count = 0

    def is_button_pressed(self) -> bool:
        """
        返回按键是否被按下的状态。

        Returns:
            bool: True 表示按键被按下，False 表示未按下。

        ==========================================

        Get button pressed state.

        Returns:
            bool: True if button is pressed, False otherwise.
        """
        return self.button_pressed

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================