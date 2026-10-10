# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 零高幸
# @File    : piranha_led_async.py
# @Description : 食人鱼 LED 的异步适配器
# @License : MIT

__version__ = "1.0.0"
__author__ = "零高幸"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================

from piranha_led import PiranhaLED

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class PiranhaLEDAsync(PiranhaLED):
    """
    食人鱼 LED 的显式异步适配器。
    Attributes:
        _pin (Pin): 来源驱动持有的 GPIO 对象。
    Methods:
        on_async(): 点亮 LED。
        off_async(): 熄灭 LED。
        aclose(): 释放资源。
    Notes:
        - GPIO value() 是短同步临界区，属于 sync_adapter_only。
    ==========================================
    Explicit asynchronous adapter for a Piranha LED.
    Attributes:
        _pin (Pin): GPIO object held by the source driver.
    Methods:
        on_async(): Turn on the LED.
        off_async(): Turn off the LED.
        aclose(): Release resources.
    Notes:
        - GPIO value() remains a short synchronous critical section.
    """

    async def on_async(self) -> None:
        """点亮 LED。\n\nTurn on the LED.\n\nNotes:\n    - ISR-safe: 否 / No."""
        self.on()

    async def off_async(self) -> None:
        """熄灭 LED。\n\nTurn off the LED.\n\nNotes:\n    - ISR-safe: 否 / No."""
        self.off()

    async def toggle_async(self) -> None:
        """切换 LED 状态。\n\nToggle the LED state.\n\nNotes:\n    - ISR-safe: 否 / No."""
        self.toggle()

    async def is_on_async(self) -> bool:
        """读取 LED 状态。\n\nRead the LED state.\n\nNotes:\n    - ISR-safe: 否 / No."""
        return self.is_on()

    async def aclose(self) -> None:
        """释放资源。\n\nRelease resources.\n\nNotes:\n    - ISR-safe: 否 / No."""
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================