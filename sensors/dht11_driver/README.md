# GraftSense-基于 DHT11 的温湿度传感器模块（MicroPython）

# GraftSense-基于 DHT11 的温湿度传感器模块（MicroPython）

# GraftSense 基于 DHT11 的温湿度传感器模块

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

本模块是 FreakStudio GraftSense 基于 DHT11 的温湿度传感器模块，通过 DHT11 芯片实现环境温度与湿度的精准测量，采用单总线通信协议，具备成本低、易用性高、接口简单等优势，兼容 Grove 接口标准。适用于电子 DIY 气象实验、智能温控与环境监测演示、物联网数据采集等场景，为系统提供可靠的温湿度环境感知能力。

## 主要功能

1. 环境温湿度采集：基于 DHT11 芯片实现温度（-40~85℃）、湿度（20~90%RH）的数字量测量，输出 40 位数字信号保障数据完整性；
2. 单总线通信：通过单 DIO 引脚完成与主控的串行通信，无需额外时钟线，接口简洁易集成；
3. 数据校验：内置校验和机制，可验证采集数据的完整性，避免因通信干扰导致的错误数据；
4. 硬件兼容性：支持 3.3V/5V 双电压供电，兼容 Grove 接口标准，可快速与各类主控板对接；
5. 异常处理：提供自定义异常类，可捕获数据校验失败、脉冲数异常等通信问题，提升程序鲁棒性。

## 硬件要求

### 核心接口

- 单总线通信接口（DIO）：

  - 采用单总线协议，通过 DIO 引脚与主控建立串行通信，无需额外时钟线
  - 内置 4.7kΩ 上拉电阻，保障 DIO 引脚空闲时为高电平；100nF 滤波电容抑制信号干扰，提升通信稳定性
- 电源与引脚：

  - VCC：模块供电（支持 3.3V/5V）
  - GND：接地
  - NC：未连接引脚
  - DIO：单总线数据引脚（与 MCU 的 GPIO 引脚直接连接）
- 电源指示灯：LED1 常亮表示模块供电正常

### 电路设计

- 传感器核心电路：DHT11 芯片负责温湿度采集，通过单总线输出 40 位数字信号（湿度整数、湿度小数、温度整数、温度小数、校验和）
- MCU 接口电路：提供 DIO、VCC、GND 引脚，兼容 Grove 接口标准，便于与主控板快速连接
- 滤波与保护电路：C2/C3 滤波电容抑制电源噪声，提升测量稳定性；R2 限流电阻保护电源指示灯

### 模块布局

- 正面：DHT11 温湿度探头、DIO 单总线接口、电源接口（GND/VCC）、电源指示灯（LED1），接口清晰标注，便于接线调试

## 文件说明

| 文件名    | 功能说明                                                                      |
| --------- | ----------------------------------------------------------------------------- |
| dht11.py  | 核心驱动文件，包含 DHT11 类及自定义异常类，实现单总线通信、数据采集与校验逻辑 |
| main.py   | 示例程序文件，演示 DHT11 传感器的初始化、温湿度实时采集与数据打印功能         |
| README.md | 模块使用说明文档，包含简介、功能、硬件要求、使用方法等核心信息                |

## 软件设计核心思想

核心类：DHT11

基于 MicroPython 实现，提供完整的温湿度采集与数据校验 API，核心设计思想如下：

### 1. 异常处理设计

通过自定义异常类精准捕获通信过程中的异常场景，避免程序无提示崩溃：

| 异常类            | 触发场景                                                    |
| ----------------- | ----------------------------------------------------------- |
| InvalidChecksum   | 数据校验和验证失败（40 位数据的校验和与接收的校验和不匹配） |
| InvalidPulseCount | 捕获的脉冲数量不符合预期（预期 84 个脉冲，实际捕获数异常）  |

### 2. 核心方法与属性设计

围绕单总线通信时序和数据解析逻辑，封装易用的 API：

