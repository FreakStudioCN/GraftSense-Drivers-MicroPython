try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from ds3231maxim_async import DS3231Async, I2cAdapterAsync

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2026/3/13 下午6:00
    # @Author  : octaprog7
    # @File    : main.py
    # @Description : DS3231实时时钟测试  设置并读取时间 读取温度状态等信息 配置闹钟并循环检测闹钟标志

    # ======================================== 导入相关模块 =========================================

    # 导入I2C和Pin模块用于硬件通信
    # 导入时间模块用于延时和获取本地时间

    # ======================================== 全局变量 ============================================

    # 定义I2C引脚和频率常量
    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 400_000
    # DS3231默认I2C地址
    TARGET_SENSOR_ADDR = 0x68

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    await asyncio.sleep(3)
    print("FreakStudio: DS3231 RTC Clock Test and Alarm Configuration")

    # 初始化I2C总线
    i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    # 开始扫描I2C总线上的设备
    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")
    # 检查I2C设备扫描结果
    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))
        # 遍历地址列表初始化目标传感器
        clock = None
        for device in devices_list:
            if device == TARGET_SENSOR_ADDR:
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 创建I2C适配器对象
                    adaptor = I2cAdapterAsync(i2c_bus)
                    # 创建DS3231实时时钟对象
                    clock = DS3231Async(adapter=adaptor)
                    print("Target sensor initialization successful")
                    break
                except Exception as e:
                    print(f"Sensor Initialization failed: {e}")
                    continue
        if clock is None:
            raise Exception("No DS3231 found")

    # ========================================  主程序  ============================================

    # 获取当前本地时间
    tr = time.localtime()
    # 打印要设置的时间
    print(f"set time to actual value: {tr}")
    # 将本地时间设置到DS3231时钟
    await clock.set_time_async(tr)

    # 打印提示信息，调用get_time方法
    print("Call get_time() method")
    # 读取DS3231当前时间
    tr = await clock.get_time_async()
    # 打印读取到的本地时间
    print(f"Local time: {tr}")

    # 读取DS3231内部温度传感器数据
    tmp = await clock.get_temperature_async()
    # 读取DS3231状态寄存器值
    stat = await clock.get_status_async()
    # 读取DS3231控制寄存器值
    ctrl = await clock.get_control_async()
    # 读取DS3231老化偏移值
    ao = await clock.get_aging_offset_async()
    # 打印温度、状态、控制寄存器、老化偏移值
    print(f"Temperature: {tmp}\tstatus: {hex(stat)}\tcontrol: {hex(ctrl)}\taging offset: {hex(ao)}")

    # 打印提示信息，显示闹钟时间
    print("Alarm times:")
    # 读取并打印第一个闹钟（alarm 0）的配置
    print("get_alarm(0):", await clock.get_alarm_async(0))
    # 读取并打印第二个闹钟（alarm 1）的配置
    print("get_alarm(1):", await clock.get_alarm_async(1))

    # 定义闹钟时间元组（秒、分、时、日）
    at = (00, 10, 11, 12)
    # 设置闹钟匹配模式为0（每秒匹配，每分钟触发）
    k = 0
    # 打印提示信息，调用set_alarm方法
    print(f"Call: set_alarm({at}, {k})")
    # 配置第一个闹钟（alarm 0）的时间和匹配模式
    await clock.set_alarm_async(at, k, k)
    # 读取并打印配置后的第一个闹钟信息
    print(f"get_alarm({k}):", await clock.get_alarm_async(k))
    # 设置闹钟匹配模式为1
    k = 1
    # 配置第二个闹钟（alarm 1）的时间和匹配模式（时分匹配）
    await clock.set_alarm_async(at, k, k)
    # 读取并打印配置后的第二个闹钟信息
    print(f"get_alarm({k}):", await clock.get_alarm_async(k))

    # 打印提示信息，使用迭代器读取时间
    print("Using iterator...")
    # 循环迭代读取DS3231时间并检测闹钟标志
    try:
        while True:
            ltime = await clock.get_time_async()
            f = await clock.get_alarm_flags_async()
            print(f"Local time: {ltime}\talarm flags: {f}")
            await asyncio.sleep_ms(1000)
    finally:
        await clock.aclose()

if __name__ == '__main__':
    asyncio.run(main())
