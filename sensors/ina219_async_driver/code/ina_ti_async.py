# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : ina_ti_async.py
# @Description : INA219 explicit asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from ina_ti import INA219
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class INA219Async(INA219):
    """Explicit async API; each I2C transaction remains bounded and synchronous."""
    async def set_bus_voltage_range_async(self, value: bool) -> None: self.bus_voltage_range = value
    async def set_bus_adc_resolution_async(self, value: int) -> None: self.bus_adc_resolution = value
    async def set_shunt_adc_resolution_async(self, value: int) -> None: self.shunt_adc_resolution = value
    async def set_max_expected_current_async(self, value: float) -> None: self.max_expected_current = value
    async def start_measurement_async(self, continuous: bool = True, enable_calibration: bool = True) -> int: return self.start_measurement(continuous, enable_calibration)
    async def get_conversion_cycle_time_async(self) -> int: return self.get_conversion_cycle_time()
    async def get_config_async(self) -> tuple: return self.get_config()
    async def get_shunt_voltage_async(self) -> float: return self.get_shunt_voltage()
    async def get_voltage_async(self) -> float: return self.get_voltage()
    async def get_current_async(self) -> float: return self.get_current()
    async def get_power_async(self) -> float: return self.get_power()
    async def soft_reset_async(self) -> None: return self.soft_reset()
    async def aclose(self) -> None: self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================