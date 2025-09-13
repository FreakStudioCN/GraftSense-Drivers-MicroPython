# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午5:16
# @Author  : 缪贵成
# @File    : ttl_rs485.py
# @Description : ttl转rs485测试程序
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
# MicroPython 内置 UART
from machine import UART

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class TTL_RS485:
    """
    该类用于驱动隔离型 TTL 转 RS485 模块，提供发送、接收、半双工操作及 Modbus CRC16 计算。

    Attributes:
        uart (UART): 已配置的 UART 实例，用于 TTL/RS485 通信。
        baud (int): UART 波特率，用于估算发送耗时。
        turnaround_ms (int): 写后额外等待时间（ms），用于半双工模式。
        debug (bool): 是否打印调试信息。

    Methods:
        send(data: bytes) -> int: 直接发送字节到 UART。
        read(nbytes: int=0, timeout_ms: int=1000) -> bytes: 阻塞读取字节。
        write_then_read(tx: bytes, rx_expected: int=0, timeout_ms: int=1000) -> bytes: 半双工写后读操作。
        flush_input() -> None: 清空 UART 输入缓冲区。
        set_turnaround(ms: int) -> None: 设置写后等待时间。
        crc16_modbus(data: bytes) -> int: 计算 Modbus/RTU CRC16。
        close(deinit_uart: bool=False) -> None: 可选清理 UART。

    Notes:
        该类适合半双工 RS485 通信。
        调用 UART 相关方法（如 read/write）非 ISR-safe。
        MicroPython 不保证所有板子都有 uart.deinit()。

    ==========================================

    TTL_RS485 driver for isolated TTL to RS485 modules.

    Attributes:
        uart (UART): Pre-configured UART object for TTL/RS485 communication.
        baud (int): UART baud rate for estimating transmission time.
        turnaround_ms (int): Extra wait time after writing in ms.
        debug (bool): enable debug prints.

    Methods:
        send(data: bytes) -> int: Send bytes directly to UART.
        read(nbytes: int=0, timeout_ms: int=1000) -> bytes: Blocking read.
        write_then_read(tx: bytes, rx_expected: int=0, timeout_ms: int=1000) -> bytes: Half-duplex write then read.
        flush_input() -> None: Flush UART input buffer.
        set_turnaround(ms: int) -> None: Set extra turnaround time.
        crc16_modbus(data: bytes) -> int: Calculate Modbus RTU CRC16.
        close(deinit_uart: bool=False) -> None: Optional UART cleanup.

    Notes:
        Half-duplex RS485 suitable.
        UART operations are not ISR-safe.
        uart.deinit() may not exist on all MicroPython ports.
    """
    def __init__(self, uart: UART, baud: int = None, turnaround_ms: int = None, debug: bool = False) -> None:
        """
        构造函数，初始化 TTL_RS485 实例。

        Args:
            uart (UART): 已配置的 UART 对象。
            baud (int, optional): 波特率，用于估算发送时间。默认尝试从 uart 读取属性，否则 115200。
            turnaround_ms (int, optional): 写后额外等待时间（ms），默认基于 baud 估算。
            debug (bool, optional): 是否启用调试输出。

        Notes:
            该方法会读取 uart 属性，不是 ISR-safe。

        ==========================================

        Initialize TTL_RS485 driver instance.

        Args:
            uart (UART): Pre-configured UART object.
            baud (int, optional): Baud rate for estimating transmission time. Defaults from uart or 115200.
            turnaround_ms (int, optional): Extra wait after write in ms. Default calculated from baud.
            debug (bool, optional): Enable debug prints.

        Notes:
            The method reads the uart attributes,Not ISR-safe.
        """
        self.uart = uart
        self.debug = debug

        self.baud = baud if baud is not None else getattr(uart, 'baudrate', 115200)
        if turnaround_ms is None:
            self.turnaround_ms = int((10 * 10 * 1000) / self.baud) + 2
        else:
            self.turnaround_ms = turnaround_ms

        if self.debug:
            print("[DEBUG] TTL_RS485 initialized with baud=%d, turnaround_ms=%d" % (self.baud, self.turnaround_ms))

    def send(self, data: bytes) -> int:
        """
        发送字节到 UART，不做读等待。

        Args:
            data (bytes): 要发送的字节。

        Returns:
            int: 实际写入的字节数。

        Notes:
            非 ISR-safe。

        ==========================================

        Send bytes directly to UART.

        Args:
            data (bytes): Bytes to send.

        Returns:
            int: Number of bytes written.

        Notes:
            Not ISR-safe.
        """
        n = self.uart.write(data)
        if self.debug:
            print("[DEBUG] Sent %d bytes: %s" % (n, data.hex()))
        return n

    def read(self, nbytes: int = 0, timeout_ms: int = 1000) -> bytes:
        """
        阻塞读取 UART 字节。

        Args:
            nbytes (int, optional): 要读取的字节数，0 表示尽量读取所有可用字节。
            timeout_ms (int, optional): 超时时间，单位 ms。

        Returns:
            bytes: 读取到的字节，可能为空。

        Notes:
            非 ISR-safe。

        ==========================================

        Blocking read from UART.

        Args:
            nbytes (int, optional): Number of bytes to read. 0 = read all available.
            timeout_ms (int, optional): Timeout in milliseconds.

        Returns:
            bytes: Data read, may be empty.

        Notes:
            Not ISR-safe.
        """
        start = time.ticks_ms()
        buffer = bytearray()
        while True:
            avail = self.uart.any() if hasattr(self.uart, 'any') else 1
            if avail > 0:
                to_read = nbytes - len(buffer) if nbytes > 0 else avail
                chunk = self.uart.read(to_read)
                if chunk:
                    buffer.extend(chunk)
            if nbytes > 0 and len(buffer) >= nbytes:
                break
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                break
            time.sleep_ms(1)
        if self.debug:
            print("[DEBUG] Read %d bytes: %s" % (len(buffer), buffer.hex()))
        return bytes(buffer)

    def write_then_read(self, tx: bytes, rx_expected: int = 0, timeout_ms: int = 1000) -> bytes:
        """
        半双工操作：先发送再读取。

        Args:
            tx (bytes): 要发送的数据。
            rx_expected (int, optional): 期望读取的字节数，0 表示尽量读取所有可用字节。
            timeout_ms (int, optional): 读取超时时间，单位 ms。

        Returns:
            bytes: 读取到的字节。

        Notes:
            非 ISR-safe。

        ==========================================

        Half-duplex write then read operation.

        Args:
            tx (bytes): Bytes to send.
            rx_expected (int, optional): Expected bytes to read. 0 = read all available.
            timeout_ms (int, optional): Timeout in milliseconds.

        Returns:
            bytes: Data read.

        Notes:
            Not ISR-safe.
        """
        self.send(tx)
        send_time_ms = int((len(tx) * 10 * 1000) / self.baud)
        time.sleep_ms(send_time_ms + self.turnaround_ms)
        return self.read(rx_expected, timeout_ms)

    def flush_input(self) -> None:
        """
        清空 UART 输入缓冲区。

        Notes:
            非 ISR-safe。

        ==========================================

        Flush UART input buffer.

        Notes:
            Not ISR-safe.
        """
        if hasattr(self.uart, 'read'):
            while self.uart.any() if hasattr(self.uart, 'any') else False:
                self.uart.read(1)
        if self.debug:
            print("[DEBUG] Input buffer flushed")

    def set_turnaround(self, ms: int) -> None:
        """
        设置写后额外等待时间（ms）。

        Args:
            ms (int): 等待时间，单位 ms。

        Notes:
            非 ISR-safe。

        ==========================================

        Set extra turnaround time after write.

        Args:
            ms (int): Turnaround time in ms.

        Notes:
            Not ISR-safe.
        """
        self.turnaround_ms = ms
        if self.debug:
            print("[DEBUG] Turnaround time set to %d ms" % ms)

    @staticmethod
    def crc16_modbus(data: bytes) -> int:
        """
        计算 Modbus/RTU CRC16。

        Args:
            data (bytes): 要计算 CRC 的字节。

        Returns:
            int: CRC16 值。

        ==========================================

        Calculate Modbus RTU CRC16.

        Args:
            data (bytes): Bytes to calculate CRC.

        Returns:
            int: CRC16 value.
        """
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def close(self, deinit_uart: bool = False) -> None:
        """
        可选关闭/清理 UART。

        Args:
            deinit_uart (bool, optional): 是否调用 uart.deinit()。

        Notes:
            非 ISR-safe。
            uart.deinit() 可能不在所有 MicroPython 板子上可用。

        ==========================================

        Optional cleanup of UART.

        Args:
            deinit_uart (bool, optional): Call uart.deinit() if True.

        Notes:
            Not ISR-safe.
            uart.deinit() may not exist on all MicroPython ports.
        """
        if deinit_uart and hasattr(self.uart, 'deinit'):
            self.uart.deinit()
        if self.debug:
            print("[DEBUG] TTL_RS485 closed")

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
