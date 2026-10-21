# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/27 上午11:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : mlx90614双温区温度传感器测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from mlx90614 import MLX90614, MLX90615

# ======================================== 全局变量 =============================================

mlx61xaddr = None

# ======================================== 功能函数 =============================================


def test_sensor_realtime(sensor, name="Sensor", interval=1.0):
    """

    实时显示传感器温度数据，覆盖所有功能测试。
    Args:
        sensor: MLX90614 或 MLX90615 传感器实例
        name: 传感器名称，用于输出标识
        interval: 数据刷新间隔时间，单位秒

    Notes:
        测试内容包括内部方法、公共方法、属性访问和一次性读取功能
        双温区传感器会额外显示第二路物体温度数据
        内部方法测试可能因传感器型号不同而存在差异

    ==========================================

    Realtime display of sensor temperature data, covering all functional tests.

    Args:
        sensor: Instance of MLX90614 or MLX90615 sensor
        name: Sensor name for output identification
        interval: Data refresh interval in seconds

    Notes:
        Tests include internal methods, public methods, property access and one-time read function
        Dual-zone sensors will additionally display the second object temperature data
        Internal method tests may vary by sensor model
    """
    print("\n=== Realtime testing {} ===".format(name))
    print("Dual zone:", sensor.dual_zone)  # 输出是否为双温区传感器
    print("Press Ctrl+C to stop")  # 提示用户可以使用 Ctrl+C 停止测试

    try:
        while True:
            # ================= 内部方法测试 =================
            try:
                # 读取寄存器原始值（16 位）
                raw_ambient = sensor._read16(sensor._REGISTER_TA)
                raw_object = sensor._read16(sensor._REGISTER_TOBJ1)

                # 将寄存器原始值转换为摄氏温度
                temp_ambient_internal = sensor._read_temp(sensor._REGISTER_TA)
                temp_object_internal = sensor._read_temp(sensor._REGISTER_TOBJ1)
            except Exception as e:
                print("[Internal] Error:", e)
                raw_ambient = raw_object = temp_ambient_internal = temp_object_internal = None

            # ================= 公共方法测试 =================
            ambient = sensor.read_ambient()  # 读取环境温度
            obj = sensor.read_object()  # 读取物体温度
            # 双温区时读取第二路物体温度，否则为 None
            obj2 = sensor.read_object2() if sensor.dual_zone else None

            # ================= 属性访问测试 =================
            ambient_prop = sensor.ambient
            obj_prop = sensor.object
            obj2_prop = sensor.object2 if sensor.dual_zone else None

            # ================= 一次性读取功能测试 =================
            try:
                all_data = sensor.read()  # 一次性读取全部数据（返回字典）
            except Exception as e:
                all_data = None

            # ================= 数据输出 =================
            print("\n[{}] Data Snapshot".format(name))
            print("Raw ambient (internal):", raw_ambient)
            print("Raw object (internal):", raw_object)
            if temp_ambient_internal is not None:
                print("Temp ambient via _read_temp: {:.2f} °C".format(temp_ambient_internal))
            if temp_object_internal is not None:
                print("Temp object via _read_temp: {:.2f} °C".format(temp_object_internal))
            print("Ambient: {:.2f} °C".format(ambient))
            print("Object: {:.2f} °C".format(obj))
            if sensor.dual_zone:
                print("Object2: {:.2f} °C".format(obj2))
            print("Property ambient: {:.2f} °C".format(ambient_prop))
            print("Property object: {:.2f} °C".format(obj_prop))
            if sensor.dual_zone:
                print("Property object2: {:.2f} °C".format(obj2_prop))
            print("Read all:", all_data)

            # 间隔一段时间再刷新
            time.sleep(interval)

    except KeyboardInterrupt:
        # 用户按 Ctrl+C 时退出循环
        print("\nRealtime testing stopped")


# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 硬件上电延时，保证传感器初始化完成
time.sleep(3)
print("FreakStudio: MLX90614 test start ")


i2c = I2C(0, scl=5, sda=4, freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print("START I2C SCANNER")
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print("i2c devices found:", len(devices_list))
for device in devices_list:
    if 0x5A <= device <= 0x5D:
        print("I2c hexadecimal address:", hex(device))
        mlx61xaddr = device


# 初始化 MLX90614
sensor14 = MLX90614(i2c, mlx61xaddr)
print("[MLX90614] Sensor initialized.")

# 初始化 MLX90615
sensor15 = MLX90615(i2c, mlx61xaddr)
print("[MLX90615] Sensor initialized.")

# ======================================== 主程序 ==============================================

# ================= MLX90614 测试 =================
print("\n--- Starting MLX90614 Realtime Test ---")
test_sensor_realtime(sensor14, "MLX90614", interval=1.0)

# ================= MLX90615 测试 =================
print("\n--- Starting MLX90615 Realtime Test ---")
test_sensor_realtime(sensor15, "MLX90615", interval=1.0)
