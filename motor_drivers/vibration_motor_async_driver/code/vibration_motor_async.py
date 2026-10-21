# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/15
# @Author  : 缪贵成
# @File    : vibration_motor_async.py
# @Description : 异步适配的震动马达驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

MAX_DUTY = 1023

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================


class VibrationMotorAsync:
    """Source-compatible vibration motor control with explicit short PWM writes."""

    def __init__(self, pwm):
        """Use a caller-owned, configured PWM instance."""
        self._pwm = pwm
        self._pwm.duty_u16(0)
        self._state = False

    def on(self):
        self._pwm.duty_u16(MAX_DUTY * 64)
        self._state = True

    def off(self):
        self._pwm.duty_u16(0)
        self._state = False

    def toggle(self):
        if self._state:
            self.off()
        else:
            self.on()

    def set_brightness(self, duty):
        if not 0 <= duty <= MAX_DUTY:
            raise ValueError("PWM duty must be 0-1023")
        self._pwm.duty_u16(duty * 64)

    def get_state(self):
        return self._state

    async def on_async(self):
        self.on()

    async def off_async(self):
        self.off()

    async def toggle_async(self):
        self.toggle()

    async def set_brightness_async(self, duty):
        self.set_brightness(duty)

    async def get_state_async(self):
        return self.get_state()

    @property
    def pwm(self):
        return self._pwm

    def deinit(self):
        self.off()

    async def aclose(self):
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
