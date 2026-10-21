"""Cooperative RM3100 adapter preserving source I2C transactions."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class RM3100Async:
    def __init__(self, sensor):
        self._sensor = sensor
        self._lock = asyncio.Lock()
        self._closed = False

    async def get_id_async(self):
        async with self._lock:
            return self._sensor.get_id()

    async def perform_self_test_async(self, timeout_ms=50):
        async with self._lock:
            self._sensor._write_reg(0, 0x70)
            self._sensor._write_reg(0x35, 8)
            self._sensor._write_reg(0x33, 0x8F)
            self._sensor._write_reg(0, 0x70)
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        try:
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                async with self._lock:
                    ready = self._sensor.get_status()[0]
                if ready:
                    break
                await asyncio.sleep_ms(10)
            async with self._lock:
                result = self._sensor._read_reg(0x33)[0]
            return bool(result & 64), bool(result & 32), bool(result & 16), (result & 12) >> 2, result & 3
        finally:
            async with self._lock:
                self._sensor._write_reg(0x33, 0)

    async def get_axis_cycle_count_async(self, axis):
        async with self._lock:
            return self._sensor.get_axis_cycle_count(axis)

    async def start_measure_async(self, axis, update_rate=6, single_mode=True):
        async with self._lock:
            self._sensor.start_measure(axis=axis, update_rate=update_rate, single_mode=single_mode)

    async def is_data_ready_async(self):
        async with self._lock:
            return self._sensor.is_data_ready()

    async def is_continuous_meas_mode_async(self):
        async with self._lock:
            return self._sensor.is_continuous_meas_mode()

    async def wait_data_ready_async(self, timeout_ms=1000):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not await self.is_data_ready_async():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False
            await asyncio.sleep_ms(1)
        return True

    async def get_meas_result_async(self, axis):
        async with self._lock:
            return self._sensor.get_meas_result(axis)

    async def get_axis_async(self, axis=-1):
        async with self._lock:
            return self._sensor.get_axis(axis)

    async def aclose(self):
        if not self._closed:
            async with self._lock:
                self._sensor.deinit()
                self._closed = True

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================