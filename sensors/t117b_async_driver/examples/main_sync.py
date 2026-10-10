# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/26 12:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试 T117B 温度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
from t117b import T117
import time

# ======================================== 全局变量 ============================================
# T117B 目标 I2C 地址（ADDR 引脚接 VDD）
DEVICE_ADDR    = [0x40,0x41,0x42,0x43]
# ROM ID 寄存器基地址（用于设备识别）
REG_ROM_ID     = 0x18
# 打印间隔（毫秒）
PRINT_INTERVAL = 500
# 报警高温阈值（℃）
ALERT_TH       = 30.0
# 报警低温阈值（℃）
ALERT_TL       = 10.0

# ======================================== 功能函数 ============================================
def scan_i2c(i2c: I2C) -> int:
    """扫描 I2C 总线，返回目标设备地址"""
    # 扫描总线上所有设备
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("I2C devices found: %s" % [hex(d) for d in devices])
    # 查找目标地址
    for addr in devices:
        if addr in DEVICE_ADDR:
            print("Target device found at 0x%02X" % addr)
            return addr
    raise RuntimeError("Device not found at expected address 0x%02X" % DEVICE_ADDR)


def read_rom_id(i2c: I2C, addr: int) -> None:
    """读取 ROM ID 寄存器并打印（T117B 无标准 WHO_AM_I，仅打印供参考）"""
    try:
        rom_id = i2c.readfrom_mem(addr, REG_ROM_ID, 4)
        print("ROM ID: %s" % [hex(b) for b in rom_id])
    except OSError as e:
        print("ROM ID read failed: %s" % str(e))


def test_basic_read(sensor: T117) -> None:
    """测试基本温度读取"""
    temp = sensor.get_temp()
    status = sensor.get_status()
    print("Temperature: %s C  Status: %s" % (temp, status))


def test_boundary_params(sensor: T117) -> None:
    """测试边界参数：极限阈值配置"""
    # 极限高温阈值 130℃，极限低温阈值 -100℃
    sensor.set_alert_thresholds(130.0, -100.0)
    print("Boundary thresholds set: TH=130.0, TL=-100.0")
    # 恢复正常阈值
    sensor.set_alert_thresholds(ALERT_TH, ALERT_TL)
    print("Thresholds restored: TH=%s, TL=%s" % (ALERT_TH, ALERT_TL))


def test_invalid_params(sensor: T117) -> None:
    """测试异常参数：验证 ValueError 是否正确抛出"""
    # 测试 th <= tl 的非法阈值
    try:
        sensor.set_alert_thresholds(10.0, 30.0)
        print("ERROR: Expected ValueError not raised")
    except ValueError as e:
        print("ValueError raised as expected: %s" % str(e))
    # 测试非法 avg 值
    try:
        sensor.set_avg(99)
        print("ERROR: Expected ValueError not raised")
    except ValueError as e:
        print("ValueError raised as expected: %s" % str(e))
    # 测试非法 mps 值
    try:
        sensor.set_mps(8)
        print("ERROR: Expected ValueError not raised")
    except ValueError as e:
        print("ValueError raised as expected: %s" % str(e))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Using T117B temperature sensor ...")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

# 扫描并验证设备
driver_addr=scan_i2c(i2c)
read_rom_id(i2c, driver_addr)

# 实例化传感器驱动
sensor = T117(i2c=i2c, addr=driver_addr)

# 配置报警：高温超过 ALERT_TH 或低温低于 ALERT_TL 时触发
sensor.enable_alerts(th_temp=ALERT_TH, tl_temp=ALERT_TL,
                     mps=T117.MPS_2_1, avg=T117.AVG_8)
print("Alert configured: TH=%s C, TL=%s C" % (ALERT_TH, ALERT_TL))

# 运行参数校验测试（仅初始化时执行一次）
test_boundary_params(sensor)
test_invalid_params(sensor)

# 记录上次打印时间
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        # 按打印间隔读取温度和报警状态
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            test_basic_read(sensor)
            last_print_time = current_time
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
