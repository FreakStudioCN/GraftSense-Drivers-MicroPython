# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : e22_uart_client.py
# @Description : External RP2040 Pico UART client API
# @License : MIT

"""High-level Pico API for an RP2040-Zero E22 UART bridge."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
try:
    from time import sleep_ms, ticks_diff, ticks_ms
except ImportError:
    import time

    def sleep_ms(value: int) -> None:
        """Sleep for the requested number of milliseconds."""
        if not isinstance(value, int) or value < 0:
            raise ValueError("value must be a non-negative int")
        time.sleep(value / 1000.0)

    def ticks_ms() -> int:
        """Return a monotonic millisecond counter."""
        return int(time.monotonic() * 1000)

    def ticks_diff(end: int, start: int) -> int:
        """Return the signed difference between two fallback tick values."""
        if not isinstance(end, int) or not isinstance(start, int):
            raise TypeError("end and start must be int")
        return end - start


from e22_uart_protocol import (
    PROTOCOL_VERSION,
    bytes_to_hex,
    decode_frame,
    encode_frame,
    hex_to_bytes,
)


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class E22UARTError(RuntimeError):
    """
    E22UARTError 类。
    Attributes:
        继承 RuntimeError 属性。
    Methods:
        继承 RuntimeError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    Base UART client error.
    Attributes:
        Inherits RuntimeError attributes.
    Methods:
        Inherits RuntimeError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class E22UARTTimeoutError(E22UARTError):
    """
    E22UARTTimeoutError 类。
    Attributes:
        继承 E22UARTError 属性。
    Methods:
        继承 E22UARTError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    UART response timeout.
    Attributes:
        Inherits E22UARTError attributes.
    Methods:
        Inherits E22UARTError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


class E22UARTClient:
    """
    基于外部 UART 对象的阻塞式 E22 客户端。
    Attributes:
        无公开可写属性。
    Methods:
        ping(): 检查 bridge 连接。
        status(): 读取远端状态。
        initialize(): 初始化远端 E22。
        send(): 发送一个无线数据包。
        receive(): 接收一个无线数据包。
        deinit(): 清空协议接收缓冲。
    Notes:
        - UART 由调用方创建和管理。
        - 所有请求都使用有界超时；非 ISR-safe。
    ==========================================
    Blocking E22 client for an injected UART object.
    Attributes:
        No public writable attributes.
    Methods:
        ping(): Check bridge connectivity.
        status(): Read remote state.
        initialize(): Initialize the remote E22.
        send(): Transmit one radio packet.
        receive(): Receive one radio packet.
        deinit(): Clear the protocol receive buffer.
    Notes:
        - The caller creates and owns the UART object.
        - Every request has a bounded timeout; not ISR-safe.
    """

    __slots__ = ("_uart", "_timeout_ms", "_next_id", "_rx_buffer")

    def __init__(self, uart: object, timeout_ms: int = 5000) -> None:
        """
        执行 `__init__` 操作。
        Args:
            uart (object): 方法参数。
            timeout_ms (int): 方法参数。
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
            timeout_ms (int): Method parameter.
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
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        self._uart = uart
        self._timeout_ms = timeout_ms
        self._next_id = 1
        self._rx_buffer = bytearray()

    def ping(self) -> dict:
        """
        执行 `ping` 操作。
        Args:
            无。
        Returns:
            dict: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Verify the Pico-to-Zero UART bridge.
        Args:
            None.
        Returns:
            dict: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._request("ping")

    def status(self) -> dict:
        """
        执行 `status` 操作。
        Args:
            无。
        Returns:
            dict: 方法返回值。
        Raises:
            无。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Return bridge initialization and radio state.
        Args:
            None.
        Returns:
            dict: Method return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        return self._request("status")

    def initialize(
        self,
        frequency_mhz: float,
        bandwidth_khz: float = 125.0,
        spreading_factor: int = 9,
        coding_rate: int = 7,
        output_power_dbm: int = 14,
        preamble_length: int = 8,
    ) -> dict:
        """
        执行 `initialize` 操作。
        Args:
            frequency_mhz (float): 方法参数。
            bandwidth_khz (float): 方法参数。
            spreading_factor (int): 方法参数。
            coding_rate (int): 方法参数。
            output_power_dbm (int): 方法参数。
            preamble_length (int): 方法参数。
        Returns:
            dict: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
            TypeError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Initialize the remote E22 radio.
        Args:
            frequency_mhz (float): Method parameter.
            bandwidth_khz (float): Method parameter.
            spreading_factor (int): Method parameter.
            coding_rate (int): Method parameter.
            output_power_dbm (int): Method parameter.
            preamble_length (int): Method parameter.
        Returns:
            dict: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
            TypeError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if frequency_mhz is None:
            raise ValueError("frequency_mhz must not be None")
        if not isinstance(frequency_mhz, (int, float)):
            raise TypeError("frequency_mhz must be int or float")
        if not isinstance(bandwidth_khz, (int, float)):
            raise TypeError("bandwidth_khz must be int or float")
        if not isinstance(spreading_factor, int):
            raise TypeError("spreading_factor must be int")
        if not isinstance(coding_rate, int):
            raise TypeError("coding_rate must be int")
        if not isinstance(output_power_dbm, int):
            raise TypeError("output_power_dbm must be int")
        if not isinstance(preamble_length, int):
            raise TypeError("preamble_length must be int")
        return self._request(
            "initialize",
            {
                "frequency_mhz": frequency_mhz,
                "bandwidth_khz": bandwidth_khz,
                "spreading_factor": spreading_factor,
                "coding_rate": coding_rate,
                "output_power_dbm": output_power_dbm,
                "preamble_length": preamble_length,
            },
        )

    def send(self, data: bytes, timeout_ms: int = 3000) -> int:
        """
        执行 `send` 操作。
        Args:
            data (bytes): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            int: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Send one radio packet and return the accepted byte count.
        Args:
            data (bytes): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            int: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(data, (bytes, bytearray)) or not data:
            raise ValueError("data must be non-empty bytes-like")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        result = self._request(
            "send",
            {
                "data": bytes_to_hex(data),
                "timeout_ms": timeout_ms,
            },
            timeout_ms + self._timeout_ms,
        )
        return result["sent"]

    def receive(self, max_length: int = 255, timeout_ms: int = 3000) -> tuple:
        """
        执行 `receive` 操作。
        Args:
            max_length (int): 方法参数。
            timeout_ms (int): 方法参数。
        Returns:
            tuple: 方法返回值。
        Raises:
            ValueError: 参数、状态或通信异常。
        Notes:
            - 可能访问或修改驱动状态；ISR-safe: 否。
        ==========================================
        Receive one packet as (payload, rssi_dbm, snr_db).
        Args:
            max_length (int): Method parameter.
            timeout_ms (int): Method parameter.
        Returns:
            tuple: Method return value.
        Raises:
            ValueError: Parameter, state, or communication error.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        if not isinstance(max_length, int) or not 1 <= max_length <= 255:
            raise ValueError("max_length must be an int between 1 and 255")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        result = self._request(
            "receive",
            {
                "max_length": max_length,
                "timeout_ms": timeout_ms,
            },
            timeout_ms + self._timeout_ms,
        )
        return hex_to_bytes(result["data"]), result["rssi_dbm"], result["snr_db"]

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
        Clear buffered protocol data without releasing the injected UART.
        Args:
            None.
        Returns:
            None: No return value.
        Raises:
            None.
        Notes:
            - May access or modify driver state; ISR-safe: No.
        """
        self._rx_buffer = bytearray()

    def _request(self, command: str, parameters: dict = None, timeout_ms: int = None):
        request_id = self._next_id
        self._next_id = 1 if request_id >= 0x7FFFFFFF else request_id + 1
        request = {"v": PROTOCOL_VERSION, "id": request_id, "cmd": command}
        if parameters:
            request.update(parameters)
        try:
            self._uart.write(encode_frame(request))
        except OSError as error:
            raise E22UARTError("UART write failed: %s" % str(error)) from error
        response = self._read_response(timeout_ms or self._timeout_ms, request_id)
        if response.get("id") != request_id:
            raise E22UARTError("response id mismatch")
        if response.get("v") != PROTOCOL_VERSION:
            raise E22UARTError("response protocol mismatch")
        if not response.get("ok"):
            error = response.get("error", {})
            raise E22UARTError("%s: %s" % (error.get("code", "ERROR"), error.get("message", "")))
        return response.get("result")

    def _read_response(self, timeout_ms: int, expected_id: int = None) -> dict:
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        if expected_id is not None and not isinstance(expected_id, int):
            raise TypeError("expected_id must be int or None")
        started = ticks_ms()
        while ticks_diff(ticks_ms(), started) < timeout_ms:
            available = self._uart.any() if hasattr(self._uart, "any") else 1
            if available:
                try:
                    chunk = self._uart.read(available)
                except OSError as error:
                    raise E22UARTError("UART read failed: %s" % str(error)) from error
                if chunk:
                    self._rx_buffer.extend(chunk)
                    while True:
                        newline = self._rx_buffer.find(b"\n")
                        if newline < 0:
                            break
                        frame = bytes(self._rx_buffer[:newline])
                        self._rx_buffer = bytearray(self._rx_buffer[newline + 1 :])
                        response = decode_frame(frame)
                        if expected_id is None or response.get("id") == expected_id:
                            return response
            sleep_ms(1)
        self._rx_buffer = bytearray()
        raise E22UARTTimeoutError("UART response timeout")


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
