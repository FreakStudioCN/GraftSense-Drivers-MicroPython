# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 TCA9554 8位 I2C GPIO 扩展器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from tca9554 import TCA9554, TCA9554_INPUT, TCA9554_OUTPUT, TCA9554_HIGH, TCA9554_LOW

# ======================================== 全局变量 ============================================

# 请替换为你的实际引脚配置
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
TCA9554_ADDR = 0x20

# TCA9554 无标准芯片 ID 寄存器，使用地址扫描验证
TCA9554_EXPECTED_ADDR = TCA9554_ADDR

# 打印间隔（ms）
PRINT_INTERVAL = 2000

# 上次打印时间戳
last_print_time = 0

# ======================================== 功能函数 ============================================


def demo_output_mode(io_expander):
    """
    演示输出模式：配置引脚为输出，写入高低电平（低频，自动执行）
    """
    print("")
    print("=== Demo: Output Mode ===")
    # 配置引脚0为输出模式
    io_expander.pin_mode(0, TCA9554_OUTPUT)
    print("Pin 0 configured as OUTPUT")
    # 写入高电平
    io_expander.write(0, TCA9554_HIGH)
    # 读取输出寄存器验证写入值
    out_val = io_expander.read_output8()
    print("Output register after writing HIGH to pin 0: 0x%02X" % out_val)
    # 延时等待，便于观察
    time.sleep(0.5)
    # 写入低电平
    io_expander.write(0, TCA9554_LOW)
    out_val = io_expander.read_output8()
    print("Output register after writing LOW to pin 0: 0x%02X" % out_val)


def demo_input_mode(io_expander):
    """
    演示输入模式：配置引脚为输入，读取引脚电平（低频，自动执行）
    """
    print("")
    print("=== Demo: Input Mode ===")
    # 配置引脚0为输入模式
    io_expander.pin_mode(0, TCA9554_INPUT)
    print("Pin 0 configured as INPUT")
    # 读取全部8个引脚的输入寄存器
    in_val = io_expander.read_input8()
    print("Input register: 0x%02X" % in_val)
    # 读取单个引脚的电平
    pin_val = io_expander.read(0)
    print("Pin 0 level: %d" % pin_val)


def demo_polarity_mode(io_expander):
    """
    演示极性反转功能（模式切换，默认注释调用，可REPL手动触发）
    """
    print("")
    print("=== Demo: Polarity Inversion ===")
    # 反转引脚0的输入极性
    io_expander.set_polarity(0, True)
    print("Pin 0 polarity inverted")
    # 读取输入验证极性反转效果
    in_val = io_expander.read(0)
    print("Pin 0 level after polarity inversion: %d" % in_val)
    # 恢复正常极性
    io_expander.set_polarity(0, False)
    print("Pin 0 polarity restored to normal")


def demo_port_operations(io_expander):
    """
    演示端口级批量操作（批量操作，封装为独立函数供REPL调用）
    """
    print("")
    print("=== Demo: Port-Level Operations ===")
    # 配置所有8个引脚为输出（0x00 = 全部输出）
    io_expander.pin_mode8(0x00)
    print("All pins configured as OUTPUT (mask=0x00)")
    # 批量写入端口数据（0x55 = 01010101）
    io_expander.write_port(0x55)
    out_val = io_expander.read_output8()
    print("Output register after write_port(0x55): 0x%02X" % out_val)
    # 配置所有8个引脚为输入（0xFF = 全部输入）
    io_expander.pin_mode8(0xFF)
    print("All pins configured as INPUT (mask=0xFF)")
    # 读取全部输入状态
    in_val = io_expander.read_input8()
    print("Input register: 0x%02X" % in_val)


# ======================================== 初始化配置 ==========================================

# 上电延时，等待硬件稳定
time.sleep(3)

print("FreakStudio: Testing TCA9554 8-bit I2C GPIO Expander Driver")
print("")

# 初始化 I2C 总线
print("Initializing I2C bus...")
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C bus initialized: SCL=%d, SDA=%d, freq=%d" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

# 检查目标设备是否在扫描列表中
if TCA9554_EXPECTED_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % TCA9554_EXPECTED_ADDR)
print("Device found at expected address: 0x%02X" % TCA9554_EXPECTED_ADDR)

# 实例化 TCA9554 驱动（I2C 实例外部注入）
print("Initializing TCA9554 driver...")
io_expander = TCA9554(i2c, address=TCA9554_ADDR)

# 验证设备连接（I2C 探测读取）
if io_expander.is_connected():
    print("TCA9554 connected and responding")
else:
    raise RuntimeError("TCA9554 not responding at address 0x%02X" % TCA9554_ADDR)

# ========================================  主程序  ===========================================

try:
    # 低频自动执行：基础演示
    demo_output_mode(io_expander)
    demo_input_mode(io_expander)

    # 模式切换：注释自动调用，可REPL手动触发
    # demo_polarity_mode(io_expander)

    # 批量操作：封装为独立函数，可REPL调用
    # demo_port_operations(io_expander)

    print("")
    print("Basic demo completed. Use REPL to call additional functions:")
    print("  demo_polarity_mode(io_expander)")
    print("  demo_port_operations(io_expander)")
    print("")

    # 主循环：周期性读取输入寄存器
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        # 按间隔打印输入状态
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取全部8个引脚的输入状态
            in_val = io_expander.read_input8()
            print("Input register: 0x%02X" % in_val)
            last_print_time = current_time
        # 短延时避免 CPU 占用过高
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放资源，所有引脚恢复输入模式
    io_expander.deinit()
    del io_expander
    print("Program exited")
