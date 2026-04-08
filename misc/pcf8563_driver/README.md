# PCF8563 MicroPython Driver

# PCF8563 MicroPython Driver

## 目录

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

`pcf8563_driver` 是一款针对 **PCF8563 实时时钟（RTC）芯片** 开发的 MicroPython 驱动库，隶属于 GraftSense-Drivers-MicroPython 生态。它提供了简洁易用的 API，帮助开发者在 MicroPython 环境下快速实现时间读写、闹钟配置等核心功能，适用于各类需要精准时间记录的嵌入式项目。

---

## 主要功能

- 初始化 PCF8563 芯片，建立 I2C 通信
- 读取 / 设置当前日期与时间（年、月、日、时、分、秒）
- 配置闹钟功能，支持分钟 / 小时 / 日 / 星期匹配触发
- 控制时钟输出频率（CLKOUT），适配不同低功耗场景
- 检测 / 清除定时器中断、闹钟中断标志位
- 兼容主流 MicroPython 固件与硬件平台

---

## 硬件要求

- **开发板**：支持 MicroPython 的开发板（如 ESP32、ESP8266、RP2040、STM32 等）
- **RTC 模块**：PCF8563 实时时钟模块（I2C 接口，默认地址 `0x51`）
- **连接方式**：通过 I2C 总线连接开发板与 PCF8563（SDA、SCL 引脚对应连接）
- **供电**：3.3V 直流供电（推荐搭配 CR2032 电池实现掉电时间保持）

---

## 文件说明

## 软件设计核心思想

1. **I2C 通信封装**：底层基于 MicroPython `machine.I2C` 实现，屏蔽寄存器读写细节，对外提供高可读性的时间 / 闹钟 API。
2. **无固件依赖**：设计上不依赖特定固件（如 ulab、lvgl），支持所有标准 MicroPython 环境，兼容性极强。
3. **轻量高效**：代码精简，内存占用低，适配资源受限的嵌入式设备。
4. **易扩展**：模块化设计，便于后续新增功能（如定时器、中断优先级配置）。

---

## 使用说明

### 导入驱动

将 `pcf8563.py` 上传至开发板文件系统，在代码中导入：

```python
from pcf8563 import PCF8563
from machine import I2C, Pin
```

### 初始化 I2C 与 RTC

根据开发板引脚定义，初始化 I2C 总线，再创建 PCF8563 实例：

```python
# 以 ESP32 为例，SDA=21, SCL=22
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
rtc = PCF8563(i2c)
```

### 基础操作

- **设置时间**：`rtc.datetime((年, 月, 日, 星期, 时, 分, 秒))`
- **读取时间**：`rtc.datetime()` → 返回 (年，月，日，星期，时，分，秒)
- **设置闹钟**：`rtc.set_alarm(时, 分)` 或 `rtc.set_alarm(日, 时, 分, 星期)`
- **启用闹钟中断**：`rtc.enable_alarm_interrupt()`

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午8:00
# @Author  : hogeiha
# @File    : main.py
# @Description : PCF8563实时时钟模块完整使用示例，包含时间读写、时钟输出配置、闹钟功能等核心操作

# ======================================== 导入相关模块 ========================================

from machine import SoftI2C, Pin
import time
import pcf8563  # 导入PCF8563 RTC模块驱动

# ======================================== 全局变量 ============================================

# SCL引脚编号
I2C_SCL_PIN = 5  
# SDA引脚编号
I2C_SDA_PIN = 4  
# I2C通信频率
I2C_FREQ = 400000  
# PCF8563默认I2C地址
TARGET_RTC_ADDR = 0x51  

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: Initialize PCF8563 RTC module")

# 初始化SoftI2C
i2c_bus = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 执行I2C设备扫描
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 3. 检查扫描结果是否为空
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 4. 遍历地址列表匹配目标RTC地址
rtc = None  # 初始化rtc变量
for device in devices_list:
    if device == TARGET_RTC_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            rtc = pcf8563.PCF8563(i2c_bus)
            print("Target RTC (PCF8563) initialization successful")
            break
        except Exception as e:
            print(f"RTC Initialization failed: {e}")
            continue
