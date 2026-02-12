# GraftSense-基于 BH1750 芯片的光强度传感器模块（MicroPython）

# GraftSense-基于 BH1750 芯片的光强度传感器模块（MicroPython）

# GraftSense 基于 BH1750 的光强度传感器模块

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本模块是 FreakStudio GraftSense 基于 BH1750 的光强度传感器模块，通过 BH1750 芯片实现高精度环境光强度测量，支持 1~65535 lux 范围内的数字化光照数据采集，具备高精度、响应快速、易操作等优势，兼容 Grove 接口标准。适用于创客项目光照采集、智能家居亮度自动调节、设备显示屏调光控制等场景，为系统提供精准的环境光数据交互能力。

## 主要功能

1. 高精度光照强度测量：支持 1~65535 lux 量程，提供 0.5 lux/1 lux/4 lux 三种分辨率可选；
2. 灵活的 I2C 通信：支持标准 I2C 速率，通过拨码开关可配置 0x23/0x5C 两个 I2C 地址，避免总线冲突；
3. 多测量模式：支持连续测量、单次触发测量两种模式，适配不同采集场景；
4. 宽电压兼容：支持 3.3V/5V 供电，内置 DC-DC 转换和电源滤波电路，保证供电稳定；
5. 完整的 MicroPython 驱动：提供配置、重置、电源控制、数据读取等全功能 API，支持生成器模式持续采集。

## 硬件要求

### 核心接口

- I2C 通信接口：SDA（数据）、SCL（时钟），支持标准 I2C 通信速率，兼容 3.3V/5V 电平；
- 地址选择拨码开关：通过 ADDR 引脚拨码 0/1，可配置两个 I2C 地址（拨码 0→0x23、拨码 1→0x5C）；
- 电源接口：VCC（3.3V/5V 供电）、GND（接地）；
- 电源指示灯：直观显示模块供电状态。

### 电路要求

- 核心芯片：BH1750（实现 1~65535 lux 光强度数字化测量）；
- 供电电路：DC-DC 5V 转 3.3V（为 BH1750 提供稳定供电）；
- 辅助电路：电源滤波电路（滤除噪声）、MCU 接口电路（I2C 通信）。

### 模块布局要求

正面需包含 BH1750 芯片、ADDR 拨码开关、I2C 接口（SDA/SCL）、电源接口（GND/VCC）、电源指示灯，且接口清晰标注。

## 文件说明

| 文件名     | 功能说明                                                                        |
| ---------- | ------------------------------------------------------------------------------- |
| bh_1750.py | BH1750 传感器核心驱动文件，定义 BH1750 类，包含初始化、配置、数据读取等核心方法 |
| main.py    | 传感器使用示例文件，实现单次测量、连续测量、生成器模式三种光照采集方式          |

## 软件设计核心思想

核心设计围绕 **BH1750 类**展开（基于 MicroPython 实现），通过封装硬件操作细节，提供简洁易用的 API，核心设计思路如下：

### 1. 配置项常量化

将测量模式、分辨率、测量时间等硬件配置项定义为类常量，便于调用和维护：

| 类别     | 常量                                                                                        | 说明                                                            |
| -------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 测量模式 | MEASUREMENT_MODE_CONTINUOUSLY（1）<br>MEASUREMENT_MODE_ONE_TIME（2）                        | 连续测量模式 / 单次触发测量模式                                 |
| 分辨率   | RESOLUTION_HIGH（0）<br>RESOLUTION_HIGH_2（1）<br>RESOLUTION_LOW（2）                       | 高分辨率（1 lux）<br>高分辨率 2（0.5 lux）<br>低分辨率（4 lux） |
| 测量时间 | MEASUREMENT_TIME_DEFAULT（69）<br>MEASUREMENT_TIME_MIN（31）<br>MEASUREMENT_TIME_MAX（254） | 默认测量时间（69）<br>测量时间范围：31~254                      |

### 2. 核心属性封装

封装传感器关键状态属性，仅在初始化/配置时修改，保证数据一致性：

| 属性              | 类型 | 说明                                   |
| ----------------- | ---- | -------------------------------------- |
| _address          | int  | BH1750 的 I2C 设备地址（0x23 或 0x5C） |
| _i2c              | I2C  | 绑定的 I2C 接口实例，用于与传感器通信  |
| _measurement_mode | int  | 当前测量模式（连续/单次）              |
| _resolution       | int  | 当前分辨率模式（高/高 2/低）           |
| _measurement_time | int  | 当前测量时间（31~254）                 |

