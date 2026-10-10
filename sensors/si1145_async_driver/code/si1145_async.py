"""Cooperative SI1145 register adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from si1145 import *

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SI1145Async(SI1145):
    async def read_uv_async(self): return self.read_uv
    async def read_visible_async(self): return self.read_visible
    async def read_ir_async(self): return self.read_ir
    async def read_prox_async(self): return self.read_prox
    async def _write8_async(self, register, value):
        return self._write8(register, value)
    async def _reset_async(self):
        for register, value in ((SI1145_REG_MEASRATE0, 0), (SI1145_REG_MEASRATE1, 0), (SI1145_REG_IRQEN, 0), (SI1145_REG_IRQMODE1, 0), (SI1145_REG_IRQMODE2, 0), (SI1145_REG_INTCFG, 0), (SI1145_REG_IRQSTAT, 0xFF), (SI1145_REG_COMMAND, SI1145_RESET)):
            self._write8(register, value)
        await asyncio.sleep_ms(10)
        self._write8(SI1145_REG_HWKEY, 0x17)
        await asyncio.sleep_ms(10)
    async def _load_calibration_async(self):
        for register, value in ((SI1145_REG_UCOEFF0, 0x7B), (SI1145_REG_UCOEFF1, 0x6B), (SI1145_REG_UCOEFF2, 0x01), (SI1145_REG_UCOEFF3, 0x00), (SI1145_REG_INTCFG, SI1145_REG_INTCFG_INTOE), (SI1145_REG_IRQEN, SI1145_REG_IRQEN_ALSEVERYSAMPLE), (SI1145_REG_MEASRATE0, 0xFF)):
            self._write8(register, value)
        self._write_param(SI1145_PARAM_CHLIST, SI1145_PARAM_CHLIST_ENUV | SI1145_PARAM_CHLIST_ENAUX | SI1145_PARAM_CHLIST_ENALSIR | SI1145_PARAM_CHLIST_ENALSVIS | SI1145_PARAM_CHLIST_ENPS1)
        self._i2c.writeto_mem(SI1145_ADDR, SI1145_REG_PSLED21, b'0x03')
        for parameter, value in ((SI1145_PARAM_PS1ADCMUX, SI1145_PARAM_ADCMUX_LARGEIR), (SI1145_PARAM_PSLED12SEL, SI1145_PARAM_PSLED12SEL_PS1LED1), (SI1145_PARAM_PSADCGAIN, 0), (SI1145_PARAM_PSADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK), (SI1145_PARAM_PSADCMISC, SI1145_PARAM_PSADCMISC_RANGE | SI1145_PARAM_PSADCMISC_PSMODE), (SI1145_PARAM_ALSIRADCMUX, SI1145_PARAM_ADCMUX_SMALLIR), (SI1145_PARAM_ALSIRADCGAIN, 0), (SI1145_PARAM_ALSIRADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK), (SI1145_PARAM_ALSIRADCMISC, SI1145_PARAM_ALSIRADCMISC_RANGE), (SI1145_PARAM_ALSVISADCGAIN, 0), (SI1145_PARAM_ALSVISADCOUNTER, SI1145_PARAM_ADCCOUNTER_511CLK), (SI1145_PARAM_ALSVISADCMISC, SI1145_PARAM_ALSVISADCMISC_VISRANGE)):
            self._write_param(parameter, value)
            await asyncio.sleep_ms(0)
        self._write8(SI1145_REG_COMMAND, SI1145_PSALS_AUTO)
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================