# GraftSense-基于 ADS1115 芯片的模数转换模块（MicroPython）

# GraftSense-基于 ADS1115 芯片的模数转换模块（MicroPython）

# GraftSense ADS1115 模数转换模块

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

本模块是 FreakStudio GraftSense ADS1115 模数转换模块，基于 ADS1115 芯片实现 16 位高精度 A/D 转换，支持 4 路差分或 8 路单端模拟信号采集，具备高分辨率、低功耗、多通道输入等优势，兼容 Grove 接口标准。适用于电子 DIY 传感器数据采集实验、精密测量演示、便携设备电压监测等场景，为系统提供高精度的模拟信号数字化交互能力。

## 主要功能

### 硬件功能

- 支持 I2C 通信接口（SDA/SCL），可通过短接点配置 0x48-0x4B 范围内的 I2C 设备地址
- 提供 4 路模拟输入通道（AIN0-AIN3），支持单端输入（0-3 通道）和差分输入（0-1、0-3、1-3、2-3 组合）
- 16 位高精度 A/D 转换，增益可调（2/3x-16x），采样率可调（8-860 SPS）
- 板载电源滤波电路和 DC-DC 5V 转 3.3V 电路，保障供电稳定性
- 电源指示灯直观显示模块供电状态

### 软件功能

- 基于 MicroPython 实现完整的 ADS1115 驱动类，支持单端/差分输入配置
- 提供增益、采样率灵活配置接口，支持比较器中断和连续转换模式
- 内置原始 ADC 值转电压值的计算方法，简化数据解析
- 支持滑动均值滤波，降低采集数据噪声干扰
- 提供 UART 数据帧传输功能，便于上位机解析数据

## 硬件要求

### 核心接口要求

- I2C 通信：需主控设备支持 I2C 协议，通信速率兼容标准 I2C 速率（模块默认 400KHz）
- 供电：3.3V/5V 直流电源，纹波小、稳定性高，避免电压波动影响采集精度
- 输入信号：模拟输入电压范围需匹配所选增益（2/3x 对应 ±6.144V，16x 对应 ±0.256V）

### 硬件连接要求

- I2C 总线：SDA/SCL 引脚需正确连接，模块已内置上拉电阻，无需额外配置
- ADC 输入：输入线尽量短，避免电磁干扰；差分输入需保证通道配对正确
- 地址配置：通过 J1、J2 短接点设置唯一 I2C 地址（0x48-0x4B），避免地址冲突

## 文件说明

| 文件名     | 功能说明                                                            |
| ---------- | ------------------------------------------------------------------- |
| ads1115.py | ADS1115 核心驱动文件，包含 ADS1115 类及所有寄存器配置、数据采集方法 |
| main.py    | 高精度 ADC 数据采集示例程序，实现定时器采集、滤波、串口传输功能     |
| README.md  | 模块使用说明文档，包含硬件特性、软件使用、示例代码等内容            |

## 软件设计核心思想

核心类为 `ADS1115`，基于 MicroPython 实现 16 位高精度 ADC 采集的完整 API，设计核心如下：

### 1. 寄存器与配置抽象

通过类变量定义 ADS1115 的寄存器地址（转换寄存器、配置寄存器等）、配置位掩码（OS_MASK、MUX_MASK 等），以及增益、通道、采样率的映射关系，简化配置参数与寄存器值的转换。

### 2. 模块化方法设计

将功能拆分为独立的核心方法：

- 寄存器读写：`_write_register`/`_read_register` 实现底层 I2C 通信
- 数据转换：`raw_to_v` 将原始 ADC 值转换为实际电压值
- 采集控制：`set_conv` 配置采样率和通道，`read`/`read_rev` 实现单次/连续采集
- 中断处理：`_irq_handler` 配合 `alert_pin` 实现比较器中断回调

### 3. 易用性与扩展性

- 构造函数封装 I2C 接口、地址、增益等初始化参数，降低使用门槛
- 支持可选的警报引脚和回调函数，便于扩展中断触发逻辑
- 全局变量 + 定时器回调的示例设计，适配实时数据采集场景

## 使用说明

### 1. 硬件初始化

- 连接模块电源（VCC 接 3.3V/5V，GND 接地）
- 连接 I2C 引脚（SDA/SCL 对应主控设备的 I2C 引脚）
- 根据需求配置 J1/J2 短接点，设置唯一的 I2C 地址（0x48-0x4B）
- 连接模拟输入信号到 AIN0-AIN3 中的指定通道

### 2. 软件初始化

```python
from machine import Pin, I2C
from ads1115 import ADS1115

# 初始化I2C（SDA=4, SCL=5, 400KHz）
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
# 扫描I2C总线获取设备地址
ADC_ADDRESS = i2c.scan()[0]
# 初始化ADS1115（增益1x，±4.096V）
adc = ADS1115(i2c, ADC_ADDRESS, 1)
```

