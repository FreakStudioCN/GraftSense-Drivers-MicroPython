# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : stewedio
# @File    : host.py
# @Description : ATECC608A host-side SHA-256 hashing helper
# @License : MIT

__version__ = "1.0.0"
__author__ = "stewedio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    import hashlib
except ImportError:
    import uhashlib as hashlib

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# 计算消息的 SHA-256 摘要（主机端哈希辅助函数）
# Compute SHA-256 digest of message (host-side hashing helper)
def atcah_sha256(message):
    return hashlib.sha256(message).digest()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
