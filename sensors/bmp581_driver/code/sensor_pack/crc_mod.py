# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午4:45
# @Author  : octaprog7
# @File    : crc_mod.py
# @Description : CRC-8校验计算模块，支持自定义多项式、初始值和掩码
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

"""
MIT License
Copyright (c) 2022 Roman Shevchik

реализация вычисление CRC
 8 бит
 полином 0x31 (x^8 + x^5 + x^4 + 1)
 начальное значение 0xFF
 отражение входа: нет
 отражение выхода: нет
 завершающий XOR: нет

 Примеры CRC-8:
    Входная последовательность: 0x01 0x02 0x03
    CRC-8: 0x87
    Входная последовательность: 0 1 2 3 4 5 6 7 8 9
    CRC-8: 0x52"""

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def crc8(sequence, polynomial: int, init_value: int = 0x00) -> int:
    """
    计算 CRC-8 校验值
    Args:
        sequence (bytes, bytearray, list): 输入数据序列（字节或整数列表）
        polynomial (int): CRC 多项式（8位）
        init_value (int): 初始值，默认为 0x00

    Returns:
        int: 计算得到的 CRC-8 值（0-255）

    Notes:
        使用标准 CRC-8 算法，逐字节处理，每个字节按位计算。
        如果初始值设置为 0xFF，多项式 0x31，则符合常见的 CRC-8 规范。
        算法实现中使用了 0xFF 掩码确保结果在 8 位范围内。

    ==========================================
    Calculate CRC-8 checksum
    Args:
        sequence (bytes, bytearray, list): Input data sequence (bytes or list of integers)
        polynomial (int): CRC polynomial (8-bit)
        init_value (int): Initial value, default 0x00

    Returns:
        int: Computed CRC-8 value (0-255)

    Notes:
        Uses standard CRC-8 algorithm, processing byte by byte, each byte bitwise.
        If init_value is set to 0xFF and polynomial 0x31, it conforms to common CRC-8 spec.
        The implementation uses 0xFF mask to ensure result stays within 8 bits.
    """
    mask = 0xFF
    crc = init_value & mask
    for item in sequence:
        crc ^= item & mask
        for _ in range(8):
            if crc & 0x80:
                crc = mask & ((crc << 1) ^ polynomial)
            else:
                crc = mask & (crc << 1)
    return crc


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
