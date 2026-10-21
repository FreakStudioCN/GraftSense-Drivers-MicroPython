"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

class PlayerAsync:
    """Async facade; each delegated call remains a short sync transaction."""

    EQ_NORMAL = 0
    EQ_POP = 1
    EQ_ROCK = 2
    EQ_JAZZ = 3
    EQ_CLASSIC = 4
    EQ_BASS = 5
    SRC_SDCARD = 1
    SRC_BUILTIN = 4
    LOOP_ALL = 0
    LOOP_FOLDER = 1
    LOOP_ONE = 2
    LOOP_RAM = 3
    LOOP_ONE_STOP = 4
    LOOP_NONE = 4
    STATUS_STOPPED = 0
    STATUS_PLAYING = 1
    STATUS_PAUSED = 2
    READ_DELAY = 0.1

    def __init__(self, uart, volume: int = 20):
        if uart is None or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise TypeError("uart must provide read and write")
        if not isinstance(volume, int) or not 0 <= volume <= 30:
            raise ValueError("volume must be an integer between 0 and 30")
        self.uart = uart
        self._initial_volume = volume
        self._initialized = False
        self._closed = False
        self._lock = asyncio.Lock()

    async def _write_locked_async(self, command):
        if not isinstance(command, list) or not all(isinstance(value, int) for value in command):
            raise TypeError("command must be a list of integers")
        await self._read_uart_async()
        self.uart.write(bytes([0x7E, len(command) + 1] + command + [0xEF]))

    async def _read_uart_async(self, nbytes=None):
        """The only UART reader; callers hold _lock for a complete transaction."""
        return self.uart.read() if nbytes is None else self.uart.read(nbytes)

    async def _command_async(self, command):
        if self._closed:
            raise RuntimeError("player is closed")
        async with self._lock:
            await self._write_locked_async(command)

    async def initialize_async(self):
        if self._closed:
            raise RuntimeError("player is closed")
        async with self._lock:
            if self._initialized:
                return
            await self._read_uart_async()
            await self._write_locked_async([0x0C])
            await asyncio.sleep_ms(500)
            await self._write_locked_async([0x06, self._initial_volume])
            self._initialized = True

    async def clean_up_async(self):
        if not self._closed:
            try:
                await self.reset_async()
            finally:
                self._closed = True
                if hasattr(self.uart, "deinit"):
                    self.uart.deinit()

    async def aclose(self):
        await self.clean_up_async()

    async def play_async(self):
        await self._command_async([0x0D])

    async def play_pause_async(self):
        status = await self.get_status_async()
        if status in (self.STATUS_PAUSED, self.STATUS_STOPPED):
            await self.play_async()
        elif status == self.STATUS_PLAYING:
            await self.pause_async()

    async def restart_async(self):
        old_volume = await self.get_volume_async()
        await self.set_volume_async(0)
        await self.next_async()
        await self.pause_async()
        await self.set_volume_async(old_volume)
        await self.prev_async()

    async def pause_async(self):
        await self._command_async([0x0E])

    async def next_async(self):
        await self._command_async([0x01])

    async def prev_async(self):
        await self._command_async([0x02])

    async def next_folder_async(self):
        await self._command_async([0x0F, 0x01])

    async def prev_folder_async(self):
        await self._command_async([0x0F, 0x00])

    async def play_by_index_async(self, file_index: int):
        await self._command_async([0x03, (file_index >> 8) & 0xFF, file_index & 0xFF])

    async def play_by_number_async(self, folder_number: int, file_number: int):
        await self._command_async([0x12, folder_number & 0xFF, file_number & 0xFF])

    async def volume_up_async(self):
        await self._command_async([0x04])

    async def volume_down_async(self):
        await self._command_async([0x05])

    async def set_volume_async(self, level: int):
        if not isinstance(level, int) or not 0 <= level <= 30:
            raise ValueError("volume must be 0..30")
        await self._command_async([0x06, level])

    async def set_equalizer_async(self, mode: int):
        await self._command_async([0x07, mode])

    async def set_looping_async(self, mode: int):
        await self._command_async([0x11, mode])

    async def set_source_async(self, source: int):
        await self._command_async([0x09, source])

    async def sleep_async(self):
        await self._command_async([0x0A])

    async def get_folder_count_async(self, source: int):
        if source == self.SRC_BUILTIN:
            return 0
        if source != self.SRC_SDCARD:
            raise ValueError("Invalid audio source")
        return await self._query_value_async(0x53)

    async def get_file_index_async(self, source: int):
        if source == self.SRC_SDCARD:
            return await self._query_value_async(0x4B)
        if source == self.SRC_BUILTIN:
            return (await self._query_value_async(0x4D)) + 1
        raise ValueError("Invalid audio source")

    async def get_name_async(self):
        async with self._lock:
            await self._write_locked_async([0x52])
            await asyncio.sleep(self.READ_DELAY)
            return await self._read_uart_async()

    async def read_buffer_async(self):
        async with self._lock:
            return await self._read_uart_async()

    async def read_bytes_async(self):
        async with self._lock:
            data = await self._read_uart_async(4)
            return int(data, 16) if data else -1

    async def write_bytes_async(self, b: list):
        await self._command_async(b)

    async def _query_value_async(self, command):
        async with self._lock:
            await self._write_locked_async([command])
            await asyncio.sleep(self.READ_DELAY)
            data = await self._read_uart_async(4)
            return int(data, 16) if data else -1

    async def reset_async(self):
        async with self._lock:
            await self._write_locked_async([0x0C])
            await asyncio.sleep_ms(500)

    async def get_status_async(self):
        async with self._lock:
            await self._write_locked_async([0x42])
            await asyncio.sleep(self.READ_DELAY)
            status = await self._read_uart_async()
            await asyncio.sleep(self.READ_DELAY)
            return int(status) if status and status.isdigit() else -1

    async def get_volume_async(self):
        return await self._query_value_async(0x43)

    async def get_equalizer_async(self):
        return await self._query_value_async(0x44)

    async def get_looping_async(self):
        return await self._query_value_async(0x45)

    async def get_file_count_async(self, source: int):
        if source not in (self.SRC_SDCARD, self.SRC_BUILTIN):
            raise ValueError("Invalid audio source")
        return await self._query_value_async(0x47 if source == self.SRC_SDCARD else 0x49)

    async def get_position_async(self):
        return await self._query_value_async(0x50)

    async def get_length_async(self):
        return await self._query_value_async(0x51)

    async def get_version_async(self):
        return await self._query_value_async(0x46)
