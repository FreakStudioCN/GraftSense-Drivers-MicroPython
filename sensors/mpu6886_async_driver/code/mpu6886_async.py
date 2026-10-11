"""Cooperative MPU6886 adapter preserving source register operations."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mpu6886 import MPU6886, ACCEL_FS_SEL_2G, GYRO_FS_SEL_250DPS, SF_M_S2, SF_RAD_S

PWR_MGMT_1_REG = 0x6B

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MPU6886Async(MPU6886):
    """Awaitable MPU6886 API; every I2C access remains a bounded transaction."""

    def __init__(self, i2c, address=0x68, accel_fs=ACCEL_FS_SEL_2G, gyro_fs=GYRO_FS_SEL_250DPS, accel_sf=SF_M_S2, gyro_sf=SF_RAD_S, gyro_offset=(0, 0, 0), debug=False):
        if i2c is None or not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must be an I2C instance")
        self._i2c = i2c
        self._address = address
        self._debug = debug
        chip_id = self.whoami
        if chip_id != 0x19:
            raise RuntimeError("MPU6886 not found at I2C address 0x%02X, device ID: 0x%02X" % (address, chip_id))
        self._register_char(PWR_MGMT_1_REG, 0b10000000)
        self._pending_start = (accel_fs, gyro_fs, accel_sf, gyro_sf, gyro_offset)
        self._started = False

    async def start_async(self):
        if not self._started:
            await asyncio.sleep_ms(100)
            self._register_char(PWR_MGMT_1_REG, 0b00000001)
            accel_fs, gyro_fs, accel_sf, gyro_sf, gyro_offset = self._pending_start
            self._accel_so = self._accel_fs(accel_fs)
            self._gyro_so = self._gyro_fs(gyro_fs)
            self._accel_sf = accel_sf
            self._gyro_sf = gyro_sf
            self._gyro_offset = gyro_offset
            self._started = True

    async def calibrate_async(self, count=256, delay=0):
        if not isinstance(count, int) or count < 1:
            raise ValueError("count must be a positive int")
        if not isinstance(delay, int) or delay < 0:
            raise ValueError("delay must be a non-negative int")
        ox = oy = oz = 0.0
        self._gyro_offset = (0.0, 0.0, 0.0)
        for _ in range(count):
            if delay:
                await asyncio.sleep_ms(delay)
            else:
                await asyncio.sleep_ms(0)
            gx, gy, gz = self.gyro
            ox += gx
            oy += gy
            oz += gz
        self._gyro_offset = (ox / count, oy / count, oz / count)
        self._log("Calibration complete, offset: (%f, %f, %f)" % self._gyro_offset)
        return self._gyro_offset

    async def acceleration_async(self):
        return self.acceleration

    async def gyro_async(self):
        return self.gyro

    async def temperature_async(self):
        return self.temperature

    async def whoami_async(self):
        return self.whoami

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
