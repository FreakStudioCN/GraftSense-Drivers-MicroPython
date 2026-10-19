# MicroPython
# MIT license; Copyright (c) 2022 Roman Shevchik
# CRC8 计算模块
# 多项式 0x31 (x^8 + x^5 + x^4 + 1)，初始值 0xFF，无反射，无终止 XOR
#
# 示例：
#   输入 0x01 0x02 0x03 -> CRC-8: 0x87
#   输入 0~9            -> CRC-8: 0x52


def crc8(sequence: bytes, polynomial: int, init_value: int = 0x00, final_xor=0x00):
    mask = 0xFF
    crc = init_value & mask
    for item in sequence:
        crc ^= item & mask
        for _ in range(8):
            if crc & 0x80:
                crc = mask & ((crc << 1) ^ polynomial)
            else:
                crc = mask & (crc << 1)
    return crc ^ final_xor
