# AS7341 Driver for MicroPython

# AS7341 Driver for MicroPython

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

AS7341 Driver 是一款面向 **MicroPython** 环境的光谱传感器驱动库，隶属于 `GraftSense-Drivers-MicroPython` 项目。该库由 FreakStudio 开发，封装了 AS7341 传感器的底层通信与控制逻辑，帮助开发者快速在 MicroPython 设备上实现多波段光谱数据采集，适用于环境光监测、颜色分析等场景。

## 主要功能

- 支持 AS7341 传感器的 I2C 通信初始化与基础配置
- 提供多波段光谱数据读取接口（F1-F8 通道）
- 可配置传感器增益、测量模式等核心工作参数
- 封装寄存器操作细节，降低开发者使用门槛
- 兼容主流 MicroPython 开发板，无特殊固件依赖

## 硬件要求

- **传感器**：AS7341 光谱传感器
- **开发板**：支持 MicroPython 的开发板（如 ESP32、Raspberry Pi Pico、ESP8266 等）
- **通信接口**：I2C 接口（需将传感器 SDA/SCL 引脚连接至开发板对应 I2C 引脚）
- **供电**：3.3V 直流供电（禁止直接使用 5V 供电，避免传感器损坏）

## 文件说明

## 软件设计核心思想

- **模块化封装**：将 AS7341 寄存器操作、I2C 通信等底层逻辑封装为独立函数，降低代码耦合度
- **易用性优先**：提供简洁的上层 API，开发者无需深入了解传感器寄存器细节即可快速完成开发
- **高兼容性**：遵循 MicroPython 通用规范，支持多种芯片平台与固件版本（无特殊固件依赖）
- **可扩展性**：预留功能扩展接口，便于后续添加新的传感器配置或数据处理能力

## 使用说明

1. **文件上传**：将 `code/as7341.py` 文件上传至 MicroPython 设备文件系统（可通过 mpremote、Thonny 等工具完成）
2. **模块导入**：在项目代码中通过 `import as7341` 导入驱动模块
3. **I2C 初始化**：根据开发板引脚定义，初始化 I2C 总线
4. **实例创建**：传入 I2C 对象，创建 AS7341 传感器实例
5. **配置与读取**：调用实例方法配置传感器参数，读取光谱数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午9:00
# @Author  : hogeiha
# @File    : main.py
# @Description : Raspberry Pi Pico驱动AS7341光谱传感器 配置参数 读取光谱数据 控制LED和GPIO 配置中断

# ======================================== 导入相关模块 =========================================

import sys
import time
from machine import I2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def init_i2c():
    """Initialize I2C bus (adapted for RP2040, modify pins for other boards)"""
    try:
        # RP2040: I2C0 (SDA=4, SCL=5), frequency 100kHz
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        detected_devices = [hex(addr) for addr in i2c.scan()]
        print(f"I2C initialization successful, detected device addresses: {', '.join(detected_devices)}")
        if "0x39" not in detected_devices:
            print("Warning: AS7341 sensor not detected (default address 0x39)")
        return i2c
    except Exception as e:
        print(f"I2C initialization failed: {e}")
        return None