### 3. 功能方法模块化

将传感器操作拆分为独立方法，单一职责，便于扩展和调试：

| 方法         | 功能                             | 参数说明                                                                   | 返回值                                |
| ------------ | -------------------------------- | -------------------------------------------------------------------------- | ------------------------------------- |
| **init**     | 初始化 BH1750 传感器             | address: I2C 地址；i2c: I2C 实例                                           | 无                                    |
| configure    | 配置测量模式、分辨率和测量时间   | measurement_mode: 测量模式；resolution: 分辨率；measurement_time: 测量时间 | 无                                    |
| reset        | 重置传感器，清除光照数据寄存器   | 无                                                                         | 无                                    |
| power_on     | 开启传感器                       | 无                                                                         | 无                                    |
| power_off    | 关闭传感器                       | 无                                                                         | 无                                    |
| measurement  | 获取当前光照强度（lux）          | 无                                                                         | float，光照强度值（单位：lux）        |
| measurements | 生成器方法，持续获取光照强度数据 | 无                                                                         | generator，每次迭代返回当前光照强度值 |

## 使用说明

### 前置准备

1. 硬件接线：将模块 SDA 接主控 GPIO4、SCL 接 GPIO5，VCC 接 3.3V/5V，GND 接地；
2. 地址配置：根据 ADDR 拨码开关确定 I2C 地址（拨码 0→0x23，拨码 1→0x5C）；
3. 环境准备：确保主控设备已烧录 MicroPython 固件，且已将 bh_1750.py 文件上传至设备。

### 基本使用步骤

1. 初始化 I2C 总线，扫描并获取 BH1750 的 I2C 地址；
2. 创建 BH1750 传感器实例，传入 I2C 地址和 I2C 实例；
3. 调用 configure 方法配置测量模式、分辨率、测量时间；
4. 调用 measurement（单次/连续）或 measurements（生成器）方法读取光照数据。

## 示例程序

```python
from machine import I2C, Pin
import time
from bh_1750 import BH1750

# 初始化配置
time.sleep(3)
print("FreakStudio: test Light Intensity Sensor now")

# 初始化I2C总线（I2C0，SCL=5，SDA=4，100kHz）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描I2C设备，获取BH1750地址
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
    for device in devices_list:
        if 0x21 <= device <= 0x5E:
            print("I2c hexadecimal address:", hex(device))
            bh_addr = device

# 创建BH1750传感器实例
sensor = BH1750(bh_addr, i2c)

# --- 1. 单次测量模式 ---
print("one time measure")
sensor.configure(
    measurement_mode=BH1750.MEASUREMENT_MODE_ONE_TIME,
    resolution=BH1750.RESOLUTION_HIGH,
    measurement_time=69
)
for i in range(5):
    lux = sensor.measurement
    print("One-time lux =", lux)
    time.sleep(1)

time.sleep(2)

# --- 2. 连续测量模式 ---
print("\n>>> Continuous measurement mode <<<")
sensor.configure(
    measurement_mode=BH1750.MEASUREMENT_MODE_CONTINUOUSLY,
    resolution=BH1750.RESOLUTION_HIGH,
    measurement_time=69
)
for i in range(5):
    lux = sensor.measurement
    print("Continuous lux =", lux)
    time.sleep(1)

time.sleep(2)

# --- 3. 生成器模式（持续采集） ---
print("\n>>> Generator mode <<<")
gen = sensor.measurements()
for i in range(5):
    lux = next(gen)
    print("Generator lux =", lux)

print("\nTest finished.")
```

## 注意事项

1. I2C 地址匹配：ADDR 拨码 0 对应地址 0x23，拨码 1 对应 0x5C，代码中 address 参数需与拨码设置一致，否则通信失败；
2. 测量时间范围：测量时间必须在 31~254 之间，超出范围会触发 ValueError，时间越短响应越快但精度略有下降；
3. 分辨率选择：高分辨率 2（0.5 lux）精度最高，低分辨率（4 lux）响应最快，可根据场景平衡精度与速度；
4. 连续测量延时：连续模式下，生成器会自动根据测量时间计算采样延时，避免频繁读取导致数据未更新；
5. ISR 安全限制：I2C 操作不是 ISR-safe，禁止在中断服务程序中调用传感器方法；
6. 电源稳定性：测量时需保证电源稳定，避免电压波动导致光照值异常。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudio

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
