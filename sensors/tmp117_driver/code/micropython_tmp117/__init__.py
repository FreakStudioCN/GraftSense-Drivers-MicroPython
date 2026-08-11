# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Jose D. Montoya
# @File    : __init__.py
# @Description : TMP117 driver package exports
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

from micropython_tmp117.tmp117 import ALERT_HYSTERESIS
from micropython_tmp117.tmp117 import ALERT_WINDOW
from micropython_tmp117.tmp117 import AVERAGE_1X
from micropython_tmp117.tmp117 import AVERAGE_8X
from micropython_tmp117.tmp117 import AVERAGE_32X
from micropython_tmp117.tmp117 import AVERAGE_64X
from micropython_tmp117.tmp117 import CONTINUOUS_CONVERSION_MODE
from micropython_tmp117.tmp117 import ONE_SHOT_MODE
from micropython_tmp117.tmp117 import SHUTDOWN_MODE
from micropython_tmp117.tmp117 import TMP117

# ==================== 全局变量 ====================

__all__ = (
    "ALERT_HYSTERESIS",
    "ALERT_WINDOW",
    "AVERAGE_1X",
    "AVERAGE_8X",
    "AVERAGE_32X",
    "AVERAGE_64X",
    "CONTINUOUS_CONVERSION_MODE",
    "ONE_SHOT_MODE",
    "SHUTDOWN_MODE",
    "TMP117",
)

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================

# ==================== 初始化配置 ====================

# ====================  主程序  ====================
