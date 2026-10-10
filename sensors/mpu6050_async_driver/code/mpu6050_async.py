"""MPU6050 adapter with cooperative wake-up timing."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mpu6050 import ComplementaryKalmanFilter, MPU6050, signedIntFromBytes, error_msg, i2c_err_str

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class ComplementaryKalmanFilterAsync(ComplementaryKalmanFilter):
    async def update_roll_pitch_async(self, accel_data, gyro_data):
        return self.update_roll_pitch(accel_data, gyro_data)

class MPU6050Async(MPU6050):
    """Issue the source wake command in __init__; await its 5ms settling time."""

    def __init__(self, i2c, addr=0x68):
        self._failCount = 0
        self._terminatingFailCount = 0
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, MPU6050._PWR_MGMT_1, bytes([0x00]))
        self._started = False

    async def start_async(self):
        if not self._started:
            await asyncio.sleep_ms(5)
            self._accel_range = self.get_accel_range(True)
            self._gyro_range = self.get_gyro_range(True)
            self._started = True

    async def _read_data_async(self, register):
        for attempt in range(MPU6050._maxFails):
            await asyncio.sleep_ms(10)
            try:
                data = self.i2c.readfrom_mem(self.addr, register, 6)
                return {
                    "x": signedIntFromBytes(data[0:2]),
                    "y": signedIntFromBytes(data[2:4]),
                    "z": signedIntFromBytes(data[4:6]),
                }
            except Exception:
                self._failCount += 1
                if attempt + 1 == MPU6050._maxFails:
                    self._terminatingFailCount += 1
                    print(i2c_err_str.format(self.addr))
        return {"x": float("NaN"), "y": float("NaN"), "z": float("NaN")}

    async def read_temperature_async(self):
        try:
            raw_data = self.i2c.readfrom_mem(self.addr, MPU6050._TEMP_OUT0, 2)
            return signedIntFromBytes(raw_data, "big") / 340 + 36.53
        except Exception:
            print(i2c_err_str.format(self.addr))
            return float("NaN")

    async def read_accel_data_async(self, g=False):
        accel_data = await self._read_data_async(MPU6050._ACCEL_XOUT0)
        scalers = {
            MPU6050._ACC_RNG_2G: MPU6050._ACC_SCLR_2G,
            MPU6050._ACC_RNG_4G: MPU6050._ACC_SCLR_4G,
            MPU6050._ACC_RNG_8G: MPU6050._ACC_SCLR_8G,
            MPU6050._ACC_RNG_16G: MPU6050._ACC_SCLR_16G,
        }
        scaler = scalers.get(self._accel_range, MPU6050._ACC_SCLR_2G)
        values = {axis: accel_data[axis] / scaler for axis in ("x", "y", "z")}
        if g:
            return values
        return {axis: values[axis] * MPU6050._GRAVITIY_MS2 for axis in ("x", "y", "z")}

    async def read_gyro_data_async(self):
        gyro_data = await self._read_data_async(MPU6050._GYRO_XOUT0)
        scalers = {
            MPU6050._GYR_RNG_250DEG: MPU6050._GYR_SCLR_250DEG,
            MPU6050._GYR_RNG_500DEG: MPU6050._GYR_SCLR_500DEG,
            MPU6050._GYR_RNG_1000DEG: MPU6050._GYR_SCLR_1000DEG,
            MPU6050._GYR_RNG_2000DEG: MPU6050._GYR_SCLR_2000DEG,
        }
        scaler = scalers.get(self._gyro_range, MPU6050._GYR_SCLR_250DEG)
        return {axis: gyro_data[axis] / scaler for axis in ("x", "y", "z")}

    async def aclose(self):
        return None

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================