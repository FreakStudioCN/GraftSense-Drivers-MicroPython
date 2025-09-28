# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 下午3:32
# @Author  : 缪贵成
# @File    : uart.py
# @Description : 串口通信，继承pn532
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
import time
from pn532 import PN532

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PN532_UART(PN532):
    """
    该类通过 UART 串口控制 PN532 RFID/NFC 模块，提供设备唤醒、数据收发和状态检测。

    Attributes:
        uart (UART): 已初始化的 machine.UART 实例，用于与 PN532 通信。
        reset (Pin 或 None): 可选复位引脚，None 表示不使用硬件复位。
        debug (bool): 调试输出开关，True 时会打印原始收发数据帧。

    Methods:
        __init__(uart, *, reset=None, debug=False) -> None:
            初始化驱动，绑定 UART 通道，可选指定 reset 引脚和 debug 模式。
        _wakeup() -> None:
            向设备发送唤醒帧，并通过复位引脚恢复低功耗模式。
        _wait_ready(timeout: int = 1000) -> bool:
            轮询 UART 缓冲区，等待设备在指定超时时间内变为就绪。
        _read_data(count: int) -> bytes:
            从 UART 读取指定字节数，若无数据则抛 BusyError。
        _write_data(framebytes: bytes) -> None:
            将数据帧写入 UART，阻塞直至写入完成。

    Notes:
        该类仅支持 UART 通信方式，不支持 I2C 或 SPI。
        驱动不会自动创建或关闭外部传入的 UART 实例，除非显式调用 close(close_uart=True)。
        当 debug=True 时，所有收发数据会以十六进制打印，便于硬件排查。

    ==========================================

    UART driver for PN532 RFID/NFC modules. Provides wakeup, read, write and ready-check helpers.

    Attributes:
        uart (UART): Initialized machine.UART instance for PN532 communication.
        reset (Pin or None): Optional reset pin, None if unused.
        debug (bool): Enable debug logging; prints TX/RX frames in hex when True.

    Methods:
        __init__(uart, *, reset=None, debug=False) -> None:
            Initialize driver with UART, optional reset pin, and debug mode.
        _wakeup() -> None:
            Send wakeup frame and release from low-power mode.
        _wait_ready(timeout: int = 1000) -> bool:
            Poll UART buffer until data is available or timeout.
        _read_data(count: int) -> bytes:
            Read specified number of bytes; raise BusyError if no data.
        _write_data(framebytes: bytes) -> None:
            Write frame bytes to UART, blocking until complete.

    Notes:
        This class only supports UART communication, not I2C or SPI.
        The driver does not create or close the provided UART unless explicitly requested.
        With debug=True, raw TX/RX frames are printed in hex for troubleshooting.
    """

    def __init__(self, uart, *, reset=None, debug=False):
        """
        初始化 PN532_UART 实例。

        Args:
            uart (UART): 已初始化的 UART 对象。
            reset (Pin, optional): 可选的复位引脚。
            debug (bool): 是否启用调试输出。
        raises:
            TypeError: 如果 uart 不是 machine.UART 的实例。
            TypeError: 如果 reset 不是 machine.Pin 的实例或 None。
            TypeError: 如果 debug 不是布尔值。

        ==========================================

        Initialize PN532_UART instance.

        Args:
            uart (UART): Pre-initialized UART object.
            reset (Pin, optional): Optional reset pin.
            debug (bool): Enable debug output.

        raises:
            TypeError: If uart is not an instance of machine.UART.
            TypeError: If reset is not an instance of machine.Pin or None.
            TypeError: If debug is not a boolean value.
        """
        super().__init__(debug=debug, reset=reset)
        if not isinstance(uart, UART):
            raise TypeError("uart must be an instance of machine.UART")

        if reset is not None and not isinstance(reset, Pin):
            raise TypeError("reset must be an instance of machine.Pin or None")

        if not isinstance(debug, bool):
            raise TypeError("debug must be a boolean value")
        self.debug = debug
        self._uart = uart


    def _wakeup(self):
        """
        唤醒 PN532 芯片。

        如果存在复位引脚，先拉高保持 10ms。
        通过 UART 发送唤醒字节序列。
        默认延迟为 10ms，可根据需要调整。

        Notes:
            调用后自动执行 SAM_configuration 配置。

        ==========================================

        Wake up PN532 chip.

        If reset pin exists, drive it HIGH for 10ms.
        Send wake-up byte sequence over UART.
        Default delay is 10ms, adjustable if needed.

        Notes:
            Calls SAM_configuration internally.
        """
        if self._reset_pin:
            self._reset_pin.value(1)
            time.sleep(0.01)
        self.low_power = False
        self._uart.write(
            b"\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        )
        # 使用普通模式，配置内部安全访问模式
        self.SAM_configuration()

    def _wait_ready(self, timeout=1000) -> bool:
        """
        等待 PN532 在指定时间内变为可读状态。

        Args:
            timeout (int): 超时时间，毫秒。

        Returns:
            bool: True 表示有数据可读，False 表示超时。

        ==========================================

        Wait until PN532 is ready within the timeout.

        Args:
            timeout (int): Timeout in milliseconds.

        Returns:
            bool: True if data available, False if timed out.
        """
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
            if self._uart.any() > 0:
                return True
            time.sleep(0.01)
        return False

    def _read_data(self, count) -> bytes:
        """
        从 PN532 读取指定字节数。

        Args:
            count (int): 要读取的字节数。

        Returns:
            bytes: 读取的数据。

        Raises:
            RuntimeError: 如果未读取到数据。

        ==========================================

        Read a specific number of bytes from PN532.

        Args:
            count (int): Number of bytes to read.

        Returns:
            bytes: Data read.

        Raises:
            RuntimeError: If no data available.
        """
        frame = self._uart.read(count)
        if not frame:
            raise RuntimeError("No data read from PN532")
        if self.debug:
            print("Reading: ", [hex(i) for i in frame])
        return frame

    def _write_data(self, framebytes):
        """
        向 PN532 写入字节数据。

        Args:
            framebytes (bytes/bytearray): 要发送的数据帧。

        ==========================================

        Write data bytes to PN532.

        Args:
            framebytes (bytes/bytearray): Data frame to send.

        """
        while self._uart.any():
            self._uart.read()
        self._uart.write(framebytes)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
