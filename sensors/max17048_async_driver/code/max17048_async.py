# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Andre Peeters
# @File    : max17048_async.py
# @Description : MAX17048 bounded-I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

from max17048 import MAX17048

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MAX17048Async(MAX17048):
    """Explicit source-API adapters; caller retains I2C ownership."""
    async def sensor_exists_async(self): return self.sensor_exists()
    async def address_async(self): return self.address()
    async def reset_async(self): return self.reset()
    async def getVCell_async(self): return self.getVCell()
    async def getSoc_async(self): return self.getSoc()
    async def getVersion_async(self): return self.getVersion()
    async def getCompensateValue_async(self): return self.getCompensateValue()
    async def getAlertThreshold_async(self): return self.getAlertThreshold()
    async def setAlertThreshold_async(self, threshold): return self.setAlertThreshold(threshold)
    async def inAlert_async(self): return self.inAlert()
    async def clearAlert_async(self): return self.clearAlert()
    async def quickStart_async(self): return self.quickStart()
    async def aclose(self): return None

# ======================================== init ================================================

# ======================================== main ================================================