# ds3231_driver - MicroPython DS3231 实时时钟驱动库

# ds3231_driver - MicroPython DS3231 实时时钟驱动库

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

`ds3231_driver` 是一个专为 **MicroPython** 环境设计的 **DS3231 高精度实时时钟（RTC）模块驱动库**，由 FreakStudio 开发维护。该库封装了 DS3231 的 I2C 通信协议与寄存器操作，提供简洁易用的 Python API，帮助开发者快速在嵌入式项目中实现时间获取、时间设置及温度监测等功能。

---

## 主要功能

- 支持通过 I2C 接口与 DS3231 模块通信
- 实现**时间设置**与**时间读取**功能（支持年 / 月 / 日 / 时 / 分 / 秒 / 星期格式）
- 支持读取 DS3231 内置温度传感器的温度数据
- 兼容多种运行 MicroPython 的硬件平台与固件版本
- 轻量级封装，资源占用低，适配嵌入式设备资源限制

---

## 硬件要求

- **DS3231 实时时钟模块**（需配备 3V 纽扣电池以保持掉电后时间记忆）
- 支持 MicroPython 的开发板（如 ESP32、ESP8266、Raspberry Pi Pico、STM32 等）
- 开发板需具备可用的 **I2C 接口**（SDA/SCL 引脚）
- 3.3V 供电（部分模块支持 5V，需注意电平匹配）

---

## 文件说明

## 软件设计核心思想

1. **轻量级封装**：仅封装 DS3231 核心功能，避免冗余代码，确保在资源受限的嵌入式设备上高效运行。
2. **I2C 抽象**：基于 MicroPython 标准 `machine.I2C` 接口实现通信，兼容不同硬件平台的 I2C 实现。
3. **寄存器映射**：将 DS3231 的时间、温度寄存器映射为 Python 可操作属性，降低底层寄存器操作复杂度。
4. **无依赖设计**：不依赖特定固件或第三方库（`fw: all`），支持所有兼容 MicroPython 的芯片（`chips: all`）。

---

## 使用说明

### 硬件连接

将 DS3231 模块与开发板的 I2C 引脚连接：

- DS3231 `SDA` → 开发板 I2C SDA 引脚
- DS3231 `SCL` → 开发板 I2C SCL 引脚
- DS3231 `VCC` → 3.3V 电源
- DS3231 `GND` → 开发板 GND

### 库安装

将 `code/ds3231maxim.py` 文件上传至开发板的文件系统（可通过 Thonny、mpremote 等工具完成）。

### 导入库

在 MicroPython 脚本中导入驱动：

```python
from ds3231maxim import DS3231
from machine import I2C, Pin
```

## 示例程序

以下示例展示了初始化 DS3231、设置时间、读取时间和温度的完整流程：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午6:00
# @Author  : octaprog7
# @File    : main.py
# @Description : DS3231实时时钟测试  设置并读取时间 读取温度状态等信息 配置闹钟并循环检测闹钟标志

# ======================================== 导入相关模块 =========================================

# 导入I2C和Pin模块用于硬件通信
from machine import I2C, Pin

# 导入DS3231驱动相关类
from ds3231maxim import DS3231, I2cAdapter

# 导入时间模块用于延时和获取本地时间
import time

# ======================================== 全局变量 ============================================

# 定义I2C引脚和频率常量
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000
# DS3231默认I2C地址
TARGET_SENSOR_ADDR = 0x68

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: DS3231 RTC Clock Test and Alarm Configuration")

# 初始化I2C总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
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
    clock = None
    for device in devices_list:
        if device == TARGET_SENSOR_ADDR:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 创建I2C适配器对象
                adaptor = I2cAdapter(i2c_bus)
                # 创建DS3231实时时钟对象
                clock = DS3231(adapter=adaptor)
                print("Target sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    if clock is None:
        raise Exception("No DS3231 found")

# ========================================  主程序  ============================================

# 获取当前本地时间
tr = time.localtime()
# 打印要设置的时间
print(f"set time to actual value: {tr}")
# 将本地时间设置到DS3231时钟
clock.set_time(tr)

# 打印提示信息，调用get_time方法
print("Call get_time() method")
# 读取DS3231当前时间
tr = clock.get_time()
# 打印读取到的本地时间
print(f"Local time: {tr}")

# 读取DS3231内部温度传感器数据
tmp = clock.get_temperature()
# 读取DS3231状态寄存器值
stat = clock.get_status()
# 读取DS3231控制寄存器值
ctrl = clock.get_control()
# 读取DS3231老化偏移值
ao = clock.get_aging_offset()
# 打印温度、状态、控制寄存器、老化偏移值
print(f"Temperature: {tmp}\tstatus: {hex(stat)}\tcontrol: {hex(ctrl)}\taging offset: {hex(ao)}")

# 打印提示信息，显示闹钟时间
print("Alarm times:")
# 读取并打印第一个闹钟（alarm 0）的配置
print("get_alarm(0):", clock.get_alarm(0))
# 读取并打印第二个闹钟（alarm 1）的配置
print("get_alarm(1):", clock.get_alarm(1))

# 定义闹钟时间元组（秒、分、时、日）
at = (00, 10, 11, 12)
# 设置闹钟匹配模式为0（每秒匹配，每分钟触发）
k = 0
# 打印提示信息，调用set_alarm方法
print(f"Call: set_alarm({at}, {k})")
# 配置第一个闹钟（alarm 0）的时间和匹配模式
clock.set_alarm(at, k, k)
# 读取并打印配置后的第一个闹钟信息
print(f"get_alarm({k}):", clock.get_alarm(k))
# 设置闹钟匹配模式为1
k = 1
# 配置第二个闹钟（alarm 1）的时间和匹配模式（时分匹配）
clock.set_alarm(at, k, k)
# 读取并打印配置后的第二个闹钟信息
print(f"get_alarm({k}):", clock.get_alarm(k))

# 打印提示信息，使用迭代器读取时间
print("Using iterator...")
# 循环迭代读取DS3231时间并检测闹钟标志
for ltime in clock:
    # 获取闹钟触发标志
    f = clock.get_alarm_flags()
    # 打印当前时间和闹钟标志
    print(f"Local time: {ltime}\talarm flags: {f}")
    # 延时1秒
    time.sleep_ms(1000)

```

## 注意事项

- **电池供电**：DS3231 需安装 3V 纽扣电池（如 CR2032），否则断电后时间会重置。
- **I2C 地址**：DS3231 默认 I2C 地址为 `0x68`，若存在地址冲突需检查硬件连接。
- **时间格式**：设置时间时需遵循 `(年, 月, 日, 星期, 时, 分, 秒)` 格式，星期取值为 1-7。
- **温度精度**：DS3231 内置温度传感器精度为 ±0.5℃，仅用于粗略温度监测。
- **电平兼容**：确保开发板与 DS3231 模块供电电平一致（推荐 3.3V），避免 5V 电平损坏模块。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：📧 **邮箱**：liqinghsui@freakstudio.cn💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源许可协议，完整协议内容如下：

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
