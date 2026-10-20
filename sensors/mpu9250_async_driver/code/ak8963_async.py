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
from micropython import const

# Identical to the private consts in the source; private names are not exported.
_CNTL1 = const(10)
_ASAX = const(16)
_ASAY = const(17)
_ASAZ = const(18)
_MODE_POWER_DOWN = const(0)
_MODE_FUSE_ROM_ACCESS = const(15)
_PWR_MGMT_1 = const(107)

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class AK8963Async(AK8963):
    def __init__(self, i2c, address=AK8963.I2C_DEFAULT_ADDR,
                 mode=_ak.MODE_CONTINOUS_MEASURE_1, output=_ak.OUTPUT_16_BIT,
                 offset=(0, 0, 0), scale=(1, 1, 1), debug=False):
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')
        if not isinstance(address, int): raise ValueError('address must be int')
        if not isinstance(mode, int) or mode not in _ak._VALID_MODES: raise ValueError('invalid AK8963 mode')
        if not isinstance(output, int) or output not in _ak._VALID_OUTPUTS: raise ValueError('invalid AK8963 output')
        if not isinstance(offset, tuple) or len(offset) != 3: raise ValueError('invalid offset')
        if not isinstance(scale, tuple) or len(scale) != 3: raise ValueError('invalid scale')
        if not isinstance(debug, bool): raise ValueError('debug must be bool')
        self._i2c, self._address, self._debug = i2c, address, debug
        self._offset, self._scale, self._mode = offset, scale, mode
        self._so = _ak._SO_16BIT if output == _ak.OUTPUT_16_BIT else _ak._SO_14BIT
        self._output, self._initialized = output, False
        self._async_lock = asyncio.Lock()

    async def initialize_async(self):
        async with self._async_lock:
            if self._initialized: return self
            if self.whoami != 0x48: raise RuntimeError('AK8963 not found on I2C bus')
            try:
                self._register_char(_CNTL1, _MODE_POWER_DOWN)
                await asyncio.sleep_ms(10)
                self._register_char(_CNTL1, _MODE_FUSE_ROM_ACCESS)
                await asyncio.sleep_ms(10)
                asax, asay, asaz = (self._register_char(_ASAX), self._register_char(_ASAY), self._register_char(_ASAZ))
                self._register_char(_CNTL1, _MODE_POWER_DOWN)
                await asyncio.sleep_ms(10)
                self._adjustement = ((0.5 * (asax - 128)) / 128 + 1,
                                    (0.5 * (asay - 128)) / 128 + 1,
                                    (0.5 * (asaz - 128)) / 128 + 1)
                self._register_char(_CNTL1, self._mode | self._output)
                await asyncio.sleep_ms(10)
                self._initialized = True
            except BaseException as error:
                try: self._register_char(_CNTL1, _MODE_POWER_DOWN)
                except BaseException as cleanup_error: raise error from cleanup_error
                raise
            return self

    @classmethod
    async def create_async(cls, *args, **kwargs):
        return await cls(*args, **kwargs).initialize_async()

    async def get_offset_async(self):
        return self.get_offset()

    async def get_scale_async(self):
        return self.get_scale()

    async def magnetic_async(self):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
        return self.magnetic

    async def adjustement_async(self):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
        return self.adjustement

    async def whoami_async(self):
        return self.whoami

    async def aclose(self):
        async with self._async_lock:
            if self._initialized:
                self._register_char(_CNTL1, _MODE_POWER_DOWN)
                self._initialized = False
                await asyncio.sleep_ms(10)

