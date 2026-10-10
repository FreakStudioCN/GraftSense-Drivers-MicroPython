# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Rob Hamerling
# @File    : as7341_async.py
# @Description : Source-faithful AS7341 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from as7341 import AS7341

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class AS7341Async(AS7341):
    """Keep source synchronous API intact; provide bounded async measurement wait."""
    async def start_measure_async(self, selection=None, timeout_ms=2000, poll_ms=50):
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        if not isinstance(poll_ms, int) or poll_ms <= 0:
            raise ValueError("poll_ms must be a positive integer")
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        self._modify_reg(self.AS7341_CFG_0, self.AS7341_CFG_0_LOW_POWER, False)
        self.set_spectral_measurement(False)
        self._write_byte(self.AS7341_CFG_6, self.AS7341_CFG_6_SMUX_CMD_WRITE)
        if selection is not None:
            self.channel_select(selection)
        if self._measuremode == self.AS7341_CONFIG_INT_MODE_SPM:
            self.set_smux(True)
        elif self._measuremode == self.AS7341_CONFIG_INT_MODE_SYNS:
            self.set_smux(True)
            self.set_gpio_input(True)
        self.set_spectral_measurement(True)
        if self._measuremode == self.AS7341_CONFIG_INT_MODE_SPM:
            while not self.measurement_completed():
                if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                    raise TimeoutError("AS7341 measurement timeout after %d ms" % timeout_ms)
                await asyncio.sleep_ms(poll_ms)
    async def isconnected_async(self): return self.isconnected()
    async def set_measure_mode_async(self, mode): return self.set_measure_mode(mode)
    async def get_channel_data_async(self, channel=0): return self.get_channel_data(channel)
    async def get_spectral_data_async(self): return self.get_spectral_data()
    async def set_gpio_input_async(self, enable=True): return self.set_gpio_input(enable)
    async def get_gpio_value_async(self): return self.get_gpio_value()
    async def set_gpio_output_async(self, inverted=False): return self.set_gpio_output(inverted)
    async def set_gpio_inverted_async(self, flag=True): return self.set_gpio_inverted(flag)
    async def set_astep_async(self, value=599): return self.set_astep(value)
    async def get_astep_time_async(self): return self.get_astep_time()
    async def set_atime_async(self, value=29): return self.set_atime(value)
    async def get_overflow_count_async(self): return self.get_overflow_count()
    async def get_integration_time_async(self): return self.get_integration_time()
    async def set_again_async(self, code): return self.set_again(code)
    async def get_again_async(self): return self.get_again()
    async def set_again_factor_async(self, factor): return self.set_again_factor(factor)
    async def get_again_factor_async(self): return self.get_again_factor()
    async def set_wen_async(self, flag=True): return self.set_wen(flag)
    async def set_wtime_async(self, code): return self.set_wtime(code)
    async def set_led_current_async(self, current): return self.set_led_current(current)
    async def check_interrupt_async(self): return self.check_interrupt()
    async def clear_interrupt_async(self): return self.clear_interrupt()
    async def set_spectral_interrupt_async(self, flag=True): return self.set_spectral_interrupt(flag)
    async def set_interrupt_persistence_async(self, value): return self.set_interrupt_persistence(value)
    async def set_thresholds_async(self, lo, hi): return self.set_thresholds(lo, hi)
    async def get_thresholds_async(self): return self.get_thresholds()
    async def aclose(self):
        self.disable()
        await asyncio.sleep_ms(0)

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================