else:
    # 遍历结束未找到目标地址则抛出异常
    raise Exception("No PCF8563 RTC module found at I2C address 0x51")

# ========================================  主程序  ============================================
print("\n=== 2. Basic time operations ===")

# 同步系统时间到 RTC 模块
print("Synchronize system time to RTC...")
rtc.write_now()
time.sleep(0.1)

# 读取完整时间
dt = rtc.datetime()
print(f"Complete time tuple: {dt} → Format: 20{dt[0]} year {dt[1]} month {dt[2]} day Week {dt[3]} {dt[4]}:{dt[5]}:{dt[6]}")

# 单独读取各时间字段
print(f"Read separately - Year: {rtc.year()} | Month: {rtc.month()} | Date: {rtc.date()}")
print(f"Read separately - Hours: {rtc.hours()} | Minutes: {rtc.minutes()} | Seconds: {rtc.seconds()} | Weekday: {rtc.day()}")

# 手动修改指定时间字段
print("\nModify time manually: Set hours to 10, minutes to 30...")
rtc.write_all(hours=10, minutes=30)
print(f"Time after modification: {rtc.hours()}:{rtc.minutes()} (Expected 10:30)")

# 设置完整的自定义时间
custom_dt = (25, 12, 25, 4, 18, 0, 0)  # 2025年12月25日 周四 18:00:00
print(f"\nSet complete time to: 20{custom_dt[0]} year {custom_dt[1]} month {custom_dt[2]} day {custom_dt[4]}:{custom_dt[5]}")
rtc.set_datetime(custom_dt)
print(f"Verify setting result: {rtc.datetime()}")

# 时钟输出频率配置
print("\n=== 3. Clock output configuration ===")
print("Configure CLKOUT to output 1Hz square wave...")
rtc.set_clk_out_frequency(pcf8563.CLOCK_CLK_OUT_FREQ_1_HZ)

# 闹钟功能操作
print("\n=== 4. Alarm function operations ===")
rtc.clear_alarm()
print("Clear existing alarm configuration completed")

# 设置每日闹钟
print("Set daily alarm: Trigger at 10:30...")
rtc.set_daily_alarm(hours=10, minutes=30, date=None, weekday=None)

# 启用闹钟中断
print("Enable alarm interrupt...")
rtc.enable_alarm_interrupt()
print(f"Is alarm interrupt enabled: {rtc.check_for_alarm_interrupt()} (Expected True)")

# 模拟等待闹钟触发
print("\nWaiting for alarm trigger (Simulate 5 seconds, modify time to trigger alarm)...")
for i in range(5):
    time.sleep(1)
    if rtc.check_if_alarm_on():
        print(f"Second {i + 1}: Alarm triggered!")
        rtc.turn_alarm_off()
        break
    else:
        print(f"Second {i + 1}: Alarm not triggered")

# 禁用闹钟中断
print("\nDisable alarm interrupt...")
rtc.disable_alarm_interrupt()
print(f"Is alarm interrupt enabled: {rtc.check_for_alarm_interrupt()} (Expected False)")

# 清除所有闹钟配置
print("Clear all alarm configurations...")
rtc.clear_alarm()

# 循环读取实时时间
print("\n=== 5. Read real-time time in loop (Press Ctrl+C to stop) ===")
try:
    while True:
        current_dt = rtc.datetime()
        print(
            f"\rReal-time time: 20{current_dt[0]} year {current_dt[1]} month {current_dt[2]} day Week {current_dt[3]} {current_dt[4]:02d}:{current_dt[5]:02d}:{current_dt[6]:02d}",
            end="",
        )
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStop loop, example ended")

```

## 注意事项

1. **I2C 地址**：PCF8563 默认 I2C 地址为 `0x51`，若硬件有修改需在初始化时传入 `address` 参数。
2. **电池备份**：需连接备用电池（如 CR2032），否则开发板断电后时间会重置。
3. **时间格式**：年份范围为 `2000-2099`，星期取值为 `1-7`（1 = 周一，7 = 周日）。
4. **中断处理**：闹钟中断需额外配置 GPIO 中断引脚，具体逻辑需开发者自行实现。
5. **固件兼容**：已验证支持标准 MicroPython 固件，若使用定制固件需确保 `machine.I2C` 接口可用。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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
