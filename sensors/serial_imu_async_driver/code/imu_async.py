# Python env: MicroPython with uasyncio
# -*- coding: utf-8 -*-
# Async JY60/JY61 UART IMU driver.  Protocol values match imu.py.

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# ======================================== 全局变量 ============================================
_FRAME_LENGTH = 11
_FRAME_HEADER = 0x55
_ACC_FRAME = 0x51
_GYRO_FRAME = 0x52
_ANGLE_FRAME = 0x53

# ======================================== 功能函数 ============================================
def _signed16(low: int, high: int) -> int:
    value = (high << 8) | low
    if value >= 32768:
        value -= 65536
    return value

# ======================================== 自定义类 ============================================
class IMUAsync:
    """Cooperative JY60/JY61 reader; one task exclusively owns UART reads."""

    K_ACC = 16
    K_TEMP = 96.38
    C_TEMP = 36.53
    K_GYRO = 2000
    K_ANGLE = 180
    ZAXISCLEARCMD = (0xFF, 0xAA, 0x52)
    ACCCALBCMD = (0xFF, 0xAA, 0x67)
    CONVSLEEPCMD = (0xFF, 0xAA, 0x60)
    UARTMODECMD = (0xFF, 0xAA, 0x61)
    IICMODECMD = (0xFF, 0xAA, 0x62)
    HORIZINSTCMD = (0xFF, 0xAA, 0x65)
    VERTINSTCMD = (0xFF, 0xAA, 0x66)
    BAUD115200CMD = (0xFF, 0xAA, 0x63)
    BAUD9600CMD = (0xFF, 0xAA, 0x64)
    WORK_MODE, SLEEP_MODE = (1, 0)
    UART_MODE, IIC_MODE = (1, 0)
    HORIZ_INST, VERT_INST = (1, 0)

    def __init__(self, uart, poll_ms: int = 5) -> None:
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any(), read(), and write()")
        if not isinstance(poll_ms, int) or poll_ms < 1:
            raise ValueError("poll_ms must be an integer >= 1")
        self._uart = uart
        self._poll_ms = poll_ms
        self._command_lock = asyncio.Lock()
        self._reader_task = None
        self._running = False
        self._frame = bytearray(_FRAME_LENGTH)
        self._frame_count = 0
        self._sample_version = 0
        self._acc_ready = False
        self._gyro_ready = False
        self._angle_ready = False
        self.acc_x = self.acc_y = self.acc_z = 0.0
        self.temp = 0.0
        self.gyro_x = self.gyro_y = self.gyro_z = 0.0
        self.angle_x = self.angle_y = self.angle_z = 0.0
        self.workmode = self.WORK_MODE
        self.transmode = self.UART_MODE
        self.instmode = self.HORIZ_INST

    async def start(self, calibrate: bool = True) -> None:
        if self._running:
            return
        self._running = True
        self._reader_task = asyncio.create_task(self._reader_loop())
        if calibrate:
            await self.SendCMD_async(self.ZAXISCLEARCMD)
            await asyncio.sleep_ms(500)
            await self.SendCMD_async(self.ACCCALBCMD)
            await asyncio.sleep_ms(500)

    async def stop(self) -> None:
        self._running = False
        if self._reader_task is not None:
            task = self._reader_task

            task.cancel()

            try:

                await task

            except BaseException:

                pass

            self._reader_task = None
        await asyncio.sleep_ms(0)

    async def aclose(self) -> None:
        await self.stop()

    async def SendCMD_async(self, cmd: tuple) -> bool:
        valid = (self.ZAXISCLEARCMD, self.ACCCALBCMD, self.CONVSLEEPCMD,
                 self.UARTMODECMD, self.IICMODECMD, self.HORIZINSTCMD,
                 self.VERTINSTCMD, self.BAUD115200CMD, self.BAUD9600CMD)
        if tuple(cmd) not in valid:
            return False
        command = tuple(cmd)
        async with self._command_lock:
            try:
                self._uart.write(bytes(command))
            except OSError as exc:
                raise RuntimeError("JY60 UART command write failed") from exc
            if command == self.CONVSLEEPCMD:
                self.workmode = self.SLEEP_MODE if self.workmode == self.WORK_MODE else self.WORK_MODE
            elif command == self.UARTMODECMD:
                self.transmode = self.UART_MODE
            elif command == self.IICMODECMD:
                self.transmode = self.IIC_MODE
            elif command == self.HORIZINSTCMD:
                self.instmode = self.HORIZ_INST
            elif command == self.VERTINSTCMD:
                self.instmode = self.VERT_INST
            elif command == self.BAUD115200CMD:
                self._uart.init(baudrate=115200)
            elif command == self.BAUD9600CMD:
                self._uart.init(baudrate=9600)
        return True

    async def RecvData_async(self, timeout_ms: int = 1000) -> tuple:
        if not isinstance(timeout_ms, int) or timeout_ms < 1:
            raise ValueError("timeout_ms must be an integer >= 1")
        if not self._running:
            raise RuntimeError("call await start() before RecvData_async()")
        version = self._sample_version
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._sample_version != version:
                return self._sample()
            await asyncio.sleep_ms(self._poll_ms)
        raise RuntimeError("JY60 sample timeout after %d ms" % timeout_ms)

    async def _reader_loop(self) -> None:
        while self._running:
            try:
                if self._uart.any():
                    data = self._uart.read()
                    if data:
                        for value in data:
                            self._feed_byte(value)
                    await asyncio.sleep_ms(0)
                else:
                    await asyncio.sleep_ms(self._poll_ms)
            except OSError:
                await asyncio.sleep_ms(self._poll_ms)

    def _feed_byte(self, value: int) -> None:
        if self._frame_count == 0:
            if value == _FRAME_HEADER:
                self._frame[0] = value
                self._frame_count = 1
            return
        self._frame[self._frame_count] = value
        self._frame_count += 1
        if self._frame_count < _FRAME_LENGTH:
            return
        self._frame_count = 0
        checksum = 0
        for index in range(10):
            checksum = (checksum + self._frame[index]) & 0xFF
        if checksum != self._frame[10]:
            return
        kind = self._frame[1]
        if kind == _ACC_FRAME:
            self.acc_x = _signed16(self._frame[2], self._frame[3]) / 32768 * self.K_ACC
            self.acc_y = _signed16(self._frame[4], self._frame[5]) / 32768 * self.K_ACC
            self.acc_z = _signed16(self._frame[6], self._frame[7]) / 32768 * self.K_ACC
            self.temp = _signed16(self._frame[8], self._frame[9]) / 32768 * self.K_TEMP + self.C_TEMP
            self._acc_ready = True
        elif kind == _GYRO_FRAME:
            self.gyro_x = _signed16(self._frame[2], self._frame[3]) / 32768 * self.K_GYRO
            self.gyro_y = _signed16(self._frame[4], self._frame[5]) / 32768 * self.K_GYRO
            self.gyro_z = _signed16(self._frame[6], self._frame[7]) / 32768 * self.K_GYRO
            self._gyro_ready = True
        elif kind == _ANGLE_FRAME:
            self.angle_x = _signed16(self._frame[2], self._frame[3]) / 32768 * self.K_ANGLE
            self.angle_y = _signed16(self._frame[4], self._frame[5]) / 32768 * self.K_ANGLE
            self.angle_z = _signed16(self._frame[6], self._frame[7]) / 32768 * self.K_ANGLE
            self._angle_ready = True
        if self._acc_ready and self._gyro_ready and self._angle_ready:
            self._acc_ready = self._gyro_ready = self._angle_ready = False
            self._sample_version += 1

    def _sample(self) -> tuple:
        return (self.acc_x, self.acc_y, self.acc_z, self.temp, self.gyro_x,
                self.gyro_y, self.gyro_z, self.angle_x, self.angle_y, self.angle_z)

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
