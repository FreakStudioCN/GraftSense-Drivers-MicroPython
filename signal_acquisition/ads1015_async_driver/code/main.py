try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from ads1015_async import ADS1015Async


async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2026/3/13 下午4:52
    # @Author  : mcauser
    # @File    : main.py
    # @Description : ADS1015读取电压并控制GPIO引脚电平切换  通过ADS1015采集通道0电压，周期性切换GPIO16输出电平并读取验证

    # ======================================== 导入相关模块 =========================================

    # ======================================== 全局变量 ============================================

    # ADS1015增益档位对应量程（V）：0=6.144 | 1=4.096(适配3.3V) | 2=2.048 | 3=1.024 | 4=0.512 | 5=0.256
    gain_to_voltage = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]
    # ADS1015 12位ADC最大原始值
    ads1015_max = 2047
    # 输出引脚初始状态
    output_state = 0

    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 400000
    TARGET_ADS1015_ADDR = 0x48

    # ======================================== 初始化配置 ===========================================

    await asyncio.sleep(3)
    print("FreakStudio: ADS1015 voltage read and GPIO pin level control")

    i2c_bus = None
    ads = None
    try:
        i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if TARGET_ADS1015_ADDR not in devices_list:
            raise SystemExit("I2C scan found no ADS1015")
        ads = ADS1015Async(i2c_bus, TARGET_ADS1015_ADDR)
        await ads.set_gain_async(1)
        print("Start reading AIN0 data (Pin16 outputs high/low level)...")
        while True:
            raw_value = await ads.read_async(0)
            # 计算实际电压
            voltage = raw_value * gain_to_voltage[await ads.get_gain_async()] / ads1015_max

            # 打印数据
            print(f"AIN0 raw value: {raw_value:4d} | Actual voltage: {voltage:.4f}V |")

            await asyncio.sleep(0.5)

    finally:
        try:
            if ads is not None:
                await ads.aclose()
        finally:
            if i2c_bus is not None:
                i2c_bus.deinit()

if __name__ == '__main__':
    asyncio.run(main())
