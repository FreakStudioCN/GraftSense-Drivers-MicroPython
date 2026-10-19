"""Cooperative MPU9250 composition adapter with staged hardware startup."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import _gs_mpu9250_ak8963 as _ak
import _gs_mpu9250_mpu6500 as _m6500
from _gs_mpu9250_ak8963 import AK8963
from _gs_mpu9250_mpu6500 import MPU6500
from _gs_mpu9250_mpu9250 import MPU9250

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class AK8963Async(AK8963):
    async def get_offset_async(self):
        return self.get_offset()

    async def get_scale_async(self):
        return self.get_scale()

    async def magnetic_async(self):
        return self.magnetic

    async def adjustement_async(self):
        return self.adjustement

    async def whoami_async(self):
        return self.whoami

    async def aclose(self):
        self._register_char(_ak._CNTL1, _ak._MODE_POWER_DOWN)
        await asyncio.sleep_ms(10)

class MPU6500Async(MPU6500):
    async def acceleration_async(self):
        return self.acceleration

    async def gyro_async(self):
        return self.gyro

    async def temperature_async(self):
        return self.temperature

    async def whoami_async(self):
        return self.whoami

    async def calibrate_async(self, count=256, delay=0):
        if not isinstance(count, int) or count < 1:
            raise ValueError('count must be a positive int')
        if not isinstance(delay, int) or delay < 0:
            raise ValueError('delay must be a non-negative int')
        ox = oy = oz = 0.0
        self._gyro_offset = (0.0, 0.0, 0.0)
        for _ in range(count):
            await asyncio.sleep_ms(delay)
            gx, gy, gz = self.gyro
            ox += gx
            oy += gy
            oz += gz
        self._gyro_offset = (ox / count, oy / count, oz / count)
        return self._gyro_offset

    async def aclose(self):
        self._register_char(_m6500._PWR_MGMT_1, 0x40)

class MPU9250Async(MPU9250):
    @classmethod
    async def create_async(cls, i2c):
        """Create the MPU6500 and AK8963 in source register order."""
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')

        mpu = MPU6500Async.__new__(MPU6500Async)
        mpu._i2c = i2c
        mpu._address = _m6500.MPU6500.I2C_DEFAULT_ADDR
        mpu._debug = False
        mpu._gyro_offset = (0, 0, 0)
        if mpu.whoami not in _m6500._VALID_WHOAMI:
            raise RuntimeError('MPU6500 not found on I2C bus')
        mpu._register_char(_m6500._PWR_MGMT_1, 0x80)
        await asyncio.sleep_ms(100)
        mpu._register_char(_m6500._PWR_MGMT_1, 0x00)
        await asyncio.sleep_ms(100)
        mpu._accel_so = mpu._accel_fs(_m6500.ACCEL_FS_SEL_2G)
        mpu._gyro_so = mpu._gyro_fs(_m6500.GYRO_FS_SEL_250DPS)
        mpu._accel_sf = _m6500.SF_M_S2
        mpu._gyro_sf = _m6500.SF_RAD_S

        sensor = cls.__new__(cls)
        sensor.mpu6500 = mpu
        sensor._set_i2c_bypass(True)
        await asyncio.sleep_ms(10)

        mag = AK8963Async.__new__(AK8963Async)
        mag._i2c = i2c
        mag._address = _ak.AK8963.I2C_DEFAULT_ADDR
        mag._offset = (0, 0, 0)
        mag._scale = (1, 1, 1)
        mag._debug = False
        mag._mode = _ak.MODE_CONTINOUS_MEASURE_1
        mag._so = _ak._SO_16BIT
        mag._register_char(_ak._CNTL1, _ak._MODE_POWER_DOWN)
        await asyncio.sleep_ms(10)
        mag._register_char(_ak._CNTL1, _ak._MODE_FUSE_ROM_ACCESS)
        await asyncio.sleep_ms(10)
        asax = mag._register_char(_ak._ASAX)
        asay = mag._register_char(_ak._ASAY)
        asaz = mag._register_char(_ak._ASAZ)
        mag._register_char(_ak._CNTL1, _ak._MODE_POWER_DOWN)
        await asyncio.sleep_ms(10)
        mag._adjustement = ((0.5 * (asax - 128)) / 128 + 1,
                            (0.5 * (asay - 128)) / 128 + 1,
                            (0.5 * (asaz - 128)) / 128 + 1)
        mag._register_char(_ak._CNTL1, mag._mode | _ak.OUTPUT_16_BIT)
        await asyncio.sleep_ms(10)
        sensor.ak8963 = mag
        return sensor

    def __init__(self, i2c, mpu6500=None, ak8963=None):
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')
        self._i2c = i2c
        self.mpu6500 = mpu6500
        self.ak8963 = ak8963

    async def start_async(self):
        """Perform the staged, non-blocking initialization for this instance."""
        i2c = self._i2c
        ready = await type(self).create_async(i2c)
        self.mpu6500 = ready.mpu6500
        self.ak8963 = ready.ak8963
        return self
    async def acceleration_async(self):
        return self.acceleration

    async def gyro_async(self):
        return self.gyro

    async def magnetic_async(self):
        return self.magnetic

    async def temperature_async(self):
        return self.temperature

    async def whoami_async(self):
        return self.whoami

    async def aclose(self):
        await self.ak8963.aclose()
        self._set_i2c_bypass(False)
        await self.mpu6500.aclose()