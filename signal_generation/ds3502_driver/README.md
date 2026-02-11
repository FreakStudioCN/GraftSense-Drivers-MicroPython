# GraftSense-基于 DS3502 的数字电位器模块（MicroPython）

# GraftSense-基于 DS3502 的数字电位器模块（MicroPython）

# GraftSense 基于 DS3502 的数字电位器模块

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

本模块是 FreakStudio GraftSense 基于 DS3502 的数字电位器模块，通过 DS3502 芯片实现可编程电阻值调节与数字信号控制模拟量，采用 I2C 通信接口，具备高精度、操作方便、接口简便等核心优势，兼容 Grove 接口标准。适用于电子 DIY 电路调节实验、模拟信号控制演示等场景，为系统提供可靠的可编程电阻调节能力。

## 主要功能

### 硬件层面

1. 支持最高 400kHz 的 I2C 通信，可通过 A0/A1 配置地址（0x28–0x2B），兼容多设备共线挂载；
2. 7 位分辨率（0–127）可编程电阻调节，支持掉电保存/快速写入两种工作模式；
3. 兼容 Grove 接口标准，引脚定义清晰，集成电源稳压与滤波电路，供电稳定；
4. 具备电源指示灯、地址配置焊盘、拨码开关等辅助设计，便于调试与使用。

### 软件层面

1. 封装 DS3502 驱动类，提供电阻值读写、工作模式配置等核心接口；
2. 基于 DS3502 驱动实现波形发生器类，支持正弦波、方波、三角波的可编程生成；
3. 支持 ADC 采样验证波形输出，串口打印采样数据，便于结果校验。

## 硬件要求

### 核心接口要求

1. I2C 通信接口：需提供 SDA（数据）、SCL（时钟）引脚，支持 400kHz 时钟频率；
2. 供电要求：VCC 输入 5V，模块内置 AMS1117-3.3 稳压芯片转换为 3.3V 给 DS3502 供电；
3. 电位器端子连接：必须将 RL 与 RH 短接，V+ 需接入 4.5V~15.5V 电源（推荐 5V）；
4. 拨码开关：SW1 需全部闭合，确保电位器正常工作。

### 硬件配置要求

1. I2C 地址配置：通过 A0/A1 焊盘短接至 GND 或 VCC，配置地址为 0x28–0x2B 中的一个，避免地址冲突；
2. 外部电路：若 RH 电压高于 VCC，需将 V+ 与 RH 连接，保证 V+≥RH；
3. 信号频率：接入信号频率需 ≤400kHz，避免超出 I2C 通信能力。

## 文件说明

| 文件名                   | 功能说明                                                                   |
| ------------------------ | -------------------------------------------------------------------------- |
| ds3502.py                | 封装 DS3502 数字电位器核心驱动，包含初始化、电阻值读写、工作模式配置等方法 |
| dac_waveformgenerator.py | 基于 DS3502 类实现波形发生器，支持正弦波、方波、三角波生成与输出控制       |
| main.py                  | 完整示例程序，包含 I2C 初始化、设备扫描、波形生成与 ADC 采样验证等功能     |

## 软件设计核心思想

### 1. DS3502 驱动类设计

基于 MicroPython 封装，核心设计思想为**极简接口 + 模式适配**：

- 初始化时关联 I2C 总线与设备地址，确保通信链路唯一；
- 分离“掉电保存”（模式 0）和“快速写入”（模式 1）两种工作模式，适配不同使用场景；
- 封装电阻值读写接口，屏蔽底层 I2C 通信细节，对外仅暴露 0–127 的分辨率值，降低使用门槛。

### 2. WaveformGenerator 波形发生器类设计

核心设计思想为**参数化配置 + 定时器驱动**：

- 抽象波形生成通用参数（频率、幅度、偏移、波形类型），支持灵活配置；
- 预计算每个周期的采样点数据，通过定时器回调逐点输出，保证波形时序稳定；
- 关联 DS3502 实例，将数字波形参数转换为电阻值调节指令，实现模拟量输出。

## 使用说明

### 1. 硬件接线

- I2C 连接：将模块 SDA/SCL 引脚对应连接到主控板的 I2C 引脚（示例中为 Pin2/Pin3）；
- 供电连接：模块 VCC 接 5V，GND 接主控板 GND；
- 电位器端子：RL 与 RH 短接，V+ 接 5V 电源；
- 拨码开关：SW1 全部闭合，确认电源指示灯 LED1 常亮。

### 2. 软件初始化

