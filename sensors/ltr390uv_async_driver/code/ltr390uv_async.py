# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : MicroPython Developer
# @File    : ltr390uv_async.py
# @Description : LTR390UV bounded-I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

from _gs_ltr390uv_ltr390uv import LTR390UV
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class LTR390UVAsync(LTR390UV):
    """Awaitable facade preserving LTR390UV method and property semantics."""

    async def get_id_async(self): return self.get_id()
    async def soft_reset_async(self):
        register = self.ctrl_reg
        register['soft_reset'] = 1
        try:
            register.write()
        except OSError as error:
            raise RuntimeError('I2C write soft_reset failed') from error
        for _ in range(3):
            await asyncio.sleep_ms(10)
            try:
                register.read()
                if not register['soft_reset']:
                    break
            except OSError as error:
                if error.errno != 110:
                    raise RuntimeError('I2C error during soft reset') from error
        else:
            raise RuntimeError('Soft reset did not complete within timeout')
    async def start_measurement_async(self, uv_mode, meas_rate=1, gain=3, enable=True):
        return self.start_measurement(uv_mode, meas_rate, gain, enable)
    async def get_conversion_cycle_time_async(self): return self.get_conversion_cycle_time()
    async def get_status_async(self): return self.get_status()
    async def get_illumination_async(self, raw=True, w_fac=1.0):
        return self.get_illumination(raw, w_fac)
    async def get_uv_mode_async(self): return self.uv_mode
    async def get_meas_rate_async(self): return self.meas_rate
    async def get_resolution_async(self): return self.resolution
    async def get_gain_async(self): return self.gain

    async def aclose(self):
        self.deinit()

# ======================================== init ================================================

# ======================================== main ================================================
