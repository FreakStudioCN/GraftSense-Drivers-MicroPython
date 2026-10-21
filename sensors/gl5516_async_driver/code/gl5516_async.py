# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : gl5516_async.py
# @Description : Explicit bounded-transaction GL5516 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import gl5516 as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class GL5516Async(source.GL5516):
    async def read_light_intensity_async(self): return self.read_light_intensity()
    async def set_min_light_async(self): return self.set_min_light()
    async def set_max_light_async(self): return self.set_max_light()
    async def get_calibrated_light_async(self): return self.get_calibrated_light()
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================