1. 初始化 I2C 总线，设置频率为 400kHz；
2. 扫描 I2C 设备，确定 DS3502 的实际地址（0x28–0x2B）；
3. 实例化 DS3502 类，设置工作模式（推荐波形生成用模式 1）；
4. 初始化串口（用于打印数据）、ADC（用于采样验证）、定时器（用于定时采样）。

### 3. 波形生成

1. 实例化 WaveformGenerator 类，配置频率、幅度、偏移、波形类型等参数；
2. 调用 `start()` 方法启动波形输出，`stop()` 方法停止输出；
3. 观察串口打印的 ADC 采样数据，验证波形输出效果。

## 示例程序

```python
from machine import ADC, Timer, Pin, I2C, UART
import time
import micropython
from ds3502 import DS3502
from dac_waveformgenerator import WaveformGenerator

# 全局配置
DAC_ADDRESS = 0x00
adc_conversion_factor = 3.3 / 65535

def timer_callback(timer: Timer):
    """定时器回调，定时读取ADC数据"""
    global adc, adc_conversion_factor
    value = adc.read_u16() * adc_conversion_factor
    micropython.schedule(user_callback, value)

def user_callback(value: float):
    """用户回调，处理ADC数据并通过串口发送"""
    global uart
    formatted_value = "{:.2f}".format(value)
    uart.write(str(formatted_value) + '\r\n')

# 初始化配置
time.sleep(3)
print("FreakStudio : Using Digital Potentiometer chip DS3502 to generate differential waveform")

# 初始化I2C总线（SDA=Pin2, SCL=Pin3, 频率400kHz）
i2c = I2C(id=1, sda=Pin(2), scl=Pin(3), freq=400000)

# 扫描I2C设备，定位DS3502地址
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
    for device in devices_list:
        if 0x28 <= device <= 0x2B:
            print("I2C hexadecimal address: ", hex(device))
            DAC_ADDRESS = device

# 初始化DS3502，设置为快速模式（仅写入WR）
dac = DS3502(i2c, DAC_ADDRESS)
dac.set_mode(1)

# 初始化串口、ADC和定时器
uart = UART(0, 115200)
uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)
adc = ADC(2)
timer = Timer(-1)
timer.init(period=10, mode=Timer.PERIODIC, callback=timer_callback)

# 生成正弦波（5Hz，幅度1.5V，偏移1.5V）
print("FreakStudio : Generate Sine Waveform : 5Hz, 1.5V, 1.5V")
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='sine')
wave.start()
time.sleep(6)
wave.stop()

# 生成方波（5Hz，幅度1.5V，偏移1.5V）
print("FreakStudio : Generate Square Waveform : 5Hz, 1.5V, 1.5V")
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='square')
wave.start()
time.sleep(6)
wave.stop()

# 生成三角波（5Hz，幅度1.5V，偏移1.5V，上升沿比例0.8）
print("FreakStudio : Generate Triangle Waveform : 5Hz, 1.5V, 1.5V, 0.8")
wave = WaveformGenerator(dac, frequency=5, amplitude=1.5, offset=1.5, waveform='triangle', rise_ratio=0.8)
wave.start()
time.sleep(6)
wave.stop()

# 停止ADC采集
timer.deinit()
```

### 示例说明

1. I2C 初始化与设备扫描：通过 I2C 总线扫描定位 DS3502 地址，确保通信正常；
2. DS3502 模式设置：设置为快速模式（仅写入 WR），提升波形生成响应速度；
3. 波形生成：通过 WaveformGenerator 类生成正弦波、方波、三角波，通过 ADC 采集输出并串口打印验证；
4. 采样与验证：定时器定时读取 ADC 数据，验证波形输出的准确性与稳定性。

## 注意事项

1. I2C 地址配置：通过 A0/A1 焊盘短接至 GND 或 VCC 配置地址（0x28–0x2B），确保总线上无地址冲突；
2. 电位器端子连接：

   - 必须将 RL 与 RH 短接，并给 V+ 接入电源（如 +5V），否则电位器无法正常工作；
   - 若 RH 电压高于 VCC，需将 V+ 与 RH 连接，保持 V+≥RH；
   - V+ 电压范围为 +4.5V 到 15.5V；
3. 工作模式选择：

   - 模式 0（写入 WR 和 IVR）：掉电后参数保留，但写入后需延时 100ms；
   - 模式 1（仅写入 WR）：写入速度快，适合动态波形生成，但掉电后参数丢失；
4. 信号频率限制：接入信号频率需小于 400kHz，避免超出 DS3502 的 I2C 通信能力；
5. 波形生成参数：

   - 频率范围：0<frequency≤10Hz，超出范围会导致采样率不足；
   - 幅度 + 偏移需 ≤vref（参考电压），避免输出电压超出范围。

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

---
