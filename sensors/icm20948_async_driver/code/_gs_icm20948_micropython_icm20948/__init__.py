# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya
# @File    : __init__.py
# @Description : Package exports for the ICM20948 MicroPython driver.
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from _gs_icm20948_micropython_icm20948.icm20948 import ICM20948 as _ICM20948

# ======================================== 全局变量 ============================================

__all__ = ("ICM20948",)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class ICM20948(_ICM20948):
    """Package-level source-compatible export with explicit lifecycle ownership."""

    def deinit(self):
        """Preserve the source shutdown sequence through the public export."""
        return super().deinit()
# ======================================== 初始化配置 ===========================================

# ========================================  主程序 ============================================
