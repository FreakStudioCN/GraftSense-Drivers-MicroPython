"""Cooperative VL53L0X initialization and ranging adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from vl53l0x import VL53L0X
IO_TIMEOUT_MS = 1000
SYSRANGE_START_REG = 0x00
EXTSUP_HV_REG = 0x89
MSRC_CONFIG_REG = 0x60
FINAL_RATE_RTN_LIMIT_REG = 0x44
SYSTEM_SEQUENCE_REG = 0x01
SPAD_REF_START_REG = 0x4F
SPAD_ENABLES_REG = 0xB0
REF_EN_START_SELECT_REG = 0xB6
SPAD_NUM_REQUESTED_REG = 0x4E
INTERRUPT_GPIO_REG = 0x0A
INTERRUPT_CLEAR_REG = 0x0B
GPIO_MUX_ACTIVE_HIGH_REG = 0x84
RESULT_INTERRUPT_STATUS_REG = 0x13
RESULT_RANGE_STATUS_REG = 0x14
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VL53L0XAsync(VL53L0X):
    """Defers source initialization and yields at every hardware readiness poll."""
    def __init__(self, i2c, address=0x29):
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise TypeError("i2c must be a valid machine.I2C instance")
        if not isinstance(address, int) or address != 0x29:
            raise ValueError("The I2C address must be 0x29.")
        self.i2c, self.address = i2c, address
        self._started = False
        self._initialized = False
        self.measurement_timing_budget_us = 0
        self.enables = {"tcc": 0, "dss": 0, "msrc": 0, "pre_range": 0, "final_range": 0}
        self.timeouts = {"pre_range_vcsel_period_pclks": 0, "msrc_dss_tcc_mclks": 0, "msrc_dss_tcc_us": 0, "pre_range_mclks": 0, "pre_range_us": 0, "final_range_vcsel_period_pclks": 0, "final_range_mclks": 0, "final_range_us": 0}
        self.vcsel_period_type = ["VcselPeriodPreRange", "VcselPeriodFinalRange"]

    async def _spad_info_async(self, timeout_ms=IO_TIMEOUT_MS):
        self._config((0x80, 0x01), (0xFF, 0x01), (0x00, 0x00), (0xFF, 0x06))
        self._flag(0x83, 3, True)
        self._config((0xFF, 0x07), (0x81, 0x01), (0x80, 0x01), (0x94, 0x6B), (0x83, 0x00))
        started = time.ticks_ms()
        while not self._register(0x83):
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise RuntimeError("Timeout")
            await asyncio.sleep_ms(1)
        self._config((0x83, 0x01))
        value = self._register(0x92)
        self._config((0x81, 0x00), (0xFF, 0x06))
        self._flag(0x83, 3, False)
        self._config((0xFF, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00))
        return value & 0x7F, bool(value & 0x80)

    async def _calibrate_async(self, vhv_init_byte, timeout_ms=IO_TIMEOUT_MS):
        self._register(SYSRANGE_START_REG, 0x01 | vhv_init_byte)
        started = time.ticks_ms()
        while not (self._register(RESULT_INTERRUPT_STATUS_REG) & 0x07):
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise RuntimeError("timeout")
            await asyncio.sleep_ms(1)
        self._register(INTERRUPT_CLEAR_REG, 0x01)
        self._register(SYSRANGE_START_REG, 0x00)

    async def initialize_async(self, power2v8=True):
        if self._initialized:
            return
        self._flag(EXTSUP_HV_REG, 0, power2v8)
        self._config((0x88,0x00),(0x80,0x01),(0xFF,0x01),(0x00,0x00))
        self._stop_variable = self._register(0x91)
        self._config((0x00,0x01),(0xFF,0x00),(0x80,0x00))
        self._flag(MSRC_CONFIG_REG,1,True); self._flag(MSRC_CONFIG_REG,4,True)
        self._register(FINAL_RATE_RTN_LIMIT_REG,int(0.1*(1<<7)),_struct=">H")
        self._register(SYSTEM_SEQUENCE_REG,0xFF)
        spad_count,is_aperture=await self._spad_info_async()
        spad_map=bytearray(self._registers(SPAD_ENABLES_REG,_struct="6B"))
        self._config((0xFF,0x01),(SPAD_REF_START_REG,0x00),(SPAD_NUM_REQUESTED_REG,0x2C),(0xFF,0x00),(REF_EN_START_SELECT_REG,0xB4))
        enabled=0
        for index in range(48):
            if (index < 12 and is_aperture) or enabled >= spad_count:
                spad_map[index // 8] &= ~(1 << (index >> 2))
            elif spad_map[index // 8] & (1 << (index >> 2)):
                enabled += 1
        self._registers(SPAD_ENABLES_REG,spad_map,_struct="6B")
        # Exact source register program, split only at readiness waits above/below.
        program=((0xFF,1),(0x00,0),(0xFF,0),(0x09,0),(0x10,0),(0x11,0),(0x24,1),(0x25,0xFF),(0x75,0),(0xFF,1),(0x4E,0x2C),(0x48,0),(0x30,0x20),(0xFF,0),(0x30,9),(0x54,0),(0x31,4),(0x32,3),(0x40,0x83),(0x46,0x25),(0x60,0),(0x27,0),(0x50,6),(0x51,0),(0x52,0x96),(0x56,8),(0x57,0x30),(0x61,0),(0x62,0),(0x64,0),(0x65,0),(0x66,0xA0),(0xFF,1),(0x22,0x32),(0x47,0x14),(0x49,0xFF),(0x4A,0),(0xFF,0),(0x7A,0x0A),(0x7B,0),(0x78,0x21),(0xFF,1),(0x23,0x34),(0x42,0),(0x44,0xFF),(0x45,0x26),(0x46,5),(0x40,0x40),(0x0E,6),(0x20,0x1A),(0x43,0x40),(0xFF,0),(0x34,3),(0x35,0x44),(0xFF,1),(0x31,4),(0x4B,9),(0x4C,5),(0x4D,4),(0xFF,0),(0x44,0),(0x45,0x20),(0x47,8),(0x48,0x28),(0x67,0),(0x70,4),(0x71,1),(0x72,0xFE),(0x76,0),(0x77,0),(0xFF,1),(0x0D,1),(0xFF,0),(0x80,1),(0x01,0xF8),(0xFF,1),(0x8E,1),(0x00,1),(0xFF,0),(0x80,0))
        self._config(*program)
        self._register(INTERRUPT_GPIO_REG,0x04); self._flag(GPIO_MUX_ACTIVE_HIGH_REG,4,False); self._register(INTERRUPT_CLEAR_REG,1)
        self._register(SYSTEM_SEQUENCE_REG,1); await self._calibrate_async(0x40)
        self._register(SYSTEM_SEQUENCE_REG,2); await self._calibrate_async(0x00)
        self._register(SYSTEM_SEQUENCE_REG,0xE8)
        self.set_measurement_timing_budget(self.measurement_timing_budget_us)
        self._initialized=True

    async def _wait_register_clear_async(self, register, mask, timeout_ms):
        started=time.ticks_ms()
        while self._register(register)&mask:
            if time.ticks_diff(time.ticks_ms(),started)>=timeout_ms: raise RuntimeError("timeout")
            await asyncio.sleep_ms(1)

    async def _wait_interrupt_async(self, timeout_ms):
        started=time.ticks_ms()
        while (self._register(RESULT_INTERRUPT_STATUS_REG)&7)==0:
            if time.ticks_diff(time.ticks_ms(),started)>=timeout_ms: raise RuntimeError("timeout")
            await asyncio.sleep_ms(1)

    async def start_async(self, period=0):
        if not self._initialized: await self.initialize_async()
        super().start(period)

    async def read_async(self, timeout_ms=IO_TIMEOUT_MS):
        if not self._initialized: await self.initialize_async()
        if not self._started:
            self._config((0x80,1),(0xFF,1),(0x00,0),(0x91,self._stop_variable),(0x00,1),(0xFF,0),(0x80,0),(SYSRANGE_START_REG,1))
            await self._wait_register_clear_async(SYSRANGE_START_REG,1,timeout_ms)
        await self._wait_interrupt_async(timeout_ms)
        value=self._register(RESULT_RANGE_STATUS_REG+10,_struct=">H")
        self._register(INTERRUPT_CLEAR_REG,1)
        return value

    async def stop_async(self):
        if self._started: super().stop()

    async def aclose(self):
        await self.stop_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