def print_separator(title):
    """Print separator to improve output readability"""
    print("
" + "=" * 70)
    print(f"=== {title}")
    print("=" * 70)


def safe_execute(func, *args, desc="operation"):
    """Safely execute function and catch exceptions"""
    try:
        result = func(*args)
        return result, True
    except Exception as e:
        print(f"  Operation {desc} failed: {e}")
        return None, False


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: AS7341 spectral sensor configuration and measurement demonstration on Raspberry Pi Pico")

# Initialize I2C bus
i2c = init_i2c()
if not i2c:
    sys.exit(1)

# Import AS7341 driver and create sensor object
from as7341 import *

sensor = AS7341(i2c)

# Check sensor connection status
if not sensor.isconnected():
    print("Failed to connect to AS7341 sensor, program exited")
    sys.exit(1)
print("AS7341 sensor initialized successfully!")

# ========================================  主程序  ============================================

# 1. Basic configuration demonstration (integration time, gain, measurement mode)
print_separator("1. Basic parameter configuration demonstration")

# 1.1 Set integration time (ASTEP + ATIME)
print("
  [Integration time configuration]")
# Set ASTEP (step): 599 → step time ≈(599+1)*2.78μs = 1.67ms
sensor.set_astep(599)
astep_time = sensor.get_astep_time()
print(f"    ASTEP set value: 599 → step time: {astep_time:.3f} ms")

# Set ATIME (integration steps): 29 → total integration time ≈30*1.67ms = 50ms
sensor.set_atime(29)
int_time = sensor.get_integration_time()
overflow_count = sensor.get_overflow_count()
print(f"    ATIME set value: 29 → total integration time: {int_time:.2f} ms")
print(f"    Maximum count value: {overflow_count}")

# 1.2 Set gain (AGAIN)
print("
  [Gain configuration]")
# Method 1: Set by gain code (code 4 → gain 8x)
sensor.set_again(4)
gain_code = sensor.get_again()
gain_factor = sensor.get_again_factor()
print(f"    Gain code set to 4 → actual gain code: {gain_code}, gain factor: {gain_factor}x")

# Method 2: Set by gain factor (auto convert to corresponding code)
sensor.set_again_factor(16)
gain_code2 = sensor.get_again()
gain_factor2 = sensor.get_again_factor()
print(f"    Gain factor set to 16 → actual gain code: {gain_code2}, gain factor: {gain_factor2}x")

# 1.3 Set measurement mode (SPM single pulse mode)
sensor.set_measure_mode(AS7341_MODE_SPM)
print(f"
  Measurement mode set to SPM (single pulse mode)")
time.sleep(1)

# 2. Spectral measurement demonstration (all preset channel maps)
print_separator("2. Spectral measurement demonstration (all channels)")
# Define channel map description
channel_maps = {
    "F1F4CN": "F1(405-425nm), F2(435-455nm), F3(470-490nm), F4(505-525nm), CLEAR, NIR",
    "F5F8CN": "F5(545-565nm), F6(580-600nm), F7(620-640nm), F8(670-690nm), CLEAR, NIR",
    "F2F7": "F2(435-455nm), F3(470-490nm), F4(505-525nm), F5(545-565nm), F6(580-600nm), F7(620-640nm)",
    "F3F8": "F3(470-490nm), F4(505-525nm), F5(545-565nm), F6(580-600nm), F7(620-640nm), F8(670-690nm)",
}

# Traverse all preset channel maps for measurement
for map_name, desc in channel_maps.items():
    print(f"
  Measurement channel: {map_name} → {desc}")
    # Start measurement (specify channel map)
    sensor.start_measure(map_name)
    # Get spectral data
    data, success = safe_execute(sensor.get_spectral_data, desc=f"read {map_name} data")
    if success and data:
        # Format output according to different channel maps
        if map_name == "F1F4CN":
            f1, f2, f3, f4, clr, nir = data
            print(f"    F1: {f1:6d} | F2: {f2:6d} | F3: {f3:6d} | F4: {f4:6d} | CLEAR: {clr:6d} | NIR: {nir:6d}")
        elif map_name == "F5F8CN":
            f5, f6, f7, f8, clr, nir = data
            print(f"    F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d} | F8: {f8:6d} | CLEAR: {clr:6d} | NIR: {nir:6d}")
        elif map_name == "F2F7":
            f2, f3, f4, f5, f6, f7 = data
            print(f"    F2: {f2:6d} | F3: {f3:6d} | F4: {f4:6d} | F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d}")
        elif map_name == "F3F8":
            f3, f4, f5, f6, f7, f8 = data
            print(f"    F3: {f3:6d} | F4: {f4:6d} | F5: {f5:6d} | F6: {f6:6d} | F7: {f7:6d} | F8: {f8:6d}")
    time.sleep_ms(500)

# 3. Single channel data reading demonstration
print_separator("3. Single channel data reading demonstration")
# Switch to F1F4CN map first, then read single channel
sensor.start_measure("F1F4CN")
for ch in range(6):
    ch_data = sensor.get_channel_data(ch)
    ch_names = ["F1", "F2", "F3", "F4", "CLEAR", "NIR"]
    print(f"  Channel {ch} ({ch_names[ch]}): {ch_data}")

# 4. On-board LED control demonstration
print_separator("4. On-board LED control demonstration")
# Set LED current (4mA ~ 20mA, even numbers only)
led_currents = [4, 8, 12, 16, 20]
for curr in led_currents:
    sensor.set_led_current(curr)
    print(f"  Set LED current: {curr} mA (on for 2 seconds)")
    time.sleep(2)

# Turn off LED
sensor.set_led_current(0)
print("  LED turned off")

# 6. GPIO pin control demonstration
print_separator("6. GPIO pin control demonstration")
# Configure GPIO as output mode (normal mode)
sensor.set_gpio_output(inverted=False)
print("  GPIO configured as output mode (normal) → LED on (if connected)")
time.sleep(1)

# Invert GPIO output
sensor.set_gpio_inverted(True)
print("  GPIO output inverted → LED off (if connected)")
time.sleep(1)

# Configure GPIO as input mode
sensor.set_gpio_input(enable=True)
gpio_value = sensor.get_gpio_value()
print(f"  GPIO configured as input mode → current GPIO value: {gpio_value} (True=high, False=low)")

# 7. Interrupt configuration demonstration
print_separator("7. Interrupt configuration demonstration")
# Set spectral interrupt thresholds (low threshold 1000, high threshold 10000)
sensor.set_thresholds(1000, 10000)
lo_th, hi_th = sensor.get_thresholds()
print(f"  Set spectral interrupt thresholds → low threshold: {lo_th}, high threshold: {hi_th}")

# Set interrupt persistence (trigger after 3 consecutive times exceeding threshold)
sensor.set_interrupt_persistence(3)
print(f"  Set interrupt persistence: 3")

# Enable spectral interrupt
sensor.set_spectral_interrupt(True)
print(f"  Enabled spectral interrupt")

# Check and clear interrupt
interrupt_status = sensor.check_interrupt()
print(f"  Current interrupt status: {interrupt_status}")
sensor.clear_interrupt()
print(f"  Cleared all interrupts")

# 8. Auto restart configuration demonstration (WTIME)
print_separator("8. Auto restart (WTIME) configuration demonstration")
# Set WTIME (auto restart interval)
sensor.set_wtime(99)  # 99 → interval ≈(99+1)*2.78ms = 278ms
sensor.set_wen(True)  # Enable auto restart
print(f"  Set WTIME=99 → auto restart interval ≈278ms, WEN enabled")

# Final operation
print_separator("9. Demonstration finished, turn off sensor")
# Disable sensor (power off)
sensor.disable()
print("  AS7341 sensor disabled, program finished")

```

## 注意事项

- 请根据开发板硬件设计，调整 I2C 初始化时的 SCL/SDA 引脚编号
- 确保传感器供电稳定，避免电压波动导致数据采集异常
- 本库无特殊固件依赖，兼容所有标准 MicroPython 固件版本
- 若通信失败，可检查 I2C 接线、传感器地址（AS7341 默认 I2C 地址通常为 `0x39`）

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
