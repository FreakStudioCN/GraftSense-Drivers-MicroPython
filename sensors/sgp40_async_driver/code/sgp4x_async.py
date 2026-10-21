# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : Roman Shevchik, async adaptation by GraftSense
# @File    : sgp4x_async.py
# @Description : Cooperative SGP40 and SGP41 command driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
try:
    from collections import namedtuple
except ImportError:
    namedtuple = None

# ======================================== 全局变量 ============================================
I2C_DEFAULT_ADDR = 0x59
CMD_CONDITIONING = 0x2612
CMD_MEASURE_RAW = 0x260F
CMD_SELF_TEST = 0x280E
CMD_HEATER_OFF = 0x3615
CMD_SERIAL = 0x3682
SerialNumber = namedtuple("SerialNumber", "word_0 word_1 word_2")
MeasuredValues = namedtuple("MeasuredValues", "VOC NOx")

# ======================================== 功能函数 ============================================
def _crc8(data: bytes) -> int:
    crc = 0xff
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xff if crc & 0x80 else (crc << 1) & 0xff
    return crc


def _word(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


# ======================================== 自定义类 ============================================
class SGP4XAsync:
    """SGP40/SGP41 协作式命令驱动。

    Source command bytes, CRC-8 and response delays are preserved. One adapter
    transaction is synchronous but serialized; the device conversion windows yield.
    """

    def __init__(self, adapter, address: int = I2C_DEFAULT_ADDR, sensor_id: int = 0, check_crc: bool = True) -> None:
        if not hasattr(adapter, "write") or not hasattr(adapter, "read"):
            raise ValueError("adapter must provide write and read")
        if not isinstance(address, int) or address != I2C_DEFAULT_ADDR:
            raise ValueError("address must be 0x59")
        if sensor_id not in (0, 1):
            raise ValueError("sensor_id must be 0 or 1")
        if not isinstance(check_crc, bool):
            raise ValueError("check_crc must be bool")
        self._adapter = adapter
        self._address = address
        self._sensor_id = sensor_id
        self._check_crc = check_crc
        self._lock = asyncio.Lock()
        self._closed = False
        self._last_cmd_code = None

    def get_sensor_id(self) -> int:
        return self._sensor_id

    def get_last_cmd_code(self):
        return self._last_cmd_code

    async def get_id_async(self):
        answer = await self._transaction_async(CMD_SERIAL, 9, 1)
        return SerialNumber(_word(answer, 0), _word(answer, 3), _word(answer, 6))

    async def execute_self_test_async(self) -> int:
        answer = await self._transaction_async(CMD_SELF_TEST, 3, 320)
        return _word(answer, 0)

    async def execute_conditioning_async(self, rel_hum: int = 50, temperature: int = 25):
        if self._sensor_id != 1:
            raise RuntimeError("conditioning is only available on SGP41")
        answer = await self._transaction_async(CMD_CONDITIONING, 3, 50, rel_hum, temperature)
        return MeasuredValues(_word(answer, 0), None)

    async def measure_raw_signal_async(self, rel_hum: int = 50, temperature: int = 25):
        size = 3 if self._sensor_id == 0 else 6
        delay = 30 if self._sensor_id == 0 else 50
        answer = await self._transaction_async(CMD_MEASURE_RAW, size, delay, rel_hum, temperature)
        return MeasuredValues(_word(answer, 0), None if self._sensor_id == 0 else _word(answer, 3))

    async def turn_heater_off_async(self) -> None:
        await self._transaction_async(CMD_HEATER_OFF, 0, 1)

    async def aclose(self) -> None:
        if not self._closed:
            await self.turn_heater_off_async()
            self._closed = True

    def deinit(self) -> None:
        self._closed = True

    async def _transaction_async(self, command: int, response_size: int, delay_ms: int, rel_hum=None, temperature=None):
        if self._closed:
            raise RuntimeError("driver is closed")
        frame = self._command_frame(command, rel_hum, temperature)
        async with self._lock:
            try:
                self._adapter.write(self._address, frame)
            except OSError as exc:
                raise RuntimeError("I2C write command failed") from exc
            self._last_cmd_code = command
        await asyncio.sleep_ms(delay_ms)
        if response_size == 0:
            return None
        async with self._lock:
            try:
                answer = self._adapter.read(self._address, response_size)
            except OSError as exc:
                raise RuntimeError("I2C read answer failed") from exc
        if len(answer) != response_size:
            raise RuntimeError("I2C response length mismatch")
        if self._check_crc:
            self._verify_crc(answer)
        return answer

    def _command_frame(self, command: int, rel_hum, temperature) -> bytes:
        if (rel_hum is None) != (temperature is None):
            raise ValueError("humidity and temperature must be provided together")
        frame = command.to_bytes(2, "big")
        if rel_hum is None:
            return frame
        if not isinstance(rel_hum, int) or rel_hum < 0 or rel_hum > 100:
            raise ValueError("rel_hum must be in range 0..100")
        if not isinstance(temperature, int) or temperature < -45 or temperature > 130:
            raise ValueError("temperature must be in range -45..130")
        rh = round(65.35 * rel_hum).to_bytes(2, "big")
        temp = round(374.4857142857 * (45 + temperature)).to_bytes(2, "big")
        return frame + rh + bytes((_crc8(rh),)) + temp + bytes((_crc8(temp),))

    def _verify_crc(self, answer: bytes) -> None:
        for offset in range(0, len(answer), 3):
            if _crc8(answer[offset:offset + 2]) != answer[offset + 2]:
                raise ValueError("CRC mismatch")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
