# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:12
# @Author  : 缪贵成
# @File    : print_error.py
# @Description : 打印错误信息
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from . import IR_RX

# ======================================== 全局变量 ============================================

_errors = {
    IR_RX.BADSTART : 'Invalid start pulse',
    IR_RX.BADBLOCK : 'Error: bad block',
    IR_RX.BADREP : 'Error: repeat',
    IR_RX.OVERRUN : 'Error: overrun',
    IR_RX.BADDATA : 'Error: invalid data',
    IR_RX.BADADDR : 'Error: invalid address'
}

# ======================================== 功能函数 ============================================

def print_error(data: int) -> None:
    """
    打印 IR 接收错误信息。

    根据传入的错误代码打印对应的错误信息，如果代码未知则打印 Unknown error。

    Args:
        data (int): IR_RX 中定义的错误代码。

    Notes:
        仅用于调试和显示错误信息。
        不会抛出异常。
    ==========================================

    Print IR receive error message.

    Prints the corresponding error message for the given error code.
    If the code is unknown, prints "Unknown error code".

    Args:
        data (int): Error code defined in IR_RX.

    Notes:
        Only for debugging and displaying error messages.
        No exceptions are raised.
    """
    if data in _errors:
        print(_errors[data])
    else:
        print('Unknown error code:', data)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
