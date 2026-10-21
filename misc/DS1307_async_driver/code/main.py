try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C, RTC
import time
from ds1307_async import DS1307Async


async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2025/9/8 下午4:52
    # @Author  : 缪贵成
    # @File    : main.py
    # @Description : rtc时钟测试  设置时间读取时间 设置pico rtc时间

    # ======================================== 全局变量 ============================================

    DS1307_ADDRESS = None

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    await asyncio.sleep(3)
    print("FreakStudio: test ds1307 RTC now")

    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

    # 开始扫描I2C总线上的设备，返回从机地址的列表
    devices_list: list[int] = i2c.scan()
    print("START I2C SCANNER")
    # 若devices list为空，则没有设备连接到I2C总线上
    if len(devices_list) == 0:
        # 若非空，则打印从机设备地址
        print("No i2c device !")
    else:
        # 遍历从机设备地址列表
        print("i2c devices found:", len(devices_list))
    for device in devices_list:
        # 判断设备地址是否为的ds1307地址
        if 0x60 <= device <= 0x70:
            # 假设第一个找到的设备是ds1307地址
            print("I2c hexadecimal address:", hex(device))
            DS1307_ADDRESS = device

    if DS1307_ADDRESS is None:
        raise RuntimeError("No DS1307 device found")
    ds1307rtc = DS1307Async(i2c, DS1307_ADDRESS)
    print("DS1307 attributes:", dir(ds1307rtc))
    try:

        # ========================================  主程序  ============================================

        # 振荡器开关测试
        await ds1307rtc.set_disable_oscillator_async(True)
        print("disable_oscillator =", await ds1307rtc.get_disable_oscillator_async())

        await ds1307rtc.set_disable_oscillator_async(False)
        print("disable_oscillator =", await ds1307rtc.get_disable_oscillator_async(), "\n")

        # 读取当前时间
        print("Current DS1307 datetime:", await ds1307rtc.get_datetime_async(), "\n")

        # 参数:(year, month, day, hour, minute, second, weekday, None)
        await ds1307rtc.set_datetime_async((2025, 9, 17, 17, 47, 17, 6))

        print("After setting datetime:", await ds1307rtc.get_datetime_async())

        await asyncio.sleep(3.9)
        print("After 3.9s:", await ds1307rtc.get_datetime_async(), "\n")

        print("DS1307 datetime formatted for Pico RTC:", await ds1307rtc.get_datetime_rtc_async(), "\n")

        print("Pico internal RTC time:", time.localtime(), "\n")

        rtc = RTC()
        rtc.datetime(await ds1307rtc.get_datetime_rtc_async())
        print("Pico RTC set from DS1307, now:", time.localtime())
    finally:
        await ds1307rtc.aclose()

if __name__ == '__main__':
    asyncio.run(main())
