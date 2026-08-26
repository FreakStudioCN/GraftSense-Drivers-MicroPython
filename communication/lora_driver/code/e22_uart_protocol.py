# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : e22_uart_protocol.py
# @Description : Shared newline-delimited JSON protocol helpers
# @License : MIT

"""Shared UART wire protocol for the E22 bridge and client."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

# ======================================== 导入相关模块 =========================================
try:
    import ujson as json
except ImportError:
    import json

try:
    from ubinascii import hexlify, unhexlify
except ImportError:
    from binascii import hexlify, unhexlify


# ======================================== 全局变量 ============================================
PROTOCOL_VERSION = 1
MAX_LINE_LENGTH = 1200


# ======================================== 功能函数 ============================================
def encode_frame(message: dict) -> bytes:
    """
    执行 `encode_frame` 操作。
    Args:
        message (dict): 方法参数。
    Returns:
        bytes: 方法返回值。
    Raises:
        TypeError: 参数、状态或通信异常。
        E22UARTProtocolError: 参数、状态或通信异常。
    Notes:
        - 可能访问或修改驱动状态；ISR-safe: 否。
    ==========================================
    Encode one protocol dictionary as a newline-terminated UTF-8 frame.
    Args:
        message (dict): Method parameter.
    Returns:
        bytes: Method return value.
    Raises:
        TypeError: Parameter, state, or communication error.
        E22UARTProtocolError: Parameter, state, or communication error.
    Notes:
        - May access or modify driver state; ISR-safe: No.
    """
    if not isinstance(message, dict):
        raise TypeError("message must be dict")
    frame = json.dumps(message).encode("utf-8") + b"\n"
    if len(frame) > MAX_LINE_LENGTH:
        raise E22UARTProtocolError("frame exceeds maximum length")
    return frame


def decode_frame(frame: bytes) -> dict:
    """
    执行 `decode_frame` 操作。
    Args:
        frame (bytes): 方法参数。
    Returns:
        dict: 方法返回值。
    Raises:
        TypeError: 参数、状态或通信异常。
        E22UARTProtocolError: 参数、状态或通信异常。
    Notes:
        - 可能访问或修改驱动状态；ISR-safe: 否。
    ==========================================
    Decode and minimally validate one complete protocol frame.
    Args:
        frame (bytes): Method parameter.
    Returns:
        dict: Method return value.
    Raises:
        TypeError: Parameter, state, or communication error.
        E22UARTProtocolError: Parameter, state, or communication error.
    Notes:
        - May access or modify driver state; ISR-safe: No.
    """
    if not isinstance(frame, (bytes, bytearray)):
        raise TypeError("frame must be bytes-like")
    if not frame or len(frame) > MAX_LINE_LENGTH:
        raise E22UARTProtocolError("invalid frame length")
    try:
        message = json.loads(bytes(frame).decode("utf-8").strip())
    except Exception as error:
        raise E22UARTProtocolError("invalid JSON: %s" % error)
    if not isinstance(message, dict):
        raise E22UARTProtocolError("frame root must be an object")
    return message


def bytes_to_hex(data: bytes) -> str:
    """
    执行 `bytes_to_hex` 操作。
    Args:
        data (bytes): 方法参数。
    Returns:
        str: 方法返回值。
    Raises:
        TypeError: 参数、状态或通信异常。
    Notes:
        - 可能访问或修改驱动状态；ISR-safe: 否。
    ==========================================
    Encode bytes for JSON transport.
    Args:
        data (bytes): Method parameter.
    Returns:
        str: Method return value.
    Raises:
        TypeError: Parameter, state, or communication error.
    Notes:
        - May access or modify driver state; ISR-safe: No.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes-like")
    return hexlify(bytes(data)).decode("ascii")


def hex_to_bytes(value: str) -> bytes:
    """
    执行 `hex_to_bytes` 操作。
    Args:
        value (str): 方法参数。
    Returns:
        bytes: 方法返回值。
    Raises:
        TypeError: 参数、状态或通信异常。
        E22UARTProtocolError: 参数、状态或通信异常。
    Notes:
        - 可能访问或修改驱动状态；ISR-safe: 否。
    ==========================================
    Decode an even-length hexadecimal string.
    Args:
        value (str): Method parameter.
    Returns:
        bytes: Method return value.
    Raises:
        TypeError: Parameter, state, or communication error.
        E22UARTProtocolError: Parameter, state, or communication error.
    Notes:
        - May access or modify driver state; ISR-safe: No.
    """
    if not isinstance(value, str):
        raise TypeError("hex value must be str")
    if len(value) % 2:
        raise E22UARTProtocolError("hex value must have even length")
    try:
        return bytes(unhexlify(value))
    except Exception as error:
        raise E22UARTProtocolError("invalid hex value: %s" % error)


# ======================================== 自定义类 ============================================
class E22UARTProtocolError(ValueError):
    """
    E22UARTProtocolError 类。
    Attributes:
        继承 ValueError 属性。
    Methods:
        继承 ValueError 方法。
    Notes:
        - 用于区分驱动错误类型。
    ==========================================
    Raised when a UART frame is malformed.
    Attributes:
        Inherits ValueError attributes.
    Methods:
        Inherits ValueError methods.
    Notes:
        - Distinguishes a specific driver error category.
    """


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
