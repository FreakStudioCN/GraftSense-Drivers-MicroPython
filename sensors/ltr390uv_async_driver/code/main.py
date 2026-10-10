try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import sys
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from ltr390uv_async import LTR390UVAsync

async def main():
    sensor = None
    i2c_bus = None
    try:
        # Python env   : MicroPython v1.23.0
        # -*- coding: utf-8 -*-
        # @Time    : 2026/4/16 下午2:30
        # @Author  : MicroPython Developer
        # @File    : main.py
        # @Description : LTR390UV紫外线/环境光传感器I2C自动扫描与数据采集程序


        # ======================================== 导入相关模块 =========================================



        # ======================================== 全局变量 ============================================

        # 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
        TARGET_SENSOR_ADDRS = [0x53]  # LTR390UV默认地址

        # I2C初始化（兼容I2C/SoftI2C）
        I2C_SDA_PIN = 4
        I2C_SCL_PIN = 5
        I2C_FREQ = 400_000


        # ======================================== 功能函数 ============================================


        def show_header(caption: str, symbol: str = "*", count: int = 40):
            """
            打印分隔标题头
            Args: caption - 标题文字；symbol - 分隔符字符；count - 分隔符重复次数

            Raises: 无

            Notes: 用于在控制台输出明显的分区标识

            ==========================================
            Print a formatted header line
            Args: caption - title text; symbol - separator character; count - repetition count

            Raises: None

            Notes: Used to output clear section markers in console
            """
            print(count * symbol[0])
            print(caption)
            print(count * symbol[0])


        # ======================================== 自定义类 ============================================


        # ======================================== 初始化配置 ===========================================

        await asyncio.sleep_ms(3000)
        print("FreakStudio: LTR390UV sensor auto scan and data acquisition")
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
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
        sensor = None  # 初始化传感器对象占位符
        for device in devices_list:
            if device in TARGET_SENSOR_ADDRS:
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 自动识别并初始化对应传感器
                    adapter = I2cAdapter(i2c_bus)
                    sensor = LTR390UVAsync(adapter=adapter)
                    print("Sensor initialization successful")
                    break
                except Exception as e:
                    print(f"Sensor Initialization failed: {e}")
                    continue
        else:
            # 未找到目标设备，抛出异常
            raise Exception("No target sensor device found in I2C bus")


        # ========================================  主程序  ============================================

        # 使用已初始化的传感器对象
        als = sensor

        # 读取传感器ID信息
        _id = await als.get_id_async()
        print(f"Part number id: {_id[0]}; Revision id: {_id[1]};")
        # 执行软件复位
        await als.soft_reset_async()
        print("Software reset successfully!")

        # 启动ALS测量模式（环境光）
        await als.start_measurement_async(uv_mode=False)
        # 获取转换周期时间
        cct_ms = await als.get_conversion_cycle_time_async()
        # 打印当前配置参数
        print(f"uv_mode: {await als.get_uv_mode_async()}")
        print(f"meas_rate: {await als.get_meas_rate_async()}")
        print(f"resolution: {await als.get_resolution_async()}")
        print(f"gain: {await als.get_gain_async()}")
        # 获取传感器状态
        status = await als.get_status_async()
        print(status)

        # 显示ALS模式标题
        show_header(f"ALS mode. LUX out! uv_mode: {await als.get_uv_mode_async()}")

        # 循环采集1000次环境光数据
        for i in range(1000):
            await asyncio.sleep_ms(cct_ms)
            print(f"lux: {await als.get_illumination_async(raw=False)}")

        # 切换到UV测量模式
        await als.start_measurement_async(uv_mode=True)
        # 重新获取转换周期时间
        cct_ms = await als.get_conversion_cycle_time_async()

        # 显示UV模式标题
        show_header(f"UV mode. RAW only out! uv_mode: {await als.get_uv_mode_async()}")

        # 计数器初始化
        cnt = 0
        # 保持来源的 UV 原始读数顺序，同时每轮让出事件循环。
        while cnt <= 3_000:
            await asyncio.sleep_ms(cct_ms)
            raw = await als.get_illumination_async(raw=True)
            print(f"raw: {raw}")
            cnt += 1
    finally:
        if sensor is not None:
            await sensor.aclose()
        _deinit = getattr(i2c_bus, 'deinit', None)
        if _deinit is not None:
            _deinit()
if __name__ == '__main__':
    asyncio.run(main())
