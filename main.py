# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/26
# @Author  : leezisheng
# @File    : main.py
# @Description : 测试BMP280驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
import micropython
from machine import I2C, Pin
from bmp280 import BMP280

# ======================================== 全局变量 ============================================
# BMP280 芯片 ID 期望值（0x60 表示 BMP280）
BMP280_EXPECTED_ID = micropython.const(0x60)
# 芯片 ID 寄存器地址
REG_CHIP_ID = micropython.const(0xD0)
# BMP280 可能的 I2C 地址列表
BMP280_ADDRS = (0x76, 0x77)
# 上次打印时间戳
last_print_time = 0
# 打印间隔（ms）
print_interval = 2000

# ======================================== 功能函数 ============================================
def print_raw_data():
    """打印原始 ADC 数据（低频，自动执行）"""
    # 读取原始温度和气压 ADC 值
    raw_temp, raw_press = sensor.read_raw()
    print("Raw temp: %d, Raw press: %d" % (raw_temp, raw_press))

def test_reset():
    """软复位传感器（模式切换，注释调用，可 REPL 手动触发）"""
    # 发送软复位命令，传感器重启后需重新初始化
    sensor.reset()
    print("Sensor reset done")

def test_boundary_and_exception():
    """边界与异常参数测试（初始化后调用一次）"""
    # 异常参数：addr 超出合法范围
    try:
        BMP280(i2c, addr=0xFF)
        print("ERROR: should have raised ValueError")
    except ValueError as e:
        print("Expected ValueError (addr out of range): %s" % str(e))
    # 异常参数：addr 类型错误
    try:
        BMP280(i2c, addr="bad")
        print("ERROR: should have raised ValueError")
    except ValueError as e:
        print("Expected ValueError (addr wrong type): %s" % str(e))
    # 异常参数：i2c 非法对象
    try:
        BMP280("not_i2c")
        print("ERROR: should have raised ValueError")
    except ValueError as e:
        print("Expected ValueError (invalid i2c): %s" % str(e))
    # 边界参数：addr 最大合法值 0x7F
    try:
        tmp = BMP280(i2c, addr=0x7F)
        print("Boundary addr=0x7F accepted")
    except Exception as e:
        print("Boundary addr=0x7F raised: %s" % str(e))

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 等待硬件上电稳定
time.sleep(3)
print("FreakStudio: Testing BMP280 driver")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 扫描 I2C 总线
print("START I2C SCANNER")
devices_list = i2c.scan()
# 若总线为空则直接抛出异常终止程序
if len(devices_list) == 0:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %d" % len(devices_list))

# 遍历设备列表，查找 BMP280 地址
sensor_addr = None
for device in devices_list:
    print("I2C hexadecimal address: %s" % hex(device))
    if device in BMP280_ADDRS:
        sensor_addr = device
# 未找到目标地址则抛出异常
if sensor_addr is None:
    raise RuntimeError("Device not found at expected address")
print("BMP280 found at address: %s" % hex(sensor_addr))

# 读取芯片 ID 寄存器验证设备型号
_id_buf = bytearray(1)
i2c.readfrom_mem_into(sensor_addr, REG_CHIP_ID, _id_buf)
if _id_buf[0] == BMP280_EXPECTED_ID:
    print("Device found: chip_id=0x%02X" % _id_buf[0])
else:
    print("Device not found: unexpected chip_id=0x%02X" % _id_buf[0])

# 实例化 BMP280 驱动，开启调试日志
sensor = BMP280(i2c, addr=sensor_addr, debug=True)

# 执行边界与异常参数测试
test_boundary_and_exception()

# 记录初始时间戳
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        # 每隔 print_interval ms 执行一次低频数据采集
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取补偿后温度
            temp = sensor.get_temp()
            print("Temperature: %.2f C" % temp)
            # 读取补偿后气压
            press = sensor.get_pressure()
            print("Pressure: %.2f Pa" % press)
            # 读取原始 ADC 值
            print_raw_data()
            # 更新时间戳
            last_print_time = current_time
        # test_reset()    # 软复位，注释默认执行，可 REPL 手动触发
        # 主循环节拍
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 将传感器置于睡眠模式
    sensor.deinit()
    # 释放驱动对象
    del sensor
    print("Program exited")
