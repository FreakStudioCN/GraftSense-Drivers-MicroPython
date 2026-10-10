# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : octaprog7
# @File    : bmp390_async.py
# @Description : Explicit bounded-transaction BMP390 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
import bmp390 as source

# ======================================== 全局变量 ============================================
I2cAdapter = source.I2cAdapter

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class Bmp390Async(source.Bmp390):
    async def get_id_async(self):
        return self.get_id()

    async def soft_reset_async(self, reset_or_flush=True):
        return self.soft_reset(reset_or_flush)

    async def get_calibration_coefficient_async(self, index):
        return self.get_calibration_coefficient(index)

    async def get_event_async(self):
        return self.get_event()

    async def get_int_status_async(self):
        return self.get_int_status()

    async def get_fifo_length_async(self):
        return self.get_fifo_length()

    async def set_oversampling_async(self, pressure_oversampling, temperature_oversampling):
        return self.set_oversampling(pressure_oversampling, temperature_oversampling)

    async def set_sampling_period_async(self, period):
        return self.set_sampling_period(period)

    async def set_iir_filter_async(self, value):
        return self.set_iir_filter(value)

    async def start_measurement_async(self, enable_press=True, enable_temp=True, mode=2):
        return self.start_measurement(enable_press, enable_temp, mode)

    async def get_data_status_async(self):
        return self.get_data_status()

    async def get_temperature_async(self):
        return self.get_temperature()

    async def get_pressure_async(self):
        return self.get_pressure()

    async def get_sensor_time_async(self):
        return self.get_sensor_time()

    async def get_power_mode_async(self):
        return self.get_power_mode()

    async def get_conversion_cycle_time_async(self):
        return self.get_conversion_cycle_time()

    async def aclose(self):
        return None

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================