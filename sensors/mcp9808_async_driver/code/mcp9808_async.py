# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Kai Fricke
# @File    : mcp9808_async.py
# @Description : MCP9808 显式异步接口
# @License : MIT

# ======================================== 导入相关模块 =========================================
from _gs_mcp9808_mcp9808 import MCP9808

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MCP9808Async(MCP9808):
    async def get_temp_async(self): return self.get_temp()
    async def get_temp_int_async(self): return self.get_temp_int()
    async def set_shutdown_mode_async(self, shdn=True): return self.set_shutdown_mode(shdn)
    async def set_alert_mode_async(self, enable_alert=True, output_mode=1, polarity=0, selector=0): return self.set_alert_mode(enable_alert, output_mode, polarity, selector)
    async def acknowledge_alert_irq_async(self): return self.acknowledge_alert_irq()
    async def set_alert_boundary_temp_async(self, boundary_register, value): return self.set_alert_boundary_temp(boundary_register, value)
    async def set_resolution_async(self, resolution): return self.set_resolution(resolution)
    async def deinit_async(self): return self.deinit()
    async def aclose(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================