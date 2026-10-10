# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : gp2y0e03_async.py
# @Description : Explicit bounded-transaction GP2Y0E03 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import gp2y0e03 as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class GP2Y0E03Async(source.GP2Y0E03):
    async def shift_async(self, value=None): return self.shift(value)
    async def read_raw_async(self): return self.read_raw()
    async def read_async(self, raw=False): return self.read(raw)
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================