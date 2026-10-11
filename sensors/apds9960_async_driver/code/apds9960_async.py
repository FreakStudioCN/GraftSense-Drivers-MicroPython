# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Rune Langøy
# @File    : apds9960_async.py
# @Description : Source-faithful APDS9960 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from apds9960 import I2CEX, ALS, PROX, APDS9960

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class _AsyncCloseMixin:
    async def deinit_async(self):
        self.deinit()
        await asyncio.sleep_ms(0)

    async def aclose(self):
        await self.deinit_async()

class I2CEXAsync(_AsyncCloseMixin, I2CEX):
    pass

class ALSAsync(_AsyncCloseMixin, ALS):
    async def enable_sensor_async(self, on=True): return self.enableSensor(on)
    async def get_light_gain_async(self): return self.eLightGain
    async def set_light_gain_async(self, gain): self.eLightGain = gain
    async def ambient_light_level_async(self): return self.ambientLightLevel
    async def red_light_level_async(self): return self.redLightLevel
    async def green_light_level_async(self): return self.greenLightLevel
    async def blue_light_level_async(self): return self.blueLightLevel
    async def set_interrupt_threshold_async(self, high=0, low=20, persistance=4): return self.setInterruptThreshold(high, low, persistance)
    async def clear_interrupt_async(self): return self.clearInterrupt()
    async def enable_interrupt_async(self, on=True): return self.enableInterrupt(on)

class PROXAsync(_AsyncCloseMixin, PROX):
    async def enable_sensor_async(self, on=True): return self.enableSensor(on)
    async def set_interrupt_threshold_async(self, high=0, low=20, persistance=4): return self.setInterruptThreshold(high, low, persistance)
    async def clear_interrupt_async(self): return self.clearInterrupt()
    async def enable_interrupt_async(self, on=True): return self.enableInterrupt(on)
    async def get_proximity_gain_async(self): return self.eProximityGain
    async def set_proximity_gain_async(self, gain): self.eProximityGain = gain
    async def get_led_current_async(self): return self.eLEDCurrent
    async def set_led_current_async(self, current): self.eLEDCurrent = current
    async def proximity_level_async(self): return self.proximityLevel

class APDS9960Async(_AsyncCloseMixin, APDS9960):
    async def power_on_async(self, on=True): return self.powerOn(on)
    async def status_register_async(self): return self.statusRegister
    async def deinit_async(self):
        self.deinit()
        await asyncio.sleep_ms(0)
    async def aclose(self):
        await self.deinit_async()

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
