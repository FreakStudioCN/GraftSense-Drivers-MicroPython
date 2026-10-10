# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : December
# @File    : mics6814_async.py
# @Description : MiCS6814 调用方 ADC 注入适配器
# @License : MIT

# ======================================== 导入相关模块 =========================================
from mics6814 import MICS6814, Mics6814Reading

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class Mics6814ReadingAsync(Mics6814Reading):
    async def as_dict_async(self):
        return self.as_dict()


class MICS6814Async(MICS6814):
    """Async facade using caller-owned ADC instances."""

    def __init__(self, adc_co, adc_nh3, adc_no2, vref=3.3, load_resistor=56000.0, samples=1):
        for adc in (adc_co, adc_nh3, adc_no2):
            if not hasattr(adc, "read_u16"):
                raise ValueError("each ADC must provide read_u16()")
        super().__init__(adc_co, adc_nh3, adc_no2, vref, load_resistor, samples)

    async def read_raw_all_async(self):
        return self.read_raw_all()

    async def read_voltage_all_async(self):
        return self.read_voltage_all()

    async def read_all_async(self):
        return self.read_all()

    async def read_co_async(self):
        return self.read_co()

    async def read_nh3_async(self):
        return self.read_nh3()

    async def read_no2_async(self):
        return self.read_no2()

    async def aclose(self):
        self.adc_co = None
        self.adc_nh3 = None
        self.adc_no2 = None

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================