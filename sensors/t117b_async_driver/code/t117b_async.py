"""Cooperative T117B register adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from t117b import T117

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class T117Async(T117):
    """Preserves T117B register ordering while yielding for device delays."""

    async def wait_conv_ready_async(self, ms=500):
        if not isinstance(ms, int) or ms <= 0:
            raise ValueError("ms must be a positive int")
        await asyncio.sleep_ms(ms)

    async def get_temp_raw_async(self):
        await self.wait_conv_ready_async()
        data = self._read_words(self.REG_TEMP_LSB, 2)
        self._last_status = self._read_reg(self.REG_STATUS)
        raw = (data[1] << 8) | data[0]
        return raw - 65536 if raw >= 0x8000 else raw

    async def get_temp_async(self):
        raw = await self.get_temp_raw_async()
        temperature = raw / 256.0 + 25.0
        return round(temperature, 2) if -105 <= temperature <= 155 else None

    async def get_status_raw_async(self):
        return self._last_status

    async def get_status_async(self):
        status = self._last_status
        return {
            "high_alert": (status >> 7) & 1,
            "low_alert": (status >> 6) & 1,
            "alert_err": (status >> 2) & 1,
            "raw": status,
        }

    async def set_measure_mode_async(self, mode):
        if not isinstance(mode, int):
            raise ValueError("mode must be int")
        self._write_reg(self.REG_TEMP_CMD, mode)

    async def set_avg_async(self, avg):
        if not isinstance(avg, int) or not 0 <= avg <= 3:
            raise ValueError("avg must be 0~3, got %s" % avg)
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0b11100111 | ((avg & 0x03) << 3)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    async def set_mps_async(self, mps):
        if not isinstance(mps, int) or not 0 <= mps <= 7:
            raise ValueError("mps must be 0~7, got %s" % mps)
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0b00011111 | ((mps & 0x07) << 5)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    async def set_sleep_async(self, enable):
        if not isinstance(enable, bool):
            raise ValueError("enable must be bool")
        cfg = self._read_reg(self.REG_TEMP_CFG) & 0xFE | (1 if enable else 0)
        self._write_reg(self.REG_TEMP_CFG, cfg)

    async def set_alert_config_async(self, enable, polarity=0, mode=0):
        if not isinstance(enable, bool):
            raise ValueError("enable must be bool")
        if polarity not in (0, 1) or mode not in (0, 1):
            raise ValueError("polarity and mode must be 0 or 1")
        self._write_reg(self.REG_ALERT_MODE, (0x80 if enable else 0) | (polarity << 6) | (mode << 5))
        await asyncio.sleep_ms(5)

    async def set_alert_thresholds_async(self, th_temp, tl_temp):
        if not isinstance(th_temp, (int, float)) or not isinstance(tl_temp, (int, float)):
            raise ValueError("thresholds must be numeric")
        if th_temp <= tl_temp:
            raise ValueError("th_temp must be greater than tl_temp")
        high = max(-32768, min(32767, int((th_temp - 25.0) * 256)))
        low = max(-32768, min(32767, int((tl_temp - 25.0) * 256)))
        if self._msb_first:
            writes = ((self.REG_TH_MSB, high >> 8), (self.REG_TH_LSB, high), (self.REG_TL_MSB, low >> 8), (self.REG_TL_LSB, low))
        else:
            writes = ((self.REG_TH_LSB, high), (self.REG_TH_MSB, high >> 8), (self.REG_TL_LSB, low), (self.REG_TL_MSB, low >> 8))
        for register, value in writes:
            self._write_reg(register, value)
        await asyncio.sleep_ms(5)

    async def enable_alerts_async(self, th_temp, tl_temp, mps=T117.MPS_8S, avg=T117.AVG_8, polarity=0, mode=0):
        await self.set_measure_mode_async(self.MEAS_CONTINUE)
        await self.set_mps_async(mps)
        await self.set_avg_async(avg)
        await self.set_alert_thresholds_async(th_temp, tl_temp)
        await self.set_alert_config_async(True, polarity, mode)
        await self.set_sleep_async(False)
        await asyncio.sleep_ms(10)

    async def soft_reset_async(self):
        self._write_reg(self.REG_E2PROM_CMD, self.E2PROM_SOFT_RST)
        await asyncio.sleep_ms(100)

    async def deinit_async(self):
        try:
            await self.set_measure_mode_async(self.MEAS_STOP)
        except RuntimeError:
            pass

    async def aclose(self):
        await self.deinit_async()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================