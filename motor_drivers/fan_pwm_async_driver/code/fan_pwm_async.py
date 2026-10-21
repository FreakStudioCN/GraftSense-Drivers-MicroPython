# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : fan_pwm_async.py
# @Description : 异步适配的 PWM 散热风扇驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================

from machine import Pin, PWM

# ======================================== 全局变量 ============================================

MAX_DUTY = 1023
PWM_MAX_DUTY_U16 = 65535
DEFAULT_PWM_FREQ = 25000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================


class FanPWMAsync:
    """异步 PWM 风扇适配器；硬件 PWM 写入保持为短同步操作。"""

    def __init__(self, pin: int, pwm_freq: int = DEFAULT_PWM_FREQ) -> None:
        """使用指定 GPIO 与 PWM 频率初始化风扇控制。"""
        self._pin = Pin(pin, Pin.OUT)
        self._pwm = PWM(self._pin)
        self._pwm.freq(pwm_freq)
        self._duty = 0
        self._pwm.duty_u16(0)

    def on(self) -> None:
        """以最大占空比启动风扇。"""
        self.set_speed(MAX_DUTY)

    def off(self) -> None:
        """将风扇占空比设为零。"""
        self.set_speed(0)

    def set_speed(self, duty: int) -> None:
        """设置并记录钳制到 0–1023 的 PWM 占空比。"""
        duty = max(0, min(MAX_DUTY, duty))
        self._duty = duty
        self._pwm.duty_u16(int(duty / MAX_DUTY * PWM_MAX_DUTY_U16))

    def get_speed(self) -> int:
        """返回软件记录的当前占空比。"""
        return self._duty

    async def on_async(self) -> None:
        """异步启动风扇。"""
        self.on()

    async def off_async(self) -> None:
        """异步关闭风扇。"""
        self.off()

    async def set_speed_async(self, duty: int) -> None:
        """异步设置风扇占空比。"""
        self.set_speed(duty)

    async def get_speed_async(self) -> int:
        """异步返回当前占空比。"""
        return self.get_speed()

    @property
    def digital(self) -> "Pin":
        """返回绑定的 PWM 控制引脚对象。"""
        return self._pin

    @property
    def pwm(self) -> "PWM":
        """返回底层 PWM 对象，供高级调用者使用。"""
        return self._pwm

    def deinit(self) -> None:
        """关闭风扇并释放 PWM 资源。"""
        self.off()
        try:
            self._pwm.deinit()
        except AttributeError:
            pass

    async def aclose(self) -> None:
        """异步释放 PWM 资源。"""
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================