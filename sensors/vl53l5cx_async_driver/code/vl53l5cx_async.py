"""Cooperative VL53L5CX high-level state-machine adapter.

The inherited driver intentionally retains its synchronous property API.  This
adapter provides separate awaitable setup and ranging operations, so an async
application never invokes the source driver's blocking protocol sequences.
"""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import struct
import time
import vl53l5cx as _core
from vl53l5cx.mp import VL53L5CXMP
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VL53L5CXMPAsync(VL53L5CXMP):
    """Awaitable VL53L5CX protocol flow without changing source properties."""

    def __init__(self, i2c, addr=0x29, lpn=None):
        super().__init__(i2c, addr=addr, lpn=lpn)
        self._async_initialized = False
        self._async_ranging_started = False

    async def reset_async(self):
        if not self._lpn:
            raise ValueError("no LPN pin provided")
        self._lpn.value(0)
        await asyncio.sleep_ms(100)
        self._lpn.value(1)
        await asyncio.sleep_ms(100)

    async def _poll_for_answer_async(self, size, pos, reg16, mask, val,
                                     timeout_ms=2000, poll_ms=10):
        """Poll one bounded I2C read at a time and yield between attempts."""
        started = time.ticks_ms()
        while True:
            data = self._rd_multi(reg16, size)
            if data and len(data) > pos and ((data[pos] & mask) == val):
                return 0
            if size >= 4 and len(data) >= 3 and data[2] >= 0x7f:
                raise ValueError("poll_for_answer device error")
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise ValueError("poll_for_answer timeout")
            await asyncio.sleep_ms(poll_ms)

    async def _dci_read_data_async(self, data, index):
        data_size = len(data)
        if data_size % 4:
            raise ValueError("DCI data size must be a multiple of four")
        cmd = bytearray(12)
        cmd[0] = index >> 8
        cmd[1] = index & 0xff
        cmd[2] = (data_size & 0xff0) >> 4
        cmd[3] = (data_size & 0x0f) << 4
        cmd[7], cmd[9], cmd[11] = 0x0f, 0x02, 0x08
        self._wr_multi(_core._UI_CMD_END - 11, cmd)
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 0x03)
        buf = self._rd_multi(_core._UI_CMD_START, data_size + 12)
        if len(buf) < data_size + 4:
            raise OSError("short VL53L5CX DCI response")
        for i in range(0, data_size, 4):
            data[i] = buf[4 + i + 3]
            data[i + 1] = buf[4 + i + 2]
            data[i + 2] = buf[4 + i + 1]
            data[i + 3] = buf[4 + i]
        return True

    async def _dci_write_data_async(self, data, index):
        data_size = len(data)
        if data_size % 4:
            raise ValueError("DCI data size must be a multiple of four")
        buf = bytearray(data_size + 12)
        buf[0], buf[1] = index >> 8, index & 0xff
        buf[2], buf[3] = (data_size & 0xff0) >> 4, (data_size & 0x0f) << 4
        for i in range(0, data_size, 4):
            buf[4 + i] = data[i + 3]
            buf[4 + i + 1] = data[i + 2]
            buf[4 + i + 2] = data[i + 1]
            buf[4 + i + 3] = data[i]
        buf[4 + data_size:] = bytes((0, 0, 0, 0x0f, 0x05, 0x01,
                                     (data_size + 8) >> 8, (data_size + 8) & 0xff))
        self._wr_multi(_core._UI_CMD_END - (data_size + 12) + 1, buf)
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 0x03)
        return True

    async def _send_offset_data_async(self, offset_data, resolution):
        buf = bytearray(offset_data)
        if resolution == _core.RESOLUTION_4X4:
            buf[0x10:0x18] = bytes((0x0f, 0x04, 0x04, 0, 0x08, 0x10, 0x10, 0x07))
            self._swap_buffer(buf)
            signal_grid = list(struct.unpack("64I", buf[0x3c:0x13c]))
            range_grid = list(struct.unpack("64h", buf[0x140:0x1c0]))
            for row in range(4):
                for col in range(4):
                    out = col + 4 * row
                    src = 2 * col + 16 * row
                    signal_grid[out] = (signal_grid[src] + signal_grid[src + 1] +
                                        signal_grid[src + 8] + signal_grid[src + 9]) // 4
                    range_grid[out] = (range_grid[src] + range_grid[src + 1] +
                                       range_grid[src + 8] + range_grid[src + 9]) // 4
            for index in range(0x10, 64):
                signal_grid[index] = 0
                range_grid[index] = 0
            buf[0x3c:0x13c] = struct.pack("64I", *signal_grid)
            buf[0x140:0x1c0] = struct.pack("64h", *range_grid)
            self._swap_buffer(buf)
        payload = bytearray(buf[8:-4])
        payload.extend(bytes((0, 0, 0, 0x0f, 0x03, 0x01, 0x01, 0xe4)))
        self._wr_multi(0x2e18, payload)
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 0x03)
        return True

    async def _send_xtalk_data_async(self, resolution):
        data = (self.config_data.xtalk4x4_data if resolution == _core.RESOLUTION_4X4
                else self.config_data.xtalk_data)
        self._wr_multi(0x2cf8, data)
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 0x03)
        return True

    async def _load_firmware_async(self, chunk_size=0x100):
        firmware = self.config_data.fw_data(chunk_size)
        for page, size in enumerate((0x8000, 0x8000, 0x5000), 9):
            self._wr_byte(0x7fff, page)
            for offset in range(0, size, chunk_size):
                self._wr_multi(offset, next(firmware))
                await asyncio.sleep_ms(0)

    async def initialize_async(self):
        """Download firmware and apply the source initialization protocol."""
        self._wr_byte(0x7fff, 0)
        for reg, value in ((0x0009, 0x04), (0x000f, 0x40), (0x000a, 0x03)):
            self._wr_byte(reg, value)
        self._rd_byte(0x7fff)
        for reg, value in ((0x000c, 1), (0x0101, 0), (0x0102, 0), (0x010a, 1),
                           (0x4002, 1), (0x4002, 0), (0x010a, 3), (0x0103, 1),
                           (0x000c, 0), (0x000f, 0x43)):
            self._wr_byte(reg, value)
        await asyncio.sleep_ms(1)
        self._wr_byte(0x000f, 0x40)
        self._wr_byte(0x000a, 1)
        await asyncio.sleep_ms(100)
        self._wr_byte(0x7fff, 0)
        await self._poll_for_answer_async(1, 0, 0x06, 0xff, 1)
        self._wr_byte(0x000e, 1)
        self._wr_byte(0x7fff, 2)
        self._wr_byte(0x03, 0x0d)
        self._wr_byte(0x7fff, 1)
        await self._poll_for_answer_async(1, 0, 0x21, 0x10, 0x10)
        self._wr_byte(0x7fff, 0)
        self._wr_byte(0x0c, 1)
        for reg, value in ((0x7fff, 0), (0x0101, 0), (0x0102, 0), (0x010a, 1),
                           (0x4002, 1), (0x4002, 0), (0x010a, 3), (0x0103, 1),
                           (0x400f, 0), (0x021a, 0x43), (0x021a, 3),
                           (0x021a, 1), (0x021a, 0), (0x0219, 0), (0x021b, 0),
                           (0x7fff, 0), (0x000c, 0), (0x7fff, 1),
                           (0x0020, 7), (0x0020, 6)):
            self._wr_byte(reg, value)
        await self._load_firmware_async()
        self._wr_byte(0x7fff, 1)
        self._wr_byte(0x7fff, 2)
        self._wr_byte(0x03, 0x0d)
        self._wr_byte(0x7fff, 1)
        await self._poll_for_answer_async(1, 0, 0x21, 0x10, 0x10)
        self._wr_byte(0x7fff, 0)
        self._wr_byte(0x0c, 1)
        for reg, value in ((0x7fff, 0), (0x0114, 0), (0x0115, 0), (0x0116, 0x42),
                           (0x0117, 0), (0x000b, 0), (0x000c, 0), (0x000b, 1)):
            self._wr_byte(reg, value)
        await self._poll_for_answer_async(1, 0, 0x06, 0xff, 0)
        self._wr_byte(0x7fff, 2)
        nvm_cmd = bytes((0x54,0,0,0x40, 0x9e,0x14,0,0xc0, 0x9e,0x20,1,0x40,
                         0x9e,0x34,0,0x40, 0x9e,0x38,4,4, 0x9f,0x38,4,2,
                         0x9f,0xb8,1,0, 0x9f,0xc8,1,0, 0,0,0,0x0f,2,2,0,0x24))
        self._wr_multi(0x2fd8, nvm_cmd)
        await self._poll_for_answer_async(4, 0, 0x2c00, 0xff, 2)
        self._offset_data = self._rd_multi(0x2c04, 492)
        await self._send_offset_data_async(self._offset_data, _core.RESOLUTION_4X4)
        await self._send_xtalk_data_async(_core.RESOLUTION_4X4)
        self._wr_multi(0x2c34, self.config_data.default_config_data)
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 3)
        await self._dci_write_data_async(bytes((self._ntpz, 0, 1, 0)), _core._DCI_PIPE_CONTROL)
        await self._dci_write_data_async(b'\x01\x00\x00\x00', _core._DCI_SINGLE_RANGE)
        self._async_initialized = True
        return 0

    async def init_async(self):
        """Compatibility-named async entry required by source API gate."""
        return await self.initialize_async()
    async def set_resolution_async(self, resolution):
        if resolution not in (_core.RESOLUTION_8X8, _core.RESOLUTION_4X4):
            raise ValueError("invalid resolution")
        buf = bytearray(16)
        await self._dci_read_data_async(buf, _core._DCI_DSS_CONFIG)
        if resolution == _core.RESOLUTION_8X8:
            buf[4], buf[6], buf[9] = 16, 16, 1
        else:
            buf[4], buf[6], buf[9] = 64, 64, 4
        await self._dci_write_data_async(buf, _core._DCI_DSS_CONFIG)
        buf = bytearray(8)
        await self._dci_read_data_async(buf, _core._DCI_ZONE_CONFIG)
        if resolution == _core.RESOLUTION_8X8:
            buf[0], buf[1], buf[4], buf[5] = 8, 8, 4, 4
        else:
            buf[0], buf[1], buf[4], buf[5] = 4, 4, 8, 8
        await self._dci_write_data_async(buf, _core._DCI_ZONE_CONFIG)
        await self._send_offset_data_async(self._offset_data, resolution)
        await self._send_xtalk_data_async(resolution)

    async def set_ranging_freq_async(self, frequency):
        if not isinstance(frequency, int) or not 1 <= frequency <= 15:
            raise ValueError("ranging frequency must be 1..15 Hz")
        buf = bytearray(4)
        await self._dci_read_data_async(buf, _core._DCI_FREQ_HZ)
        buf[1] = frequency
        await self._dci_write_data_async(buf, _core._DCI_FREQ_HZ)

    async def start_ranging_async(self, enables):
        if not self._async_initialized:
            raise RuntimeError("call initialize_async() before start_ranging_async()")
        resolution_data = bytearray(8)
        await self._dci_read_data_async(resolution_data, _core._DCI_ZONE_CONFIG)
        resolution = resolution_data[0] * resolution_data[1]
        self._data_read_size, self._streamcount = 0, 255
        output_bh_enable = [7, 0, 0, 0xc0000000]
        output = [_core._START_BH, _core._METADATA_BH, _core._COMMONDATA_BH,
                  _core._AMBIENT_RATE_BH, _core._SPAD_COUNT_BH,
                  _core._NB_TARGET_DETECTED_BH, _core._SIGNAL_RATE_BH,
                  _core._RANGE_SIGMA_MM_BH, _core._DISTANCE_BH,
                  _core._REFLECTANCE_BH, _core._TARGET_STATUS_BH,
                  _core._MOTION_DETECT_BH]
        self._data_read_size = (0 + 4) + (4 + 0x0c) + (4 + 4)
        for enable in enables:
            btype, size, index = self._header(output[enable + 3])
            if 0 < btype < 0x0d:
                size = resolution if 0x54d0 <= index < 0x5890 else resolution * self._ntpz
                self._data_read_size += size * btype + 4
                output[enable + 3] = (index << 16) | (size << 4) | btype
            else:
                self._data_read_size += size + 4
            output_bh_enable[0] |= 1 << (enable + 3)
        self._data_read_size += 20
        await self._dci_write_data_async(struct.pack("<12I", *output), _core._DCI_OUTPUT_LIST)
        await self._dci_write_data_async(struct.pack("<II", self._data_read_size, len(output) + 1), _core._DCI_OUTPUT_CONFIG)
        await self._dci_write_data_async(struct.pack("<IIII", *output_bh_enable), _core._DCI_OUTPUT_ENABLES)
        self._wr_byte(0x7fff, 0)
        self._wr_byte(0x09, 0x05)
        self._wr_byte(0x7fff, 2)
        self._wr_multi(_core._UI_CMD_END - 3, b'\x00\x03\x00\x00')
        await self._poll_for_answer_async(4, 1, _core._UI_CMD_STATUS, 0xff, 3)
        self._async_ranging_started = True
        return True

    async def stop_ranging_async(self, timeout_ms=1000):
        if not self._async_ranging_started:
            return
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        auto_stop_flag = struct.unpack("<I", self._rd_multi(0x2ffc, 4))[0]
        if auto_stop_flag != 0x4ff:
            self._wr_byte(0x7fff, 0)
            self._wr_byte(0x15, 0x16)
            self._wr_byte(0x14, 1)
            started = time.ticks_ms()
            while not (self._rd_byte(0x06) & 0x80):
                if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                    raise ValueError("failed to stop MCU")
                await asyncio.sleep_ms(10)
        self._wr_byte(0x7fff, 0)
        self._wr_byte(0x14, 0)
        self._wr_byte(0x15, 0)
        self._wr_byte(0x09, 0x04)
        self._wr_byte(0x7fff, 2)
        self._async_ranging_started = False

    async def is_alive_async(self):
        return self.is_alive()

    async def check_data_ready_async(self):
        return self.check_data_ready()

    async def wait_data_ready_async(self, timeout_ms=1000, poll_ms=10):
        started = time.ticks_ms()
        while not await self.check_data_ready_async():
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise OSError("VL53L5CX ranging-data timeout")
            await asyncio.sleep_ms(poll_ms)
        return True

    async def get_ranging_data_when_ready_async(self):
        """Read one frame after check_data_ready_async() returned True."""
        return self.get_ranging_data()
    async def get_ranging_data_async(self, timeout_ms=1000, poll_ms=10,
                                     ready_confirmed=False):
        """Read a frame, optionally consuming one confirmed by the caller."""
        if not ready_confirmed:
            await self.wait_data_ready_async(timeout_ms, poll_ms)
        return self.get_ranging_data()

    async def deinit_async(self):
        await self.stop_ranging_async()

    async def aclose(self):
        await self.deinit_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================