# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : stewedio
# @File    : exceptions.py
# @Description : ATECC608A/ATECC508A custom exception hierarchy for CryptoAuthLib error handling
# @License : MIT

__version__ = "1.0.0"
__author__ = "stewedio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# 加密认证基础异常类
# Base exception for all crypto authentication errors
class CryptoError(Exception):
    pass


# 配置区已锁定异常（config zone locked, status=0x01）
class ConfigZoneLockedError(CryptoError):
    def __init__(self, *args):
        super().__init__("Config Zone Locked", *args)


# 数据区已锁定异常（data zone locked, status=0x02）
class DataZoneLockedError(CryptoError):
    def __init__(self, *args):
        super().__init__("Configuration Enabled", *args)


# 设备唤醒失败异常
class WakeFailedError(CryptoError):
    def __init__(self, *args):
        super().__init__("Device Wake failed", *args)


# CheckMac/Verify 验证失败异常（响应状态字节 0x01）
class CheckmacVerifyFailedError(CryptoError):
    def __init__(self, *args):
        super().__init__("response status byte indicates CheckMac/Verify failure " "(status byte = 0x01)", *args)


# 响应解析错误异常（响应状态字节 0x03）
class ParseError(CryptoError):
    def __init__(self, *args):
        super().__init__("response status byte indicates parsing error " "(status byte = 0x03)", *args)


# 看门狗即将到期异常（响应状态字节 0xEE）
class WatchDogAboutToExpireError(CryptoError):
    def __init__(self, *args):
        super().__init__(
            "response status indicate insufficient time to execute the given " "commmand begore watchdog timer will expire (status byte = 0xEE)",
            *args
        )


# CRC 校验错误异常（响应状态字节 0xFF）
class CrcError(CryptoError):
    def __init__(self, *args):
        super().__init__("response status byte indicates CRC error (status byte = 0xFF)", *args)


# 未知状态异常（响应状态字节无法识别）
class StatusUnknownError(CryptoError):
    def __init__(self, *args):
        super().__init__("Response status byte is unknown", *args)


# ECC 故障异常（响应状态字节 0x05）
class EccFaultError(CryptoError):
    def __init__(self, *args):
        super().__init__("response status byte is ECC fault (status byte = 0x05)", *args)


# 自检失败异常（芯片处于故障模式，响应状态字节 0x07）
class SelfTestError(CryptoError):
    def __init__(self, *args):
        super().__init__("response status byte is Self Test Error, " "chip in failure mode (status byte = 0x07)", *args)


# 随机数生成器健康测试异常
class HealthTestError(CryptoError):
    def __init__(self, *args):
        super().__init__("random number generator health test error", *args)


# 函数执行失败异常（芯片状态不正确）
class FunctionError(CryptoError):
    def __init__(self, *args):
        super().__init__("Function could not execute due to incorrect condition / state.", *args)


# 未指定通用错误异常
class GenericError(CryptoError):
    def __init__(self, *args):
        super().__init__("unspecified error", *args)


# 参数错误异常（越界、空指针等）
class BadArgumentError(CryptoError):
    def __init__(self, *args):
        super().__init__("bad argument (out of range, null pointer, etc.)", *args)


# 无效设备 ID 异常（ID 未设置）
class InvalidIdentifierError(CryptoError):
    def __init__(self, *args):
        super().__init__("invalid device id, id not set", *args)


# 无效大小异常（计数超出范围或大于缓冲区大小）
class InvalidSizeError(CryptoError):
    def __init__(self, *args):
        super().__init__("Count value is out of range or greater than buffer size.", *args)


# CRC 接收错误异常
class BadCrcError(CryptoError):
    def __init__(self, *args):
        super().__init__("incorrect CRC received", *args)


# 接收错误异常（等待响应超时，已接收部分字节）
class ReceiveError(CryptoError):
    def __init__(self, *args):
        super().__init__("Timed out while waiting for response. " "Number of bytes received is > 0.", *args)


# 无响应异常（命令层轮询响应失败）
class NoResponseError(CryptoError):
    def __init__(self, *args):
        super().__init__("error while the Command layer is polling for a command response.", *args)


# 重新同步成功（但需要唤醒设备）
class ResyncWithWakeupError(CryptoError):
    def __init__(self, *args):
        super().__init__("Re-synchronization succeeded, but only after generating a Wake-up", *args)


# 奇偶校验错误异常（需要奇偶校验的协议）
class ParityError(CryptoError):
    def __init__(self, *args):
        super().__init__("for protocols needing parity", *args)


# 发送超时异常（Microchip PHY 协议，等待主设备超时）
class TransmissionTimeoutError(CryptoError):
    def __init__(self, *args):
        super().__init__("for Microchip PHY protocol, " "timeout on transmission waiting for master", *args)


# 接收超时异常（Microchip PHY 协议，等待主设备超时）
class ReceiveTimeoutError(CryptoError):
    def __init__(self, *args):
        super().__init__("for Microchip PHY protocol, timeout on receipt waiting for master", *args)


# 通信错误异常（与设备通信失败）
class CommunicationError(CryptoError):
    def __init__(self, *args):
        super().__init__("Communication with device failed. " "Same as in hardware dependent modules.", *args)


# 超时异常（等待响应超时，接收字节数为 0）
class TimeOutError(CryptoError):
    def __init__(self, *args):
        super().__init__("Timed out while waiting for response. " "Number of bytes received is 0.", *args)


# 不支持的操作码异常
class BadOpcodeError(CryptoError):
    def __init__(self, *args):
        super().__init__("Opcode is not supported by the device", *args)


# 命令执行错误异常（响应状态字节 0x0F）
class ExecutionError(CryptoError):
    def __init__(self, *args):
        super().__init__(
            "chip was in a state where it could not execute the command, response "
            "status byte indicates command execution error (status byte = 0x0F)",
            *args
        )


# 未实现功能异常
class UnimplementedError(CryptoError):
    def __init__(self, *args):
        super().__init__("Function or some element of it hasn't been implemented yet", *args)


# 断言失败异常（运行时一致性检查失败）
class AssertionFailure(CryptoError):
    def __init__(self, *args):
        super().__init__("Code failed run-time consistency check", *args)


# 发送失败异常（写入失败）
class TransmissionError(CryptoError):
    def __init__(self, *args):
        super().__init__("Failed to write", *args)


# 区未锁定异常（所需区域未被锁定）
class ZoneNotLockedError(CryptoError):
    def __init__(self, *args):
        super().__init__("required zone was not locked", *args)


# 未发现设备异常（Kit 协议设备发现失败）
class NoDevicesFoundError(CryptoError):
    def __init__(self, *args):
        super().__init__("For protocols that support device discovery (kit protocol), " "no devices were found", *args)


# 不支持的设备异常（芯片型号不在支持列表中）
class UnsupportedDeviceError(CryptoError):
    def __init__(self, *args):
        super().__init__(*args)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
