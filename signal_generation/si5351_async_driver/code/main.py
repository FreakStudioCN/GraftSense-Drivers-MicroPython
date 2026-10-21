try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, I2C
from silicon5351_async import SI5351_I2CAsync

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2025/09/08 10:00
    # @Author  : 侯钧瀚
    # @File    : mian.py
    # @Description : silicon5351时钟示例 for MicroPython

    # ======================================== 导入相关模块 =========================================

    # ======================================== 全局变量 ============================================

    # 晶振频率 25 MHz
    crystal = 25e6
    # PLL 倍频系数 (25MHz * 15 = 375 MHz)
    mul = 15
    # 输出频率 2 MHz（最大 200 MHz）
    freq = 2.0e6
    # 正交输出标志（最低输出频率 = PLL / 128）
    quadrature = True
    # 反相输出标志（四相模式下忽略）
    invert = False

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试消息
    print("FreakStudio: Use silicon5351 to output clock signals.")
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
    si = None
    try:
        si = SI5351_I2CAsync(i2c, crystal=crystal)
        await si.initialize_async(timeout_ms=1000)
        await si.setup_pll_async(pll=0, mul=mul)
        await si.init_clock_async(output=0, pll=0)
        await si.set_freq_fixedpll_async(output=0, freq=freq)
        await si.enable_output_async(output=0)
        print(f"done freq={freq} mul={mul} quadrature={quadrature} invert={invert}")
        await asyncio.sleep(20)
    finally:
        try:
            if si is not None:
                await si.disable_output_async(output=0)
                await si.aclose()
        finally:
            i2c.deinit()

if __name__ == '__main__':
    asyncio.run(main())
