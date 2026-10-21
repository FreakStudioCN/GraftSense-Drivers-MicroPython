# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : ScioSense
# @File    : ens160sciosense_async.py
# @Description : Explicit bounded-transaction ENS160 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import _gs_ens160_ens160sciosense as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class Ens160Async(source.Ens160):
    async def get_id_async(self): return self.get_id()
    async def soft_reset_async(self): return self.soft_reset()
    async def get_config_async(self, raw=True): return self.get_config(raw)
    async def set_config_async(self, new_config): return self.set_config(new_config)
    async def set_ambient_temp_async(self, value_in_celsius): return self.set_ambient_temp(value_in_celsius)
    async def set_humidity_async(self, rel_hum): return self.set_humidity(rel_hum)
    async def get_firmware_version_async(self): return self.get_firmware_version()
    async def get_conversion_cycle_time_async(self): return self.get_conversion_cycle_time()
    async def start_measurement_async(self, start=True): return self.start_measurement(start)
    async def get_measurement_value_async(self, value_index): return self.get_measurement_value(value_index)
    async def get_data_status_async(self, raw=True): return self.get_data_status(raw)
    async def is_single_shot_mode_async(self): return self.is_single_shot_mode()
    async def is_continuously_mode_async(self): return self.is_continuously_mode()
    async def deinit_async(self): return self.deinit()
    async def aclose(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================