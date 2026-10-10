# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : gp2y0a21yk_async.py
# @Description : Explicit bounded-transaction GP2Y0A21YK async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import gp2y0a21yk as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class GP2Y0A21YKAsync(source.GP2Y0A21YK):
    async def begin_async(self, distance_pin, vcc_pin=None): return self.begin(distance_pin, vcc_pin)
    async def set_averaging_async(self, avg): return self.set_averaging(avg)
    async def set_ref_voltage_async(self, ref_v): return self.set_ref_voltage(ref_v)
    async def set_enabled_async(self, status): return self.set_enabled(status)
    async def get_distance_raw_async(self): return self.get_distance_raw()
    async def get_distance_volt_async(self): return self.get_distance_volt()
    async def get_distance_centimeter_async(self): return self.get_distance_centimeter()
    async def is_closer_async(self, threshold): return self.is_closer(threshold)
    async def is_farther_async(self, threshold): return self.is_farther(threshold)
    async def deinit_async(self): return self.deinit()
    async def aclose(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================