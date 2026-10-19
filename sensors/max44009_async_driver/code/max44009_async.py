# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : max44009_async.py
# @Description : MAX44009 bounded-I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

from _gs_max44009_max44009 import MAX44009

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MAX44009Async(MAX44009):
    """Awaitable facade preserving MAX44009 property semantics."""

    async def set_continuous_async(self, value): self.continuous = value
    async def set_manual_async(self, value): self.manual = value
    async def set_current_division_ratio_async(self, value): self.current_division_ratio = value
    async def set_integration_time_async(self, value): self.integration_time = value
    async def read_lux_async(self): return self.lux
    async def read_lux_fast_async(self): return self.lux_fast
    async def read_int_status_async(self): return self.int_status

    async def aclose(self):
        self.deinit()

# ======================================== init ================================================

# ======================================== main ================================================