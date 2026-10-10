# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : leeqingshui
# @File    : jedm_gas_meas_async.py
# @Description : JEDM gas measurement asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from jedm_gas_meas import JEDMGasMeas

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class JEDMGasMeasAsync(JEDMGasMeas):
    """Explicit async entry points for bounded source I2C transactions."""

    async def read_concentration_async(self):
        return self.read_concentration()

    async def calibrate_zero_async(self, calib_value=None):
        return self.calibrate_zero(calib_value)

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================