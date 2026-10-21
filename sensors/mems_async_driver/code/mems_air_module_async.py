# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense
# @File    : mems_air_module_async.py
# @Description : MEMS 多路复用器协作采样接口
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from mems_air_module import MEMSGasSensor, PCA9546ADR, AirQualityMonitor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MEMSGasSensorAsync(MEMSGasSensor):
    async def read_concentration_async(self): return self.read_concentration()
    async def calibrate_zero_async(self, calib_value=None): return self.calibrate_zero(calib_value)
    async def get_address_async(self): return self.get_address()
    async def get_type_async(self): return self.get_type()
    async def aclose(self): pass

class PCA9546ADRAsync(PCA9546ADR):
    async def write_ctl_async(self, ctl_byte): return self.write_ctl(ctl_byte)
    async def select_channel_async(self, channel): return self.select_channel(channel)
    async def disable_all_async(self): return self.disable_all()
    async def read_status_async(self): return self.read_status()
    async def current_mask_async(self): return self.current_mask()
    async def aclose(self): pass

class AirQualityMonitorAsync(AirQualityMonitor):
    async def register_sensor_async(self, channel, sensor_type, sensor_addr=MEMSGasSensor.ADDR7):
        return self.register_sensor(channel, sensor_type, sensor_addr)
    async def read_sensor_async(self, sensor_type):
        return self.read_sensor(sensor_type)
    async def read_all_async(self):
        results = {}
        for sensor_type, channel in self.channel_map.items():
            self.pca.disable_all()
            self.pca.select_channel(channel)
            results[sensor_type] = self.sensors[channel].read_concentration()
            await asyncio.sleep_ms(MEMSGasSensor.OP_DELAY_MS)
        return results
    async def calibrate_sensor_async(self, sensor_type):
        return self.calibrate_sensor(sensor_type)
    async def aclose(self):
        self.sensors = {}
        self.channel_map = {}
        self.pca.disable_all()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================