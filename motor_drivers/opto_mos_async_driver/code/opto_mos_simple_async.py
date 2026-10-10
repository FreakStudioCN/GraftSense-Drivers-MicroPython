# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/15
# @Author  : 缪贵成
# @File    : opto_mos_simple_async.py
# @Description : 异步适配的光耦 MOS PWM 驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================


class OptoMosSimpleAsync:
    """Adapter retaining the source PWM duty and inversion semantics."""

    def __init__(self, pwm, pwm_max=65535, inverted=False):
        if pwm is None or not hasattr(pwm, "duty_u16"):
            raise ValueError("pwm must provide duty_u16")
        if pwm_max <= 0:
            raise ValueError("pwm_max must be positive")
        self.pwm = pwm
        self.pwm_max = pwm_max
        self.inverted = inverted
        self._duty = 0

    def init(self):
        self.set_duty(0)

    def set_duty(self, duty):
        duty = max(0, min(duty, self.pwm_max))
        if self.inverted:
            duty = self.pwm_max - duty
        self._duty = duty
        self.pwm.duty_u16(duty)

    def set_percent(self, percent):
        percent = max(0.0, min(percent, 100.0))
        self.set_duty(int(percent / 100.0 * self.pwm_max))

    def full_on(self):
        self.set_duty(self.pwm_max)

    def off(self):
        self.set_duty(0)

    def get_status(self):
        return {"duty": self._duty, "percent": self._duty / self.pwm_max * 100.0,
                "pwm_max": self.pwm_max, "inverted": self.inverted}

    async def init_async(self):
        self.init()

    async def set_duty_async(self, duty):
        self.set_duty(duty)

    async def set_percent_async(self, percent):
        self.set_percent(percent)

    async def full_on_async(self):
        self.full_on()

    async def off_async(self):
        self.off()

    async def get_status_async(self):
        return self.get_status()

    def deinit(self):
        try:
            self.pwm.deinit()
        except AttributeError:
            self.off()

    async def aclose(self):
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