| 方法/属性           | 功能                             | 参数说明                       | 返回值                                           |
| ------------------- | -------------------------------- | ------------------------------ | ------------------------------------------------ |
| **init**(pin: int)  | 初始化 DHT11 传感器              | pin: 连接 DIO 引脚的 GPIO 对象 | 无                                               |
| measure()           | 触发一次温湿度采集，更新内部数据 | 无                             | 无（内部更新_temperature 和_humidity）           |
| temperature（属性） | 获取当前温度值（℃）             | 无                             | float，温度值（-40~85℃，DHT11 实际精度 ±2℃）  |
| humidity（属性）    | 获取当前湿度值（%RH）            | 无                             | float，湿度值（20~90%RH，DHT11 实际精度 ±5%RH） |

### 3. 通信协议实现

严格遵循 DHT11 单总线时序规则，保障数据可靠传输：

- 初始化：主机拉低 DIO 引脚 18ms，发送初始化信号；
- 数据传输：DHT11 响应后发送 84 个高低电平脉冲（前 4 个为应答脉冲，后 80 个为 40 位数据位）；
- 数据解析：高电平持续时间 >50µs 表示数据位 1，<50µs 表示数据位 0；
- 校验规则：校验和 = 湿度整数 + 湿度小数 + 温度整数 + 温度小数（取低 8 位），验证数据完整性。

## 使用说明

1. 硬件接线：将模块 VCC 接 3.3V/5V、GND 接主控地、DIO 接主控任意 GPIO 引脚（建议 GPIO6）；
2. 环境准备：确保主控板已烧录 MicroPython 固件，将 dht11.py 文件上传至主控板；
3. 初始化：创建 DHT11 实例时指定 DIO 对应的 GPIO 引脚，上电后延时 3 秒等待模块稳定；
4. 数据采集：调用 measure()方法触发采集，通过 temperature 和 humidity 属性获取温湿度值；
5. 异常处理：采集过程中需捕获 InvalidChecksum、InvalidPulseCount 等异常，避免程序终止。

## 示例程序

以下是 main.py 中的核心示例代码，实现 DHT11 温湿度的实时采集与打印：

```python
from machine import Pin
import time
from dht11 import DHT11

# 初始化配置
time.sleep(3)  # 上电延时，等待模块稳定
print('FreakStudio : Using OneWire to read DHT11 sensor')

time.sleep(1)  # 等待DHT11传感器上电完成
DHT11_PIN = Pin(6, Pin.OUT, Pin.PULL_UP)  # 初始化单总线通信引脚（GPIO6）
dht11 = DHT11(DHT11_PIN)  # 创建DHT11实例

# 主循环：实时采集温湿度
while True:
    try:
        dht11.measure()  # 触发一次温湿度采集
        temperature = dht11.temperature  # 获取温度值
        humidity = dht11.humidity        # 获取湿度值
        print("temperature: {}℃, humidity: {}%".format(temperature, humidity))
        time.sleep(2)  # 间隔2秒采集一次
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
```

### 示例说明

1. 引脚初始化：使用 GPIO6 作为单总线通信引脚，配置为上拉输出模式；
2. 数据采集：循环调用 measure()触发采集，通过 temperature 和 humidity 属性获取最新温湿度；
3. 异常处理：捕获采集过程中的异常（如校验失败、脉冲数错误），避免程序崩溃。

## 注意事项

1. 测量间隔限制：两次测量间隔至少 200ms（驱动内部已通过 MIN_INTERVAL_US 限制），否则数据可能不准确；
2. 单总线接线规范：DIO 引脚需直接连接 MCU 的 GPIO 引脚，确保上拉电阻（4.7kΩ）和滤波电容（100nF）正常焊接，避免通信干扰；
3. 电源兼容性：模块支持 3.3V/5V 供电，需与 MCU 电源电平匹配，避免电平不兼容损坏硬件；
4. 数据精度说明：DHT11 的温度精度为 ±2℃，湿度精度为 ±5%RH，适用于对精度要求不高的场景；若需更高精度，可考虑升级为 DHT22；
5. 异常处理：调用 measure()时需捕获 InvalidChecksum 和 InvalidPulseCount 异常，常见于通信干扰或模块故障；
6. 环境适应性：DHT11 的工作温度范围为 0~50℃，湿度范围为 20~90%RH，超出范围可能导致测量异常。

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