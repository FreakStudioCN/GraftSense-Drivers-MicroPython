# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/11 00:00
# @Author  : Jose D. Montoya
# @File    : __init__.py
# @Description : STTS22H driver package exports
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

from micropython_stts22h.stts22h import ODR_25_HZ
from micropython_stts22h.stts22h import ODR_50_HZ
from micropython_stts22h.stts22h import ODR_100_HZ
from micropython_stts22h.stts22h import ODR_200_HZ
from micropython_stts22h.stts22h import OUTPUT_DATA_RATE_VALUES
from micropython_stts22h.stts22h import STTS22H
from micropython_stts22h.stts22h import output_data_rate_values

# ==================== 全局变量 ====================

__all__ = (
    "ODR_25_HZ",
    "ODR_50_HZ",
    "ODR_100_HZ",
    "ODR_200_HZ",
    "OUTPUT_DATA_RATE_VALUES",
    "STTS22H",
    "output_data_rate_values",
)

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================

# ==================== 初始化配置 ====================

# ====================  主程序  ====================
