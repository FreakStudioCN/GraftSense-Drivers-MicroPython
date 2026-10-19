# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : hogeiha
# @File    : max30100_async.py
# @Description : MAX30100 bounded-I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

from _gs_max30100_max30100 import MAX30100

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MAX30100Async(MAX30100):
    """Expose source MAX30100 operations as awaitable bounded I2C transactions."""

    async def enable_spo2_async(self): return self.enable_spo2()
    async def read_sensor_async(self): return self.read_sensor()
    async def read_red_async(self): return self.red
    async def read_ir_async(self): return self.ir
    async def get_part_id_async(self): return self.get_part_id()
    async def get_rev_id_async(self): return self.get_rev_id()
    async def get_registers_async(self): return self.get_registers()

    async def aclose(self):
        """The caller owns the I2C bus; the source class has no close method."""
        return None

# ======================================== init ================================================

# ======================================== main ================================================