# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Peter Hinch
# @File    : mia_m10q_async.py
# @Description : MicropyGPS 显式异步解析接口
# @License : MIT

# ======================================== 导入相关模块 =========================================
from mia_m10q import MicropyGPS

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MicropyGPSAsync(MicropyGPS):
    async def latitude_async(self): return self.latitude
    async def longitude_async(self): return self.longitude
    async def start_logging_async(self, target_file, mode="append"): return self.start_logging(target_file, mode)
    async def stop_logging_async(self): return self.stop_logging()
    async def write_log_async(self, log_string): return self.write_log(log_string)
    async def gprmc_async(self): return self.gprmc()
    async def gpgll_async(self): return self.gpgll()
    async def gpvtg_async(self): return self.gpvtg()
    async def gpgga_async(self): return self.gpgga()
    async def gpgsa_async(self): return self.gpgsa()
    async def gpgsv_async(self): return self.gpgsv()
    async def new_sentence_async(self): return self.new_sentence()
    async def update_async(self, new_char): return self.update(new_char)
    async def new_fix_time_async(self): return self.new_fix_time()
    async def satellite_data_updated_async(self): return self.satellite_data_updated()
    async def unset_satellite_data_updated_async(self): return self.unset_satellite_data_updated()
    async def satellites_visible_async(self): return self.satellites_visible()
    async def time_since_fix_async(self): return self.time_since_fix()
    async def compass_direction_async(self): return self.compass_direction()
    async def latitude_string_async(self): return self.latitude_string()
    async def longitude_string_async(self): return self.longitude_string()
    async def speed_string_async(self, unit="kph"): return self.speed_string(unit)
    async def date_string_async(self, formatting="s_mdy", century="20"): return self.date_string(formatting, century)
    async def deinit_async(self): return self.deinit()
    async def aclose(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================