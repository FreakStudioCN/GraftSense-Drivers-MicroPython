"""Explicit async facade for bounded MMA7660 I2C operations."""

from mma7660 import Accelerometer


class AccelerometerAsync(Accelerometer):
    """Each API preserves one finite source I2C operation."""

    async def write_async(self, register, data):
        return self.write(register, data)

    async def read_async(self, register):
        return self.read(register)

    async def initAccelTable_async(self):
        return self.initAccelTable()

    async def setMode_async(self, mode):
        return self.setMode(mode)

    async def setSampleRate_async(self, rate):
        return self.setSampleRate(rate)

    async def getXYZ_async(self):
        return self.getXYZ()

    async def getAcceleration_async(self):
        return self.getAcceleration()

    async def getAllData_async(self):
        return self.getAllData()

    async def aclose(self):
        return None