# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ES7210 音频 ADC I2C 控制驱动类的代码（冷生成，未硬件验证）
# @License : MIT

import time
from machine import I2C, Pin
from es7210 import ES7210, DEFAULT_ADDRESS

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# I2C 引脚配置（ESP32 默认引脚）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000
I2C_BUS_ID = 0

# I2S 引脚配置（ESP32 典型引脚，用于音频数据流）
I2S_BCK_PIN = 26
I2S_WS_PIN = 25
I2S_SD_PIN = 33
I2S_ID = 0

# 驱动实例（初始化配置区赋值）
device = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待设备就绪
time.sleep(3)
print("FreakStudio: Using ES7210 audio ADC I2C control driver ...")
print("NOTE: This driver is cold-generated and NOT hardware verified")

# 创建 I2C 总线实例
i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线，确认设备存在
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])
if DEFAULT_ADDRESS not in devices:
    raise RuntimeError("ES7210 not found at expected address 0x%02X" % DEFAULT_ADDRESS)
print("ES7210 found at I2C address 0x%02X" % DEFAULT_ADDRESS)

# 初始化 ES7210 驱动（仅 I2C 寄存器配置，不创建 I2S 对象）
device = ES7210(i2c, sample_rate=16000, bits_per_sample=16, mic_gain_db=24, tdm=False, debug=False)

# 执行通信自检（冷生成代码，结果未经验证）
try:
    device.self_test()
    print("ES7210 I2C self-test passed")
except RuntimeError as e:
    print("ES7210 I2C self-test failed: %s" % str(e))
    print("Continuing with configuration anyway (cold-generated code)")

print("ES7210 I2C configuration completed")
print("Audio I2S data stream should be set up separately with machine.I2S(mode=I2S.RX)")

# 注意：音频 I2S 数据接收需在应用层单独配置
# 以下为 I2S 配置示例（取消注释以启用音频数据流）
# try:
#     from machine import I2S
#     audio_in = I2S(
#         I2S_ID,
#         sck=Pin(I2S_BCK_PIN),
#         ws=Pin(I2S_WS_PIN),
#         sd=Pin(I2S_SD_PIN),
#         mode=I2S.RX,
#         bits=16,
#         format=I2S.STEREO,
#         rate=16000,
#         ibuf=4096,
#     )
#     print("I2S audio input initialized")
# except ImportError:
#     print("machine.I2S not available on this platform")

# ========================================  主程序  ===========================================

try:
    while True:
        # 主循环保持运行
        # 音频 I2S 数据通过独立的 machine.I2S 对象读取，不在本循环中处理
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if device is not None:
        device.deinit()
    device = None
    print("Program exited")
