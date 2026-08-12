# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 12:00
# @Author  : rdagger
# @File    : bno085.py
# @Description : BNO085 9-DOF IMU UART-RVC mode driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "rdagger"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import struct
import time

try:
    from micropython import const
except ImportError:

    def const(value: int) -> int:
        return value


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def _ticks_ms() -> int:
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_diff(now: int, start: int) -> int:
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(now, start)
    return now - start


# ======================================== 自定义类 ============================================


class BNO085TimeoutError(Exception):
    """
    Raised if a UART-RVC message cannot be read before the given timeout.
    """


class BNO085:
    """
    BNO085 9-DOF IMU sensor driver using UART-RVC mode.

    This driver is based on the original UART-RVC implementation by Bryan
    Siepert for Adafruit Industries and the MicroPython port by rdagger.
    It keeps the public API of the normalized driver: BNO085.heading returns
    (yaw, pitch, roll, x_accel, y_accel, z_accel).
    """

    FRAME_HEADER = const(0xAA)
    FRAME_PAYLOAD_LEN = const(17)
    FRAME_TOTAL_LEN = const(19)
    CHECKSUM_COVER = const(16)
    ANGLE_SCALE = 0.01
    ACCEL_SCALE = 0.0098067

    __slots__ = ("_uart", "_timeout", "_debug")

    def __init__(self, uart: object, timeout: float = 1.0, debug: bool = False) -> None:
        """
        Initialize the BNO085 UART-RVC driver.
        """
        if not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide read and write methods")
        if not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be int or float")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._uart = uart
        self._timeout = float(timeout)
        self._debug = debug

    def set_timeout(self, timeout: float) -> None:
        """
        Set the UART read timeout in seconds.
        """
        if not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be int or float")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self._timeout = float(timeout)

    def get_timeout(self) -> float:
        """
        Return the UART read timeout in seconds.
        """
        return self._timeout

    @property
    def heading(self) -> tuple:
        """
        Read and return (yaw, pitch, roll, x_accel, y_accel, z_accel).
        """
        start = _ticks_ms()
        timeout_ms = int(self._timeout * 1000)

        while _ticks_diff(_ticks_ms(), start) < timeout_ms:
            try:
                header = self._read_exact(2, start, timeout_ms)
            except BNO085TimeoutError:
                break
            except OSError as error:
                raise RuntimeError("UART read failed during frame header: %s" % error)

            if header != bytes((self.FRAME_HEADER, self.FRAME_HEADER)):
                continue

            try:
                payload = self._read_exact(self.FRAME_PAYLOAD_LEN, start, timeout_ms)
            except BNO085TimeoutError:
                break
            except OSError as error:
                raise RuntimeError("UART read failed during frame payload: %s" % error)

            result = self._parse_frame(payload)
            if result is not None:
                return result

        raise BNO085TimeoutError("Unable to read RVC heading message within timeout")

    @staticmethod
    def _parse_frame(frame: bytes) -> tuple:
        """
        Parse a 17-byte UART-RVC payload.
        """
        if not isinstance(frame, (bytes, bytearray)):
            raise ValueError("frame must be bytes or bytearray")
        if len(frame) != BNO085.FRAME_PAYLOAD_LEN:
            raise ValueError("frame length must be 17 bytes")

        checksum_calc = sum(frame[0 : BNO085.CHECKSUM_COVER]) & 0xFF
        checksum_read = frame[BNO085.CHECKSUM_COVER]
        if checksum_calc != checksum_read:
            return None

        _, yaw, pitch, roll, x_accel, y_accel, z_accel, _, _, _, _ = struct.unpack_from("<BhhhhhhBBBB", frame)
        return (
            yaw * BNO085.ANGLE_SCALE,
            pitch * BNO085.ANGLE_SCALE,
            roll * BNO085.ANGLE_SCALE,
            x_accel * BNO085.ACCEL_SCALE,
            y_accel * BNO085.ACCEL_SCALE,
            z_accel * BNO085.ACCEL_SCALE,
        )

    def _read_exact(self, size: int, start: int, timeout_ms: int) -> bytes:
        """
        Read exactly size bytes unless the shared frame timeout expires.
        """
        if not isinstance(size, int):
            raise ValueError("size must be int")
        if size <= 0:
            raise ValueError("size must be greater than zero")

        data = bytearray()
        while len(data) < size:
            if _ticks_diff(_ticks_ms(), start) >= timeout_ms:
                raise BNO085TimeoutError("UART read timed out")

            chunk = self._uart.read(size - len(data))
            if chunk is None:
                time.sleep_ms(1)
                continue
            if len(chunk) == 0:
                time.sleep_ms(1)
                continue
            data.extend(chunk)

        return bytes(data)

    def deinit(self) -> None:
        """
        Release references owned by this driver.
        """
        self._uart = None
        self._debug = False


# ======================================== 初始化配置 ==========================================

# ========================================  主程序 ============================================