class MPU6500Async(MPU6500):
    def __init__(self, i2c, address=MPU6500.I2C_DEFAULT_ADDR,
                 accel_fs=_m6500.ACCEL_FS_SEL_2G, gyro_fs=_m6500.GYRO_FS_SEL_250DPS,
                 accel_sf=_m6500.SF_M_S2, gyro_sf=_m6500.SF_RAD_S,
                 gyro_offset=(0, 0, 0), debug=False):
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')
        if not isinstance(address, int): raise ValueError('address must be int')
        if not isinstance(accel_fs, int) or not isinstance(gyro_fs, int): raise ValueError('full scale must be int')
        if isinstance(accel_sf, bool) or not isinstance(accel_sf, (int, float)) or accel_sf <= 0: raise ValueError('invalid acceleration scale')
        if isinstance(gyro_sf, bool) or not isinstance(gyro_sf, (int, float)) or gyro_sf <= 0: raise ValueError('invalid gyro scale')
        if not isinstance(gyro_offset, tuple) or len(gyro_offset) != 3: raise ValueError('invalid gyro offset')
        if not isinstance(debug, bool): raise ValueError('debug must be bool')
        self._i2c, self._address, self._debug = i2c, address, debug
        self._gyro_offset = gyro_offset
        self._accel_sf, self._gyro_sf = accel_sf, gyro_sf
        self._initial_accel_fs, self._initial_gyro_fs = accel_fs, gyro_fs
        self._initialized = False
        self._async_lock = asyncio.Lock()

    async def initialize_async(self):
        async with self._async_lock:
            if self._initialized: return self
            if self.whoami not in _m6500._VALID_WHOAMI: raise RuntimeError('MPU6500 not found on I2C bus')
            try:
                self._register_char(_PWR_MGMT_1, 0x80)
                await asyncio.sleep_ms(100)
                self._register_char(_PWR_MGMT_1, 0)
                await asyncio.sleep_ms(100)
                self._accel_so = self._accel_fs(self._initial_accel_fs)
                self._gyro_so = self._gyro_fs(self._initial_gyro_fs)
                self._initialized = True
            except BaseException as error:
                try: self._register_char(_PWR_MGMT_1, 0x40)
                except BaseException as cleanup_error: raise error from cleanup_error
                raise
            return self

    @classmethod
    async def create_async(cls, *args, **kwargs):
        return await cls(*args, **kwargs).initialize_async()

    async def acceleration_async(self):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
        return self.acceleration

    async def gyro_async(self):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
        return self.gyro

    async def temperature_async(self):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
        return self.temperature

    async def whoami_async(self):
        return self.whoami

    async def calibrate_async(self, count=256, delay=0):
        if not self._initialized: raise RuntimeError('Call initialize_async() before use')
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
        async with self._async_lock:
            if self._initialized:
                self._register_char(_PWR_MGMT_1, 0x40)
                self._initialized = False


class MPU9250Async(MPU9250):
    @classmethod
    async def create_async(cls, i2c):
        """Create the MPU6500 and AK8963 in source register order."""
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')

        sensor = cls(i2c)
        sensor.mpu6500 = await MPU6500Async.create_async(i2c)
        try:
            sensor._set_i2c_bypass(True)
            await asyncio.sleep_ms(10)
            sensor.ak8963 = await AK8963Async.create_async(i2c)
        except BaseException as error:
            try:
                sensor._set_i2c_bypass(False)
                await sensor.mpu6500.aclose()
            except BaseException as cleanup_error:
                raise error from cleanup_error
            raise
        return sensor

    def __init__(self, i2c, mpu6500=None, ak8963=None):
        if not hasattr(i2c, 'readfrom_mem_into') or not hasattr(i2c, 'writeto_mem'):
            raise ValueError('i2c must provide readfrom_mem_into and writeto_mem')
        self._i2c = i2c
        self.mpu6500 = mpu6500
        self.ak8963 = ak8963

    async def start_async(self):
        """Perform the staged, non-blocking initialization for this instance."""
        if (self.mpu6500 is not None and self.ak8963 is not None
                and getattr(self.mpu6500, '_initialized', False)
                and getattr(self.ak8963, '_initialized', False)):
            return self
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
        if self.ak8963 is not None:
            await self.ak8963.aclose()
        if self.mpu6500 is not None and self.mpu6500._initialized:
            self._set_i2c_bypass(False)
            await self.mpu6500.aclose()
