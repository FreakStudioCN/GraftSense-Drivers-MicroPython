"""MS5803 cooperative conversion adapter."""

# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError


try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_diff = lambda end, start: end - start

from MS5803 import *


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MS5803Async(MS5803):
    """MS5803 with source ADC conversion waits yielded to uasyncio."""

    async def reset_async(self, timeout_ms=3100):
        started = ticks_ms()
        self.i2c.writeto_mem(self.address, self.CMD_RESET, b"")
        await asyncio.sleep_ms(3000)
        if ticks_diff(ticks_ms(), started) > timeout_ms:
            raise TimeoutError("MS5803 reset timed out")

    async def _get_adc_conversion_async(self, measurement, precision, deadline):
        self.i2c.writeto_mem(self.address, self.CMD_ADC_CONV + measurement + precision.address, b"")
        await asyncio.sleep_ms(precision.sampling_time)
        if ticks_diff(ticks_ms(), deadline) > 0:
            raise TimeoutError("MS5803 ADC conversion timed out")
        buf = self.i2c.readfrom_mem(self.address, self.CMD_ADC_READ, 3)
        return (buf[0] << 16) + (buf[1] << 8) + buf[2]

    async def get_measurements_async(self, temp_osr=None, pressure_osr=None, temp_units=None, pressure_units=None, timeout_ms=100):
        if temp_osr:
            self.temp_osr = temp_osr
        else:
            temp_osr = self.temp_osr
        if pressure_osr:
            self.pressure_osr = pressure_osr
        else:
            pressure_osr = self.pressure_osr
        if temp_units:
            self.temp_units = temp_units
        else:
            temp_units = self.temp_units
        if pressure_units:
            self.pressure_units = pressure_units
        else:
            pressure_units = self.pressure_units
        deadline = ticks_ms() + timeout_ms
        temp_raw = await self._get_adc_conversion_async(self.TEMPERATURE, temp_osr, deadline)
        pressure_raw = await self._get_adc_conversion_async(self.PRESSURE, pressure_osr, deadline)
        dT = temp_raw - (self.C[5] << 8)
        temp = ((dT * self.C[6]) >> 23) + 2000
        if temp < 2000:
            T2 = 3 * ((dT * dT) >> 33)
            OFF2 = 3 * ((temp - 2000) * (temp - 2000)) >> 1
            SENS2 = 5 * ((temp - 2000) * (temp - 2000)) >> 3
            if temp < -1500:
                OFF2 += 7 * ((temp + 1500) * (temp + 1500))
                SENS2 += ((temp + 1500) * (temp + 1500)) << 2
        else:
            T2 = 7 * (dT * dT) >> 37
            OFF2 = ((temp - 2000) * (temp - 2000)) >> 4
            SENS2 = 0
        OFF = (self.C[2] << 16) + ((self.C[4] * dT) >> 7)
        SENS = (self.C[1] << 15) + ((self.C[3] * dT) >> 8)
        temp -= T2
        pressure = (((SENS - SENS2) * pressure_raw >> 21) - (OFF - OFF2)) >> 15
        if temp_units:
            temp = convert_temperature(temp, temp_units)
        if pressure_units:
            pressure = convert_pressure(pressure, pressure_units)
        return temp, pressure

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit:
            deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
