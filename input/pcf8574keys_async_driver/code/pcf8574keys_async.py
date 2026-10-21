# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:00
# @Author  : 缪贵成
# @File    : pcf8574keys_async.py
# @Description : PCF8574 five-way key asynchronous driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
__version__ = "1.0.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
DEFAULT_ADDRESS = 0x20
DEBOUNCE_MS = 20
SCAN_INTERVAL_MS = 10
KEYS_MAP = {
    "UP": 0, "DOWN": 3, "LEFT": 1, "RIGHT": 2,
    "CENTER": 4, "SW1": 5, "SW2": 7,
}

# ======================================== 功能函数 ============================================
def _validate_pin(pin: int) -> int:
    if not isinstance(pin, int) or pin < 0 or pin > 7:
        raise ValueError("pin must be an integer from 0 to 7")
    return pin

# ======================================== 自定义类 ============================================
class PCF8574Async:
    """PCF8574 的短时 I2C 异步适配器。

    I2C 单字节传输仍在事件循环内同步完成；锁保证多个协程不会交叉读写。
    """
    __slots__ = ("_i2c", "_address", "_port", "_lock", "_closed")

    def __init__(self, i2c: object, address: int = DEFAULT_ADDRESS) -> None:
        if not hasattr(i2c, "readfrom_into") or not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide readfrom_into and writeto")
        if not isinstance(address, int) or address < 0x20 or address > 0x27:
            raise ValueError("address must be from 0x20 to 0x27")
        self._i2c = i2c
        self._address = address
        self._port = bytearray(1)
        self._lock = asyncio.Lock()
        self._closed = False

    async def read_port_async(self) -> int:
        async with self._lock:
            self._require_open()
            try:
                self._i2c.readfrom_into(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C read failed") from exc
            return self._port[0]

    async def write_port_async(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("value must be an integer")
        async with self._lock:
            self._require_open()
            self._port[0] = value & 0xFF
            try:
                self._i2c.writeto(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C write failed") from exc

    async def read_pin_async(self, pin: int) -> bool:
        pin = _validate_pin(pin)
        return bool((await self.read_port_async() >> pin) & 1)

    async def write_pin_async(self, pin: int, value: bool) -> None:
        pin = _validate_pin(pin)
        async with self._lock:
            self._require_open()
            try:
                self._i2c.readfrom_into(self._address, self._port)
                if value:
                    self._port[0] |= 1 << pin
                else:
                    self._port[0] &= ~(1 << pin)
                self._i2c.writeto(self._address, self._port)
            except OSError as exc:
                raise RuntimeError("PCF8574 I2C pin transaction failed") from exc

    def deinit(self) -> None:
        self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("PCF8574 is deinitialized")


class PCF8574KeysAsync:
    """PCF8574 五向按键的协作式扫描器。"""
    __slots__ = (
        "_pcf", "_keys", "_callback", "_state", "_last_raw", "_changed_ms",
        "_elapsed_ms", "_task", "_running", "_error",
    )

    def __init__(self, pcf: PCF8574Async, keys: dict = KEYS_MAP,
                 callback: callable = None) -> None:
        if not isinstance(pcf, PCF8574Async):
            raise ValueError("pcf must be a PCF8574Async instance")
        if not isinstance(keys, dict) or not keys:
            raise ValueError("keys must be a non-empty dictionary")
        if callback is not None and not callable(callback):
            raise ValueError("callback must be callable")
        for pin in keys.values():
            _validate_pin(pin)
        self._pcf = pcf
        self._keys = dict(keys)
        self._callback = callback
        self._state = {name: False for name in keys}
        self._last_raw = dict(self._state)
        self._changed_ms = {name: DEBOUNCE_MS for name in keys}
        self._elapsed_ms = 0
        self._task = None
        self._running = False
        self._error = None

    async def start(self) -> None:
        if self._running:
            return
        await self._pcf.write_port_async(0b01000000)
        self._running = True
        self._task = asyncio.create_task(self._scan_loop())

    async def stop(self) -> None:
        self._running = False
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def aclose(self) -> None:
        await self.stop()
        self._pcf.deinit()

    def read_key(self, key_name: str) -> bool:
        if key_name not in self._state:
            raise ValueError("unknown key name")
        return self._state[key_name]

    def read_all(self) -> dict:
        return dict(self._state)

    async def led_on_async(self) -> None:
        await self._pcf.write_port_async(0)

    async def led_off_async(self) -> None:
        await self._pcf.write_port_async(0b01000000)

    def last_error(self) -> object:
        return self._error

    async def _scan_loop(self) -> None:
        try:
            while self._running:
                await self._scan_once_async()
                await asyncio.sleep_ms(SCAN_INTERVAL_MS)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._error = exc
            self._running = False

    async def _scan_once_async(self) -> None:
        port = await self._pcf.read_port_async()
        self._elapsed_ms += SCAN_INTERVAL_MS
        for name, pin in self._keys.items():
            raw = bool((port >> pin) & 1)
            if raw != self._last_raw[name]:
                self._last_raw[name] = raw
                self._changed_ms[name] = self._elapsed_ms
            if raw != self._state[name] and self._elapsed_ms - self._changed_ms[name] >= DEBOUNCE_MS:
                self._state[name] = raw
                if self._callback is not None:
                    self._callback(name, raw)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
