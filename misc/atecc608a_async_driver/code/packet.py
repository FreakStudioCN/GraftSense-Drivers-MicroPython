# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : stewedio
# @File    : packet.py
# @Description : ATECC608A/ATECC508A command packet serialization with I2C CRC-16
# @License : MIT
__version__ = "1.1.0"
__author__ = "stewedio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import ustruct
import utime
from ubinascii import hexlify
import constant as ATCA

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# 命令包序列化与 CRC-16 计算类
# Command packet serialization and CRC-16 computation
# 注：at_crc 使用纯 Python CRC，便于跨 MicroPython 端口编译
# Note: at_crc uses portable pure Python for cross-port compatibility.
class ATCAPacket(object):
    """ATCAPacket"""

    struct_format = "<BBBH{:d}s"

    def __init__(self, txsize=ATCA.ATCA_CMD_SIZE_MIN, opcode=0, param1=0, param2=0, request_data=b"", response_data=b"", device="ATECC508A"):
        self.txsize = txsize
        self.opcode = opcode
        self.param1 = param1
        self.param2 = param2
        self.device = device
        self._request_data = request_data
        self._response_data = response_data or bytearray(ATCA.ATCA_CMD_SIZE_MAX)

    def __str__(self):
        return (
            "<{:s}" " txsize={:d}" " opcode=0x{:02x}" " param1=0x{:02x}" " param2=0x{:04x}" " request_data={:s}" " response_data={:s}" " device={:s}>"
        ).format(
            self.__class__.__name__,
            self.txsize,
            self.opcode,
            self.param1,
            self.param2,
            hexlify(self.request_data),
            hexlify(self.response_data),
            self.device,
        )

    def __repr__(self):
        return str(self)

    def __getitem__(self, i):
        return self._response_data[i]

    # 动态属性：delay 为指令执行时间，request/response 提供便捷访问
    # Dynamic attributes: delay is command execution time, request/response provide convenient access
    def __getattr__(self, name):
        if name == "delay":
            return ATCA.EXECUTION_TIME.get(self.device, "ATECC508A").get(self.opcode, 250)
        elif name == "request_length":
            return len(self._request_data)
        elif name == "request_data":
            return self._request_data
        elif name == "request_data_mv":
            return memoryview(self._request_data)
        elif name == "response_length":
            return len(self._response_data)
        elif name == "response_data":
            return self._response_data
        elif name == "response_data_mv":
            return memoryview(self._response_data)
        else:
            raise AttributeError(name)

    # 将命令序列化为 I2C 传输缓冲区（含 CRC-16 校验）
    # Serialize command into I2C transfer buffer (with CRC-16 checksum)
    def to_buffer(self):
        params = self.response_data or bytearray(self.txsize)
        ustruct.pack_into(
            ATCAPacket.struct_format.format(len(self.request_data)), params, 0, self.txsize, self.opcode, self.param1, self.param2, self.request_data
        )
        self.at_crc(params, self.txsize - ATCA.ATCA_CRC_SIZE)
        return params

    # CRC-16 计算（纯 Python，多项式 0x8005）
    # CRC-16 computation (polynomial 0x8005)
    def at_crc(self, src, length: int) -> int:
        polynom = 0x8005
        crc = 0
        for i in range(length):
            d = src[i]
            for b in range(8):
                data_bit = 1 if d & 1 << b else 0
                crc_bit = crc >> 15 & 0xFF
                crc = crc << 1 & 0xFFFF
                if data_bit != crc_bit:
                    crc = crc ^ polynom & 0xFFFF
        src[length] = crc & 0x00FF
        src[length + 1] = crc >> 8 & 0xFF
        return crc

    # 纯 Python 版本 CRC-16 备用实现（Viper 不可用时使用）
    # Pure Python fallback CRC-16 implementation (when Viper is unavailable)
    # def at_crc(self, src, length):
    #     polynom = 0x8005
    #     crc = 0
    #     for i in range(length):
    #         d = src[i]
    #         for b in range(8):
    #             data_bit = 1 if d & 1 << b else 0
    #             crc_bit = crc >> 15 & 0xff
    #             crc = crc << 1 & 0xffff
    #             if data_bit != crc_bit:
    #                 crc = crc ^ polynom & 0xffff
    #     src[length] = crc & 0x00ff
    #     src[length+1] = crc >> 8 & 0xff
    #     return crc


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
