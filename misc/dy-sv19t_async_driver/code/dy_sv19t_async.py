# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 00:00
# @Author  : 侯钧瀚
# @File    : dy_sv19t_async.py
# @Description : DY-SV19T UART cooperative async driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from _gs_dy_sv19t_dy_sv19t import DYSV19T

# ======================================== 全局变量 ============================================
_POLL_MS = 5

# ======================================== 功能函数 ============================================
def _ticks_expired(deadline: int) -> bool:
    return time.ticks_diff(deadline, time.ticks_ms()) <= 0

# ======================================== 自定义类 ============================================
class DYSV19TAsync:
    """DY-SV19T 的协作式 UART 异步适配器。

    同步控制帧写入保持为短暂、残余阻塞操作；响应帧采用有界轮询，且全部 UART
    事务由一个锁串行化，避免多个协程争用同一 UART 接收缓冲区。
    """

    DISK_USB = DYSV19T.DISK_USB
    DISK_SD = DYSV19T.DISK_SD
    DISK_FLASH = DYSV19T.DISK_FLASH
    VOLUME_MAX = DYSV19T.VOLUME_MAX
    MODE_SINGLE_STOP = DYSV19T.MODE_SINGLE_STOP
    EQ_ROCK = DYSV19T.EQ_ROCK
    CH_MP3 = DYSV19T.CH_MP3

    def __init__(self, uart, timeout_ms: int = 600) -> None:
        if uart is None or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide read and write")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        self._uart = uart
        self._timeout_ms = timeout_ms
        self._sync = DYSV19T(uart, timeout_ms=timeout_ms)
        self._lock = asyncio.Lock()
        self._closed = False

    async def _write_async(self, command: int, data: bytes = b"") -> None:
        if self._closed:
            raise RuntimeError("driver is closed")
        frame = self._sync._build_frame(command, data)
        try:
            self._uart.write(frame)
        except OSError as exc:
            raise RuntimeError("UART write failed") from exc
        await asyncio.sleep_ms(0)

    async def _read_frame_async(self, command: int, timeout_ms: int = None):
        if timeout_ms is None:
            timeout_ms = self._timeout_ms
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        buffer = bytearray()
        while not _ticks_expired(deadline):
            try:
                available = self._uart.any() if hasattr(self._uart, "any") else 0
                chunk = self._uart.read(available) if available else None
            except OSError as exc:
                raise RuntimeError("UART read failed") from exc
            if chunk:
                buffer.extend(chunk)
                while len(buffer) >= 4:
                    try:
                        start = buffer.index(0xAA)
                    except ValueError:
                        buffer = bytearray()
                        break
                    if start:
                        del buffer[:start]
                    if len(buffer) < 4:
                        break
                    size = 4 + buffer[2]
                    if len(buffer) < size:
                        break
                    frame = bytes(buffer[:size])
                    del buffer[:size]
                    if (sum(frame[:-1]) & 0xFF) != frame[-1]:
                        continue
                    if frame[1] == command:
                        return frame[3:-1]
            await asyncio.sleep_ms(_POLL_MS)
        return None

    async def _command_async(self, command: int, data: bytes = b"") -> None:
        async with self._lock:
            await self._write_async(command, data)

    async def _query_async(self, command: int, timeout_ms: int = None):
        async with self._lock:
            await self._write_async(command)
            return await self._read_frame_async(command, timeout_ms)

    async def set_volume_async(self, volume: int) -> None:
        if not isinstance(volume, int) or volume < 0 or volume > 30:
            raise ValueError("volume must be 0..30")
        await self._command_async(0x13, bytes([volume]))
        self._sync.volume = volume

    async def set_eq_async(self, eq: int) -> None:
        self._sync._validate_eq(eq)
        await self._command_async(0x1A, bytes([eq]))
        self._sync.eq = eq

    async def set_play_mode_async(self, mode: int) -> None:
        self._sync._validate_mode(mode)
        await self._command_async(0x18, bytes([mode]))
        self._sync.play_mode = mode

    async def set_dac_channel_async(self, channel: int) -> None:
        self._sync._validate_channel(channel)
        await self._command_async(0x1D, bytes([channel]))
        self._sync.dac_channel = channel

    async def enable_play_time_send_async(self) -> None:
        await self._command_async(0x25)

    async def disable_play_time_send_async(self) -> None:
        await self._command_async(0x26)

    async def read_play_time_async(self, timeout_ms: int = None):
        """Read one source 0x25 automatic play-time report in task context."""
        async with self._lock:
            data = await self._read_frame_async(0x25, timeout_ms)
        return (data[0], data[1], data[2]) if data and len(data) == 3 else None

    async def play_async(self) -> None:
        await self._command_async(0x02)
        self._sync.play_state = DYSV19T.PLAY_PLAY

    async def stop_async(self) -> None:
        await self._command_async(0x04)
        self._sync.play_state = DYSV19T.PLAY_STOP

    async def query_status_async(self, timeout_ms: int = None):
        data = await self._query_async(0x01, timeout_ms)
        if data and len(data) == 1:
            self._sync.play_state = data[0]
            return data[0]
        return None

    async def query_current_disk_async(self, timeout_ms: int = None):
        data = await self._query_async(0x0A, timeout_ms)
        if data and len(data) == 1:
            self._sync.current_disk = data[0]
            return data[0]
        return None

    async def query_current_track_async(self, timeout_ms: int = None):
        data = await self._query_async(0x0D, timeout_ms)
        return ((data[0] << 8) | data[1]) if data and len(data) == 2 else None

    async def query_current_track_time_async(self, timeout_ms: int = None):
        data = await self._query_async(0x24, timeout_ms)
        return (data[0], data[1], data[2]) if data and len(data) == 3 else None

    async def query_short_filename_async(self, timeout_ms: int = None):
        data = await self._query_async(0x1E, timeout_ms)
        return data.decode("ascii") if data else None

    async def query_total_tracks_async(self, timeout_ms: int = None):
        data = await self._query_async(0x0C, timeout_ms)
        return ((data[0] << 8) | data[1]) if data and len(data) == 2 else None

    async def query_folder_first_track_async(self, timeout_ms: int = None):
        data = await self._query_async(0x11, timeout_ms)
        return ((data[0] << 8) | data[1]) if data and len(data) == 2 else None

    async def query_folder_total_tracks_async(self, timeout_ms: int = None):
        data = await self._query_async(0x12, timeout_ms)
        return ((data[0] << 8) | data[1]) if data and len(data) == 2 else None

    async def query_online_disks_async(self, timeout_ms: int = None):
        data = await self._query_async(0x09, timeout_ms)
        return data[0] if data and len(data) == 1 else None

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            if hasattr(self._uart, "deinit"):
                self._uart.deinit()

    def deinit(self) -> None:
        self._closed = True

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
