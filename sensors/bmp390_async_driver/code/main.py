try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : octaprog7
# @File    : main.py
# @Description : BMP390 压力传感器测试程序

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
from bmp390_async import Bmp390Async, I2cAdapter

# ======================================== 全局变量 ============================================
# 定义I2C配置常量
I2C_SCL_PIN = 5  # SCL引脚（针对Raspberry Pi Pico）
I2C_SDA_PIN = 4  # SDA引脚（针对Raspberry Pi Pico）
I2C_FREQ = 400_000  # I2C通信频率
TARGET_SENSOR_ADDR = 0x77  # BMP390默认I2C地址（可选0x76，根据硬件接线调整）


# ======================================== 功能函数 ============================================
def pa_mmhg(value: float) -> float:
    """
    将大气压力从帕斯卡转换为毫米汞柱。
    Args:
        value: 压力值，单位帕斯卡

    Returns:
        转换后的压力值，单位毫米汞柱

    Notes:
        转换系数为 7.50062e-3

    ==========================================
    Convert air pressure from Pascal to mm Hg.
    Args:
        value: pressure in Pascal

    Returns:
        pressure in mm Hg

    Notes:
        conversion factor is 7.50062e-3
    """
    return 7.50062e-3 * value


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

async def main():
    global sensor, i2c
    i2c_bus = None
    ps = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: BMP390 sensor test starting...")
        
        # 按示例风格初始化I2C总线 + 扫描I2C设备
        # 1. 初始化I2C总线
        i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        # 2. 开始扫描I2C总线上的设备
        devices_list: list[int] = i2c_bus.scan()
        print("START I2C SCANNER")
        
        # 3. 检查I2C设备扫描结果
        if len(devices_list) == 0:
            print("No i2c device !")
            raise SystemExit("I2C scan found no devices, program exited")
        else:
            print("i2c devices found:", len(devices_list))
        
        # 4. 遍历地址列表初始化目标传感器（匹配示例逻辑）
        ps = None  # 传感器对象初始化
        for device in devices_list:
            if device == TARGET_SENSOR_ADDR:
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 初始化I2C适配器和BMP390传感器
                    adaptor = I2cAdapter(i2c_bus)
                    ps = Bmp390Async(adaptor)
                    print("Target sensor (BMP390) initialization successful")
                    break
                except Exception as e:
                    print(f"Sensor Initialization failed: {e}")
                    continue
        else:
            # 遍历完未找到目标地址时抛出异常
            raise Exception(f"No BMP390 found (target address: {hex(TARGET_SENSOR_ADDR)}, found addresses: {[hex(d) for d in devices_list]})")
        
        # 读取传感器 ID
        res = await ps.get_id_async()
        print(f"chip_id: {res}")
        # 软件复位传感器，确保进入已知状态
        await ps.soft_reset_async()
        print(f"pwr mode: {await ps.get_power_mode_async()}")
        
        # 读取校准系数
        calibration_data = [await ps.get_calibration_coefficient_async(index) for index in range(14)]
        print(f"Calibration data: {calibration_data}")
        
        # 获取事件、中断状态和 FIFO 长度
        print(f"Event: {await ps.get_event_async()}; Int status: {await ps.get_int_status_async()}; FIFO length: {await ps.get_fifo_length_async()}")
        
        # 设置延时函数别名
        delay_func = asyncio.sleep_ms
        
        # 配置传感器参数
        await ps.set_oversampling_async(pressure_oversampling=2, temperature_oversampling=3)
        await ps.set_sampling_period_async(5)
        await ps.set_iir_filter_async(2)
        
        print("Single-shot measurement mode on demand!")
        print(f"pwr mode: {await ps.get_power_mode_async()}")
        print(f"conversion time in [us]: {await ps.get_conversion_cycle_time_async()}")
        for _ in range(20):
            # 启动单次测量模式
            await ps.start_measurement_async(enable_press=True, enable_temp=True, mode=1)
            await delay_func(300)
            # 读取数据就绪状态
            temperature_ready, pressure_ready, cmd_ready = await ps.get_data_status_async()
            if cmd_ready and pressure_ready:
                t, p = await ps.get_temperature_async(), await ps.get_pressure_async()
                pm = await ps.get_power_mode_async()
                print(f"Temperature: {t} \xB0C; pressure: {p} Pa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm} ")
            else:
                print(f"Data ready: temp {temperature_ready}, press {pressure_ready}")
        
        print("Continuous periodic measurement mode!")
        # 启动连续测量模式
        await ps.start_measurement_async(enable_press=True, enable_temp=True, mode=2)
        print(f"pwr mode: {await ps.get_power_mode_async()}")
        while True:
            await delay_func(300)
            d_status = await ps.get_data_status_async()
            if d_status.cmd_decoder_ready and d_status.press_ready:
                t, p, tme = await ps.get_temperature_async(), await ps.get_pressure_async(), await ps.get_sensor_time_async()
                pm = await ps.get_power_mode_async()
                print(f"Temperature: {t} \xB0C; pressure: {p} Pa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm}")
            else:
                print(f"Data ready: temp {d_status.temp_ready}, press {d_status.press_ready}")

    # ======================================== 主程序 ==============================================

    finally:
        if ps is not None:
            await ps.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()

asyncio.run(main())
