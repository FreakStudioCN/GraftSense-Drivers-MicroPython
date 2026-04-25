# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午2:15
# @Author  : hogeiha
# @File    : main.py
# @Description : RM3100三轴磁场传感器读取示例


# ======================================== 导入相关模块 =========================================

# 导入MicroPython硬件I2C与引脚控制模块
from machine import I2C, Pin

# 导入I2C总线适配器
from sensor_pack.bus_service import I2cAdapter

# 导入数学计算模块
import math

# 导入RM3100驱动模块
import rm3100mod

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C数据引脚编号
I2C_SDA_PIN = 4

# I2C时钟引脚编号
I2C_SCL_PIN = 5

# I2C通信频率
I2C_FREQ = 400000

# 需要采集的磁场轴
MEASURE_AXIS = "XYZ"

# RM3100采样更新率
UPDATE_RATE = 6

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x20,0x21,0x22,0x23]


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: RM3100 magnetic sensor")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = I2C(id=0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

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
            # 创建驱动需要的I2C适配器
            adapter = I2cAdapter(i2c_bus)
            # 自动识别并初始化对应传感器
            sensor = rm3100mod.RM3100(adapter=adapter, address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 打印自检开始提示
print("Self Test...")

# 执行传感器自检
self_test = sensor.perform_self_test()

# 合并三个轴的自检结果
self_test_result = self_test[0] and self_test[1] and self_test[2]

# 打印传感器自检结果
print("Self Test result: {}\t{}".format(self_test_result, self_test))

# 打印传感器芯片识别值
print("Sensor id: {}".format(sensor.get_id()))

# 打印分隔线
print(16 * "_")

# 依次读取每个轴的周期计数值
for axis in MEASURE_AXIS:
    print("{} axis cycle count value: {}".format(axis, sensor.get_axis_cycle_count(axis)))

# 启动单次测量模式
sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=True)

# 打印当前是否处于连续测量模式
print("Is continuous meas mode: {}".format(sensor.is_continuous_meas_mode()))

# 打印单次测量提示
print("Single meas mode measurement")

# 获取当前更新率对应的转换等待时间
wait_time_us = rm3100mod.get_conversion_cycle_time(UPDATE_RATE)

# 设置微秒延时函数
delay_func = time.sleep_us

# 等待单次测量完成
delay_func(wait_time_us)

# 判断单次测量数据是否已经准备完成
if sensor.is_data_ready():

    # 依次读取每个轴的磁场值
    for axis in MEASURE_AXIS:
        print("{} axis magnetic field value: {}".format(axis, sensor.get_meas_result(axis)))

# 打印连续测量提示
print("Continuous meas mode measurement")

# 启动连续测量模式
sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=False)

# 打印当前是否处于连续测量模式
print("Is continuous meas mode: {}".format(sensor.is_continuous_meas_mode()))


# ========================================  主程序  ============================================

# 捕获用户中断以便正常退出示例
try:

    # 持续读取连续测量模式下的三轴磁场数据
    for mag_field_comp in sensor:

        # 按当前更新率等待下一组测量数据
        delay_func(wait_time_us)

        # 判断当前读取结果是否有效
        if mag_field_comp:

            # 计算三轴合成磁场强度
            mfs = math.sqrt(sum(map(lambda val: val ** 2, mag_field_comp)))

            # 打印三轴磁场值与合成磁场强度
            print(
                "X: {}; Y: {}; Z: {}; mag field strength: {}".format(
                    mag_field_comp[0],
                    mag_field_comp[1],
                    mag_field_comp[2],
                    mfs,
                )
            )

# 用户按下中断键时退出连续测量
except KeyboardInterrupt:

    # 打印测量停止提示
    print("Measurement stopped")