"""Async CC1101 facade preserving the source SPI protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from cc1101 import CC1101

try:
    from time import sleep_us
except ImportError:
    import time
    def sleep_us(value): time.sleep(value / 1000000)

try:
    from time import ticks_diff, ticks_ms
except ImportError:
    import time

    def ticks_ms():
        return int(time.time() * 1000)

    def ticks_diff(new, old):
        return new - old


class CC1101Async(CC1101):
    """Explicit async entry points; bounded SPI transfers remain atomic."""

    def __init__(self, spi, cs, gdo0=None, crystal_hz=26000000, reset=True, debug=False):
        if not hasattr(spi, "write") or not hasattr(spi, "write_readinto"):
            raise TypeError("spi must provide write() and write_readinto()")
        if not hasattr(cs, "value"):
            raise TypeError("cs must be a machine.Pin-like object")
        if crystal_hz <= 0: raise ValueError("crystal_hz must be positive")
        if not isinstance(debug, bool): raise ValueError("debug must be bool")
        self._spi = spi; self._cs = cs; self._gdo0 = gdo0
        self._crystal_hz = crystal_hz; self._debug = debug
        self._tx1 = bytearray(1); self._rx1 = bytearray(1); self._buf2 = bytearray(2)
        self._cs.value(1)
        self._reset_requested = reset; self._initialized_async = False

    async def initialize_async(self):
        if not self._initialized_async:
            if self._reset_requested:
                await self.reset_async()
            self._initialized_async = True

    async def aclose(self) -> None:
        self.deinit()

    def _reset_pulse_sync(self) -> None:
        """Keep the source's strict CS pulse train contiguous."""
        self._cs.value(1)
        sleep_us(5)
        self._cs.value(0)
        sleep_us(10)
        self._cs.value(1)
        sleep_us(45)
        self.strobe(self._SRES)

    async def reset_async(self) -> None:
        self._reset_pulse_sync()
        await asyncio.sleep_ms(1)

    async def strobe_async(self, command: int) -> int: return self.strobe(command)
    async def read_reg_async(self, register: int) -> int: return self.read_reg(register)
    async def write_reg_async(self, register: int, value: int) -> None: self.write_reg(register, value)
    async def read_burst_async(self, register: int, length: int) -> bytearray: return self.read_burst(register, length)
    async def write_burst_async(self, register: int, data) -> None: self.write_burst(register, data)
    async def read_status_reg_async(self, register: int) -> int: return self.read_status_reg(register)
    async def partnum_async(self) -> int: return self.partnum()
    async def version_async(self) -> int: return self.version()
    async def marcstate_async(self) -> int: return self.marcstate()
    async def rssi_raw_async(self) -> int: return self.rssi_raw()
    async def rssi_dbm_async(self) -> int: return self.rssi_dbm()
    async def available_async(self) -> int: return self.available()
    async def tx_bytes_async(self) -> int: return self.tx_bytes()
    async def verify_async(self) -> tuple: return self.verify()
    async def configure_async(self, registers) -> None: self.configure(registers)
    async def set_frequency_async(self, freq_hz: int) -> None: self.set_frequency(freq_hz)
    async def set_packet_length_async(self, length: int) -> None: self.set_packet_length(length)
    async def set_pa_table_async(self, values) -> None: self.set_pa_table(values)
    async def idle_async(self) -> None: self.idle()
    async def rx_async(self) -> None: self.rx()
    async def tx_async(self) -> None: self.tx()
    async def power_down_async(self) -> None: self.power_down()
    async def flush_rx_async(self) -> None: self.flush_rx()
    async def flush_tx_async(self) -> None: self.flush_tx()

    async def wait_for_state_async(self, state: int, timeout_ms: int = 1000) -> bool:
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            current = self.marcstate()
            if current == state:
                return True
            if current == self._STATE_RXFIFO_OVERFLOW:
                self.flush_rx()
                raise RuntimeError('CC1101 RX FIFO overflow detected in wait_for_state')
            if current == self._STATE_TXFIFO_UNDERFLOW:
                self.flush_tx()
                raise RuntimeError('CC1101 TX FIFO underflow detected in wait_for_state')
            await asyncio.sleep_ms(2)
        raise RuntimeError('CC1101 state timeout waiting for 0x%02X' % state)

    async def send_packet_async(self, payload, timeout_ms: int = 1000, variable_length: bool = True) -> None:
        data = bytes(payload)
        if variable_length:
            if len(data) > 255:
                raise ValueError('variable length payload must be <= 255 bytes')
            fifo = bytes([len(data)]) + data
        else:
            fifo = data
        self.idle()
        self.flush_tx()
        self.write_burst(self._TXFIFO, fifo)
        self.tx()
        await self.wait_for_state_async(self._STATE_IDLE, timeout_ms)

    async def read_packet_async(self, timeout_ms: int = 0, with_status: bool = False):
        start = ticks_ms()
        while self.available() == 0:
            if timeout_ms <= 0 or ticks_diff(ticks_ms(), start) >= timeout_ms:
                return None
            await asyncio.sleep_ms(2)
        length = self.read_burst(self._RXFIFO, 1)[0]
        if length == 0:
            return b''
        total = length + (2 if with_status else 0)
        raw = self.read_burst(self._RXFIFO, total)
        payload = bytes(raw[:length])
        return (payload, raw[length:]) if with_status else payload

    async def deinit_async(self) -> None:
        self.deinit()