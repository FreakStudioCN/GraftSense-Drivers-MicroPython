# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Bosch Sensortec
# @File    : bmp581mod_async.py
# @Description : Explicit bounded-transaction BMP581 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import _gs_bmp581_bmp581mod as source
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class Bmp581Async(source.Bmp581):
    async def init_hardware_async(self):
        return self.init_hardware()
    async def get_id_async(self):
        return self.get_id()
    async def get_status_async(self, status_source=2):
        return self.get_status(status_source)
    async def get_pressure_async(self):
        return self.get_pressure()
    async def get_temperature_async(self):
        return self.get_temperature()
    async def soft_reset_async(self):
        return self.soft_reset()
    async def start_measurement_async(self, mode=1, output_data_rate=10):
        return self.start_measurement(mode, output_data_rate)
    async def is_data_ready_async(self):
        return self.is_data_ready()
    async def set_temperature_only_async(self, value):
        self.temperature_only = value

    async def set_temp_oversampling_async(self, value):
        self.temp_oversampling = value

    async def set_pressure_oversampling_async(self, value):
        self.pressure_oversampling = value

    async def get_oversampling_async(self):
        return self.oversampling

    async def get_power_mode_async(self):
        return self.power_mode

    async def get_output_data_rate_async(self):
        return self.output_data_rate

    async def get_iir_config_async(self):
        return self.iir_config

    async def get_effective_osr_rating_async(self):
        return self.effective_osr_rating
    async def aclose(self):
        return None
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ==============================================