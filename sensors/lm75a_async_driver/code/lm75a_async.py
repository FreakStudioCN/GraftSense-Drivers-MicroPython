# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Mike Causer
# @File    : lm75a_async.py
# @Description : LM75A asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from lm75a import LM75A

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class LM75AAsync(LM75A):
    async def check_async(self):
        return self.check()

    async def config_async(self, shutdown=None, os_mode=None, os_polarity=None, os_fault_queue=None):
        return self.config(shutdown, os_mode, os_polarity, os_fault_queue)

    async def temp_async(self):
        return self.temp()

    async def tos_async(self, temp):
        return self.tos(temp)

    async def thyst_async(self, temp):
        return self.thyst(temp)

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================