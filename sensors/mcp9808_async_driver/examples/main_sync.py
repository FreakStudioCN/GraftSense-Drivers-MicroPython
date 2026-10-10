# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 14:37
# @Author  : Kai Fricke
# @File    : main.py
# @Description : 测试 MCP9808 温度传感器驱动的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C, Pin

from mcp9808 import MCP9808, REG_DEVIDE_ID, REG_MANUFACTURER_ID, TEMP_RESOLUTION_MAX

# ======================================== 全局变量 ============================================
# Raspberry Pi Pico / RP2040 接线示例：
#   MCP9808 VCC   -> 3V3
#   MCP9808 GND   -> GND
#   MCP9808 SCL   -> GP1
#   MCP9808 SDA   -> GP0
#   MCP9808 A0/A1/A2 -> GND（地址 0x18）
#   MCP9808 ALERT -> 可选，简单温度读取时不连接

# I2C 总线配置
I2C_BUS = 0
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
I2C_FREQ = 100_000

# MCP9808 地址
MCP9808_ADDR = 0x18

# 芯片 ID 验证期望值
_EXPECTED_MFR_ID = b"\x00T"
_EXPECTED_DEV_ID = b"\x04\x00"

# 温度打印间隔（ms）
PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: MCP9808 temperature sensor test")

# 初始化 I2C 总线
i2c = I2C(
    I2C_BUS,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)

# I2C 设备扫描
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_BUS)
print("I2C devices found:", [hex(addr) for addr in devices])

# 验证目标地址
if MCP9808_ADDR not in devices:
    raise RuntimeError("MCP9808 not found at address %s, check wiring" % hex(MCP9808_ADDR))

# 读取制造商 ID 寄存器
i2c.writeto(MCP9808_ADDR, bytes([REG_MANUFACTURER_ID]))
mfr_id = i2c.readfrom(MCP9808_ADDR, 2)
if mfr_id != _EXPECTED_MFR_ID:
    raise RuntimeError("Manufacturer ID mismatch: got %s, expected %s" % (mfr_id, _EXPECTED_MFR_ID))

# 读取设备 ID 寄存器
i2c.writeto(MCP9808_ADDR, bytes([REG_DEVIDE_ID]))
dev_id = i2c.readfrom(MCP9808_ADDR, 2)
if dev_id != _EXPECTED_DEV_ID:
    raise RuntimeError("Device ID mismatch: got %s, expected %s" % (dev_id, _EXPECTED_DEV_ID))

print("Device found: MCP9808 at %s (MFR=0x%02X%02X, DEV=0x%02X%02X)" % (hex(MCP9808_ADDR), mfr_id[0], mfr_id[1], dev_id[0], dev_id[1]))

# 实例化传感器
sensor = MCP9808(i2c=i2c, addr=MCP9808_ADDR)
sensor.set_resolution(TEMP_RESOLUTION_MAX)

# ========================================  主程序  ===========================================
try:
    while True:
        # 读取温度值
        temp_c = sensor.get_temp()
        print("Temperature: {:.4f} C".format(temp_c))

        # 以下为可选测试场景，取消注释即可运行：

        # --- 正常参数场景：切换分辨率 ---
        # sensor.set_resolution(TEMP_RESOLUTION_AVG)
        # print("Resolution changed to AVG (±0.125°C)")

        # --- 边界参数场景：设置报警阈值 ---
        # sensor.set_alert_boundary_temp(REG_TEMP_BOUNDARY_UPPER, 80.0)
        # sensor.set_alert_boundary_temp(REG_TEMP_BOUNDARY_CRITICAL, 100.0)
        # print("Alert boundaries set: upper=80°C, critical=100°C")
        # sensor.set_alert_mode(enable_alert=True,
        #                       output_mode=ALERT_OUTPUT_INTERRUPT,
        #                       polarity=ALERT_POLARITY_ALOW,
        #                       selector=ALERT_SELECT_ALL)

        # --- 异常参数场景：非法分辨率 ---
        # try:
        #     sensor.set_resolution(99)
        # except ValueError as e:
        #     print("Expected error caught: %s" % e)

        time.sleep(1)

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
