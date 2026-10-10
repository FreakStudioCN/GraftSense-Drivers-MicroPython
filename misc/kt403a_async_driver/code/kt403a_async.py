import time
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


class KT403AAsync:
    DEVICE_U_DISK = 1
    DEVICE_SD = 2
    DEVICE_AUX = 3
    DEVICE_SLEEP = 4
    DEVICE_FLASH = 5
    EQ_NORMAL = 0
    EQ_POP = 1
    EQ_ROCK = 2
    EQ_JAZZ = 3
    EQ_CLASSIC = 4
    EQ_BASS = 5

    def __init__(self, uart, device=None, volume=70, eq=None, timeout_ms=300):
        self._uart = uart
        self._device = device if device else self.DEVICE_SD
        self._timeout_ms = timeout_ms
        self._lock = asyncio.Lock()
        self._initial_volume = volume
        self._initial_eq = eq if eq is not None else self.EQ_NORMAL

    async def initialize_async(self):
        await self.SetDevice_async(self._device)
        await self.SetVolume_async(self._initial_volume)
        await self.SetEqualizer_async(self._initial_eq)

    async def _send_async(self, cmd, data_l=0, data_h=0):
        self._uart.write(bytes((0x7e, 0xff, 0x06, cmd, 0, data_h, data_l, 0xef)))
        await asyncio.sleep_ms(200 if cmd == 0x09 else 1000 if cmd == 0x0c else 30)

    async def _query_async(self, cmd, data_l=0, data_h=0):
        async with self._lock:
            while self._uart.any():
                self._uart.read()
            await self._send_async(cmd, data_l, data_h)
            last = None
            started = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), started) < self._timeout_ms:
                if self._uart.any():
                    frame = self._uart.read(10)
                    if frame and len(frame) == 10 and frame[0] == 0x7e and frame[1] == 0xff and frame[2] == 0x06 and frame[9] == 0xef:
                        last = (frame[3], (frame[5] << 8) | frame[6])
                    continue
                await asyncio.sleep_ms(5)
            return last

    async def _command_async(self, cmd, data_l=0, data_h=0):
        async with self._lock:
            await self._send_async(cmd, data_l, data_h)

    async def PlayNext_async(self): await self._command_async(0x01)
    async def PlayPrevious_async(self): await self._command_async(0x02)
    async def PlaySpecific_async(self, track_index): await self._command_async(0x03, track_index % 256, track_index // 256)
    async def VolumeUp_async(self): await self._command_async(0x04)
    async def VolumeDown_async(self): await self._command_async(0x05)
    async def SetVolume_async(self, percent): await self._command_async(0x06, int(max(0, min(100, percent)) * 0x1e / 100))
    async def SetEqualizer_async(self, eq): await self._command_async(0x07, max(0, min(5, eq)))
    async def RepeatCurrent_async(self): await self._command_async(0x08)
    async def SetDevice_async(self, device):
        self._device = device
        await self._command_async(0x09, device)
    async def SetLowPowerOn_async(self): await self._command_async(0x0a)
    async def SetLowPowerOff_async(self): await self.SetDevice_async(self._device)
    async def ResetChip_async(self): await self._command_async(0x0c)
    async def Play_async(self): await self._command_async(0x0d)
    async def Pause_async(self): await self._command_async(0x0e)
    async def PlaySpecificInFolder_async(self, folder_index, track_index): await self._command_async(0x0f, track_index, folder_index)
    async def EnableLoopAll_async(self): await self._command_async(0x11, 1)
    async def DisableLoopAll_async(self): await self._command_async(0x11, 0)
    async def PlayFolder_async(self, folder_index): await self._command_async(0x12, folder_index)
    async def Stop_async(self): await self._command_async(0x16)
    async def LoopFolder_async(self, folder_index): await self._command_async(0x17, folder_index)
    async def RandomAll_async(self): await self._command_async(0x18)
    async def EnableLoop_async(self): await self._command_async(0x19, 0)
    async def DisableLoop_async(self): await self._command_async(0x19, 1)
    async def EnableDAC_async(self): await self._command_async(0x1a, 0)
    async def DisableDAC_async(self): await self._command_async(0x1a, 1)

    async def GetState_async(self):
        result = await self._query_async(0x42)
        return result[1] if result else None
    async def GetVolume_async(self):
        result = await self._query_async(0x43)
        return result[1] if result else None
    async def GetEqualizer_async(self):
        result = await self._query_async(0x44)
        return result[1] if result else None
    async def GetFilesCount_async(self, device=None):
        code = {self.DEVICE_U_DISK: 0x47, self.DEVICE_SD: 0x48, self.DEVICE_FLASH: 0x49}.get(device or self._device)
        if code is None: return None
        result = await self._query_async(code)
        return result[1] if result else None
    async def GetFolderFilesCount_async(self, folder_index):
        result = await self._query_async(0x4e, folder_index)
        return result[1] if result else None
    async def IsStopped_async(self): return (await self.GetState_async()) == 0
    async def IsPlaying_async(self): return (await self.GetState_async()) == 1
    async def IsPaused_async(self): return (await self.GetState_async()) == 2

    async def aclose(self):
        self._uart = None
