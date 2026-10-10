# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : Peter Hinch, async adaptation by GraftSense
# @File    : bno055_async.py
# @Description : Cooperative BNO055 I2C driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
CHIP_ID = 0xA0
CONFIG_MODE = 0x00
NDOF_MODE = 0x0C
POWER_NORMAL = 0x00
POWER_SUSPEND = 0x02
REG_CHIP_ID = 0x00
REG_CALIBRATION = 0x35
REG_MODE = 0x3D
REG_POWER = 0x3E
REG_TRIGGER = 0x3F
REG_TEMP = 0x34

# ======================================== 功能函数 ============================================
def _signed16(low: int, high: int) -> int:
    value = (high << 8) | low
    return value if value < 0x8000 else value - 0x10000


# ======================================== 自定义类 ============================================
class BNO055Async:
    """BNO055 的协作式 I2C 异步适配器。

    BNO055 cooperative I2C async adapter. 复位时的设备规定等待在协程中让出；
    单次 I2C 寄存器事务仍为短时同步操作，并由同一把锁串行化。
    """

    def __init__(self, i2c, address: int = 0x28, crystal: bool = True) -> None:
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must support memory transactions")
        if not isinstance(address, int) or address < 0 or address > 0x7f:
            raise ValueError("address must be a 7-bit I2C address")
        if not isinstance(crystal, bool):
            raise ValueError("crystal must be bool")
        self._i2c = i2c
        self._address = address
        self._crystal = crystal
        self._lock = asyncio.Lock()
        self._started = False
        self._closed = False

    async def start(self) -> None:
        """Verify and reset the device without blocking conversion waits."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("driver is closed")
            if self._started:
                return
            if self._read_byte(REG_CHIP_ID) != CHIP_ID:
                raise RuntimeError("BNO055 chip ID mismatch")
            self._write_byte(REG_MODE, CONFIG_MODE)
            self._write_byte(REG_TRIGGER, 0x20)
        await asyncio.sleep_ms(700)
        async with self._lock:
            self._write_byte(REG_POWER, POWER_NORMAL)
            self._write_byte(0x07, 0x00)
            self._write_byte(REG_TRIGGER, 0x80 if self._crystal else 0x00)
        await asyncio.sleep_ms(500 if self._crystal else 10)
        async with self._lock:
            self._write_byte(REG_MODE, NDOF_MODE)
            self._started = True

    async def mode_async(self, new_mode=None) -> int:
        """Read or change operating mode; mode-change waits yield cooperatively."""
        if new_mode is not None and (not isinstance(new_mode, int) or new_mode < 0 or new_mode > NDOF_MODE):
            raise ValueError("new_mode must be a BNO055 mode")
        async with self._lock:
            old_mode = self._read_byte(REG_MODE)
            if new_mode is None:
                return old_mode
            self._write_byte(REG_MODE, CONFIG_MODE)
        await asyncio.sleep_ms(20)
        if new_mode != CONFIG_MODE:
            async with self._lock:
                self._write_byte(REG_MODE, new_mode)
            await asyncio.sleep_ms(10)
        return old_mode

    async def external_crystal_async(self) -> bool:
        return bool(await self._read_async(REG_TRIGGER, 1)[0] & 0x80)

    async def cal_status_async(self) -> tuple:
        value = (await self._read_async(REG_CALIBRATION, 1))[0]
        return ((value >> 6) & 3, (value >> 4) & 3, (value >> 2) & 3, value & 3)

    async def temperature_async(self) -> int:
        value = (await self._read_async(REG_TEMP, 1))[0]
        return value if value < 128 else value - 256

    async def accel_async(self) -> tuple:
        return await self._scaled_tuple_async(0x08, 1 / 100, 3)

    async def mag_async(self) -> tuple:
        return await self._scaled_tuple_async(0x0e, 1 / 16, 3)

    async def gyro_async(self) -> tuple:
        return await self._scaled_tuple_async(0x14, 1 / 16, 3)

    async def euler_async(self) -> tuple:
        return await self._scaled_tuple_async(0x1a, 1 / 16, 3)

    async def quaternion_async(self) -> tuple:
        return await self._scaled_tuple_async(0x20, 1 / 16384, 4)

    async def lin_acc_async(self) -> tuple:
        return await self._scaled_tuple_async(0x28, 1 / 100, 3)

    async def gravity_async(self) -> tuple:
        return await self._scaled_tuple_async(0x2e, 1 / 100, 3)

    async def aclose(self) -> None:
        if self._closed:
            return
        async with self._lock:
            try:
                self._write_byte(REG_POWER, POWER_SUSPEND)
            finally:
                self._closed = True
                self._started = False

    def deinit(self) -> None:
        """Mark this adapter closed; use aclose() to send the suspend command."""
        self._closed = True
        self._started = False

    async def _read_async(self, register: int, count: int) -> bytes:
        async with self._lock:
            if not self._started and register != REG_CHIP_ID:
                raise RuntimeError("call start before reading BNO055")
            try:
                return self._i2c.readfrom_mem(self._address, register, count)
            except OSError as exc:
                raise RuntimeError("I2C read failed at reg 0x%02X" % register) from exc

    async def _scaled_tuple_async(self, register: int, scale: float, count: int) -> tuple:
        raw = await self._read_async(register, count * 2)
        return tuple(_signed16(raw[index], raw[index + 1]) * scale for index in range(0, count * 2, 2))

    def _read_byte(self, register: int) -> int:
        try:
            return self._i2c.readfrom_mem(self._address, register, 1)[0]
        except OSError as exc:
            raise RuntimeError("I2C read failed at reg 0x%02X" % register) from exc

    def _write_byte(self, register: int, value: int) -> None:
        try:
            self._i2c.writeto_mem(self._address, register, bytes((value,)))
        except OSError as exc:
            raise RuntimeError("I2C write failed at reg 0x%02X" % register) from exc


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
