# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午4:30
# @Author  : octaprog7
# @File    : converter.py
# @Description : 单位转换工具，将帕斯卡转换为毫米汞柱
# @License : MIT
__version__ = "0.1.0"
__author__ = "Unknown"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

"""Преобразование значений из одной единицы измерения в другую.
Converting values from one unit of measure to another"""

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def pa_mmhg(value: float) -> float:
    """
    将大气压力从帕斯卡转换为毫米汞柱
    Args:
        value (float): 压力值（帕斯卡）

    Returns:
        float: 转换后的压力值（毫米汞柱）

    Notes:
        转换系数为 7.50062E-3

    ==========================================
    Convert atmospheric pressure from Pascals to millimeters of mercury
    Args:
        value (float): Pressure value in Pascals

    Returns:
        float: Converted pressure value in mmHg

    Notes:
        Conversion factor is 7.50062E-3
    """
    return 7.50062E-3 * value

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================