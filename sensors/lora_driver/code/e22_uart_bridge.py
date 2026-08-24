# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : e22_uart_bridge.py
# @Description : RP2040-Zero UART-to-E22 command bridge
# @License : MIT

"""Synchronous UART bridge that owns neither the injected UART nor radio."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
import time

from e22_uart_protocol import (
    MAX_LINE_LENGTH,
    PROTOCOL_VERSION,
    bytes_to_hex,
    decode_frame,
    encode_frame,
    hex_to_bytes,
)


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class E22UARTBridge:
    """
    UART 到 E22-900M22S 的同步命令桥。
    Attributes:
        无公开可写属性。
    Methods:
        poll(): 最多处理一个完整请求。
        serve_forever(): 持续轮询 UART。
        stop(): 请求停止轮询。
        deinit(): 停止轮询并清空协议缓冲。
    Notes:
        - UART 和 radio 均由外部注入，bridge 不拥有资源。
        - 不在 IRQ 中执行 SPI/UART 操作；非 ISR-safe。
    ==========================================
    Synchronous UART-to-E22-900M22S command bridge.
    Attributes:
        No public writable attributes.
    Methods:
        poll(): Process at most one complete request.
        serve_forever(): Continuously poll UART.
        stop(): Request polling to stop.
        deinit(): Stop polling and clear protocol buffers.
    Notes:
        - UART and radio are injected; the bridge owns neither resource.
        - SPI/UART work is not performed in IRQ context; not ISR-safe.
    """

    __slots__ = ("_uart", "_radio", "_rx_buffer", "_running")

    def __init__(self, uart: object, radio: object) -> None:
        """
        执行 `__init__` 操作。
        Args:
            uart (object): 方法参数。
            radio (object): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            TypeError: 参数、状态或通信异常。
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Execute the `__init__` operation.
        Args:
            uart (object): Method parameter.
            radio (object): Method parameter.
        Returns:
            None: No return value.
        Raises:
            TypeError: Parameter, state, or communication error.
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if uart is None or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise TypeError("uart must provide read() and write()")
        if radio is None:
            raise ValueError("radio must not be None")
        self._uart = uart
        self._radio = radio
        self._rx_buffer = bytearray()
        self._running = False

    def poll(self) -> bool:
        """
        执行 `poll` 操作。
        Args:
            无。
        Returns:
            bool: 方法返回值。
        Raises:
            RuntimeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Process at most one complete request and return whether work was done.
        Args:
            None.
        Returns:
            bool: Method return value.
        Raises:
            RuntimeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        available = self._uart.any() if hasattr(self._uart, "any") else 1
        if available:
            try:
                chunk = self._uart.read(available)
            except OSError as error:
                raise RuntimeError("UART read failed: %s" % str(error)) from error
            if chunk:
                self._rx_buffer.extend(chunk)
        if len(self._rx_buffer) > MAX_LINE_LENGTH:
            self._rx_buffer = bytearray()
            self._write_error(0, "FRAME_TOO_LONG", "request exceeds maximum length")
            return True
        newline = self._rx_buffer.find(b"\n")
        if newline < 0:
            return False
        frame = bytes(self._rx_buffer[:newline])
        self._rx_buffer = bytearray(self._rx_buffer[newline + 1 :])
        self._handle_frame(frame)
        return True

    def serve_forever(self, poll_ms: int = 2) -> None:
        """
        执行 `serve_forever` 操作。
        Args:
            poll_ms (int): 方法参数。
        Returns:
            None: 无返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Run the bridge loop until stop() is called.
        Args:
            poll_ms (int): Method parameter.
        Returns:
            None: No return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(poll_ms, int) or poll_ms <= 0:
            raise ValueError("poll_ms must be a positive int")
        self._running = True
        while self._running:
            if not self.poll():
                time.sleep_ms(poll_ms)

    def stop(self) -> None:
        """
        执行 `stop` 操作。
        Args:
            无。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Request loop termination.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._running = False

    def deinit(self) -> None:
        """
        执行 `deinit` 操作。
        Args:
            无。
        Returns:
            None: 无返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Stop polling and clear buffered data without releasing injected resources.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._running = False
        self._rx_buffer = bytearray()

    def _handle_frame(self, frame: bytes) -> None:
        request_id = 0
        try:
            request = decode_frame(frame)
            request_id = request.get("id", 0)
            if request.get("v") != PROTOCOL_VERSION:
                raise ValueError("unsupported protocol version")
            if not isinstance(request_id, int) or request_id < 0:
                raise ValueError("id must be a non-negative int")
            command = request.get("cmd")
            if not isinstance(command, str):
                raise ValueError("cmd must be str")
            result = self._dispatch(command, request)
            self._uart.write(
                encode_frame(
                    {
                        "v": PROTOCOL_VERSION,
                        "id": request_id,
                        "ok": True,
                        "result": result,
                    }
                )
            )
        except Exception as error:
            self._write_error(request_id, type(error).__name__, str(error))

    def _dispatch(self, command: str, request: dict):
        if not isinstance(command, str) or not command:
            raise ValueError("command must be a non-empty str")
        if not isinstance(request, dict):
            raise TypeError("request must be dict")
        if command == "ping":
            return {"bridge": "e22_900m22s", "protocol": PROTOCOL_VERSION}
        if command == "status":
            return {
                "initialized": self._radio.initialized,
                "state": self._radio.state,
            }
        if command == "initialize":
            self._radio.initialize(
                frequency_mhz=request["frequency_mhz"],
                bandwidth_khz=request.get("bandwidth_khz", 125.0),
                spreading_factor=request.get("spreading_factor", 9),
                coding_rate=request.get("coding_rate", 7),
                output_power_dbm=request.get("output_power_dbm", 14),
                preamble_length=request.get("preamble_length", 8),
            )
            return {"initialized": True}
        if command == "send":
            payload = hex_to_bytes(request["data"])
            sent = self._radio.send(payload, request.get("timeout_ms", 3000))
            return {"sent": sent}
        if command == "receive":
            payload, rssi_dbm, snr_db = self._radio.receive(
                request.get("max_length", 255),
                request.get("timeout_ms", 3000),
            )
            return {
                "data": bytes_to_hex(payload),
                "rssi_dbm": rssi_dbm,
                "snr_db": snr_db,
            }
        raise ValueError("unknown command: %s" % command)

    def _write_error(self, request_id: int, code: str, message: str) -> None:
        if code is None:
            raise ValueError("code must not be None")
        if not isinstance(request_id, int) or request_id < 0:
            request_id = 0
        if not isinstance(code, str) or not code:
            code = "ERROR"
        if not isinstance(message, str):
            message = str(message)
        try:
            self._uart.write(
                encode_frame(
                    {
                        "v": PROTOCOL_VERSION,
                        "id": request_id,
                        "ok": False,
                        "error": {"code": code, "message": message},
                    }
                )
            )
        except OSError as error:
            raise RuntimeError("UART write failed: %s" % str(error)) from error


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
