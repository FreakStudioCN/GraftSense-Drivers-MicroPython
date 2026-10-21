# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06
# @Author  : Nelio Goncalves Godoi
# @File    : main.py
# @Description : 测试SI1145紫外线/可见光/红外光/接近度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
import micropython
from machine import Pin, SoftI2C
from si1145 import (
    SI1145,
    SI1145_ADDR,
    SI1145_REG_PARTID,
    SI1145_PSALS_PAUSE,
    SI1145_PSALS_AUTO,
    SI1145_PS_FORCE,
    SI1145_ALS_FORCE,
    SI1145_PSALS_FORCE,
    SI1145_RESET,
    SI1145_REG_COMMAND,
)

# ======================================== 全局变量 ============================================

# I2C 引脚与频率配置
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# SI1145 设备可能的 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x60, 0x74]

# 设备 ID 寄存器与期望值（SI1145 PART_ID = 0x45）
DEVICE_ID_REG = SI1145_REG_PARTID
DEVICE_ID_EXPECTED = 0x45

# 打印间隔（ms）
last_print_time = 0
print_interval = 2000

# ======================================== 功能函数 ============================================

def print_realtime_data():
    """打印实时高频数据（高频，默认注释调用，可REPL手动调用）"""
    # 读取四路高频数据并打印
    print("UV index: %.2f" % sensor.read_uv)
    print("Visible: %d" % sensor.read_visible)
    print("IR: %d" % sensor.read_ir)
    print("Proximity: %d" % sensor.read_prox)


def switch_to_pause_mode():
    """切换到暂停测量模式（模式切换，默认注释调用，可REPL手动触发）"""
    # 写入 PSALS_PAUSE 命令暂停自动测量
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_PAUSE)
    print("Sensor switched to PSALS pause mode")


def switch_to_auto_mode():
    """切换回自动连续测量模式（模式切换，默认注释调用，可REPL手动触发）"""
    # 写入 PSALS_AUTO 命令恢复自动测量
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_AUTO)
    print("Sensor switched to PSALS auto mode")


def force_single_measurement():
    """触发一次强制单次 PS+ALS 测量（批量操作，可REPL一键调用）"""
    # 发送强制单次测量命令
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_FORCE)
    # 等待测量完成
    time.sleep_ms(50)
    print("Forced single measurement done")
    print("UV: %.2f, Visible: %d, IR: %d, Prox: %d" % (
        sensor.read_uv, sensor.read_visible, sensor.read_ir, sensor.read_prox))


def reset_sensor():
    """软件复位传感器（批量操作，可REPL一键调用）"""
    # 发送复位命令并重新加载校准
    sensor._reset()
    sensor._load_calibration()
    print("Sensor reset and recalibrated")


def test_boundary_address():
    """边界参数场景：使用合法地址边界值实例化（可REPL手动调用）"""
    # SI1145 地址固定为 0x60，测试默认地址作为边界
    try:
        tmp = SI1145(i2c=i2c_bus, addr=0x60)
        print("Boundary address 0x60 init ok")
        del tmp
    except Exception as e:
        print("Boundary address init failed: %s" % str(e))


def test_invalid_args():
    """异常参数场景：传入非法 i2c 参数，验证 ValueError 抛出（可REPL手动调用）"""
    # 传 None 应触发 ValueError
    try:
        SI1145(i2c=None)
        print("Invalid arg test failed: no exception raised")
    except ValueError as e:
        print("Invalid arg test passed: ValueError caught - %s" % str(e))
    except Exception as e:
        print("Invalid arg test got unexpected exception: %s" % str(e))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时，等待外设稳定
time.sleep(3)
print("FreakStudio: Using SI1145 UV/Visible/IR/Proximity sensor ...")

# 初始化软件 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
print("START I2C SCANNER")
devices_list = i2c_bus.scan()

# 若总线无设备则报错
if len(devices_list) == 0:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，匹配目标地址列表
sensor = None
matched_addr = None
for device in devices_list:
    print("I2C address: %s" % hex(device))
    if device in TARGET_SENSOR_ADDRS:
        matched_addr = device

# 未找到任何目标地址则报错
if matched_addr is None:
    raise RuntimeError("Device not found at expected address")

# 读取 PART_ID 寄存器并与期望值比对（SI1145 复位前可能返回 0x00，仅作参考）
part_id = i2c_bus.readfrom_mem(matched_addr, DEVICE_ID_REG, 1)[0]
if part_id == DEVICE_ID_EXPECTED:
    print("Device found: SI1145 PART_ID=0x%02X at %s" % (part_id, hex(matched_addr)))
else:
    print("PART_ID=0x%02X (expected 0x%02X), attempting init anyway..." % (part_id, DEVICE_ID_EXPECTED))

# 实例化 SI1145 传感器（构造内部已自动复位+加载校准）
sensor = SI1145(i2c=i2c_bus, addr=matched_addr)
print("SI1145 initialization successful")

# 记录首次打印时间
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 低频核心数据采集：每 print_interval 毫秒打印一次
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取紫外线指数
            uv = sensor.read_uv
            # 读取可见光强度
            vis = sensor.read_visible
            # 读取红外光强度
            ir = sensor.read_ir
            # 读取接近度
            prox = sensor.read_prox
            print("UV: %.2f | Visible: %d | IR: %d | Prox: %d" % (uv, vis, ir, prox))
            last_print_time = current_time

        # 高频函数，注释默认执行，可REPL手动调用
        # print_realtime_data()
        # 模式切换，注释默认执行，可REPL手动触发
        # switch_to_pause_mode()
        # switch_to_auto_mode()
        # 批量操作，可REPL一键调用
        # force_single_measurement()
        # reset_sensor()
        # 边界参数场景，可REPL手动调用
        # test_boundary_address()
        # 异常参数场景，可REPL手动调用
        # test_invalid_args()

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # SI1145 驱动未提供 close/deinit，发送复位命令使设备进入低功耗待机
    try:
        sensor._write8(SI1145_REG_COMMAND, SI1145_RESET)
    except Exception:
        pass
    del sensor
    print("Program exited")