### 3. 数据采集

- 单次采集：配置采样率和通道后调用 `read` 方法
- 连续采集：使用 `read_rev` 读取当前值并启动下一次转换
- 中断采集：通过 `alert_start` 设置阈值，配合中断回调实现阈值触发采集

### 4. 数据处理

- 使用 `raw_to_v` 将原始 ADC 值转换为电压值
- 可选滑动均值滤波（`moving_average_filter`）降低噪声
- 通过 UART 将采集数据封装为固定帧格式发送至上位机

## 示例程序

以下是实现定时器触发的高精度 ADC 采集、滑动均值滤波和串口数据传输的完整示例（main.py）：

```python
from machine import Pin, I2C, Timer, UART
import time
from ads1115 import ADS1115
import struct

# 全局变量
ADC_ADDRESS = 0
POT_CHANNEL = 0  # 电位器连接AIN0
FILTER_SIZE = 20
filter_buffer = []
filter_sum = 0

# 定时器回调：定时采集ADC数据
def timer_callback(timer):
    global adc, POT_CHANNEL, FILTER_SIZE
    try:
        # 设置860 SPS采样率，采集AIN0通道
        adc.set_conv(rate=7, channel1=POT_CHANNEL)
        raw_adc = adc.read_rev()
        voltage = adc.raw_to_v(raw_adc)
        print(f"Channel AIN{POT_CHANNEL}: {voltage:.4f} V (Raw: {raw_adc})")
        
        # 滑动均值滤波
        average = moving_average_filter(raw_adc, FILTER_SIZE)
        # 串口发送数据帧
        send_data_frames(raw_adc, average)
    except Exception as e:
        print("Error in timer_callback:", e)

# 串口数据帧发送
def send_data_frames(raw_adc, average):
    global uart
    try:
        # 帧头0xAA 0xBB + 原始值 + 滤波值（小端模式）
        frame_header = struct.pack('<2B', 0xAA, 0xBB)
        frame_data = struct.pack('<2H', raw_adc & 0xFFFF, average & 0xFFFF)
        uart.write(frame_header + frame_data)
    except Exception as e:
        print("Error in send_data_frames:", e)

# 滑动均值滤波
def moving_average_filter(new_value, filter_size):
    global filter_buffer, filter_sum
    filter_buffer.append(new_value)
    filter_sum += new_value
    if len(filter_buffer) > filter_size:
        removed = filter_buffer.pop(0)
        filter_sum -= removed
    return filter_sum // len(filter_buffer)

# 初始化配置
time.sleep(3)
print("FreakStudio: Using ADS1115 acquire signal")

# 初始化UART（波特率256000）
uart = UART(0, 256000)
uart.init(baudrate=256000, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)

# 初始化I2C（SDA=4, SCL=5, 400KHz）
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
devices_list = i2c.scan()
print('i2c devices found:', len(devices_list))
for device in devices_list:
    print("ADC I2C address:", hex(device))
    ADC_ADDRESS = device

# 初始化ADS1115（增益1x，±4.096V）
adc = ADS1115(i2c, ADC_ADDRESS, 1)

# 初始化定时器（10ms周期，100Hz采集）
timer = Timer(-1)
timer.init(period=10, mode=Timer.PERIODIC, callback=timer_callback)

# 主循环
while True:
    time.sleep(1)
```

### 示例说明

1. I2C 初始化：扫描 I2C 总线获取 ADS1115 地址，初始化 I2C 通信
2. ADC 配置：设置增益为 1x（±4.096V），适配大多数传感器输出范围
3. 定时器采集：10ms 周期触发 ADC 采集，实现 100Hz 采样率，使用 read_rev 读取并启动下一次转换
4. 滑动均值滤波：20 点滑动均值滤波，平滑采集数据，减少噪声干扰
5. 串口传输：将原始 ADC 值和滤波后的值通过 UART 发送，帧头 0xAA 0xBB 标识数据帧，便于上位机解析

## 注意事项

1. I2C 地址设置：通过 J1、J2 短接点设置地址，仅可选择一个地址（0x48-0x4B），不可多选，避免地址冲突
2. 增益与电压范围：增益值决定 ADC 输入电压范围，2/3x 对应 ±6.144V，16x 对应 ±0.256V，需根据传感器输出范围选择合适增益
3. 采样率选择：采样率越高，转换速度越快，但噪声可能增大，需在速度和精度之间平衡（默认 128 SPS）
4. 通道配置：单端输入使用 channel1 指定通道（0-3），差分输入需同时指定 channel1 和 channel2（支持 0-1、0-3、1-3、2-3 组合）
5. 定时器频率：定时器周期需大于 ADC 转换时间（采样率越高，转换时间越短），避免数据丢失
6. 接线规范：I2C 总线需上拉电阻（模块已内置），ADC 输入线尽量短，避免电磁干扰；电源需稳定，避免电压波动影响精度

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