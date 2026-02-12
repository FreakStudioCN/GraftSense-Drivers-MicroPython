# GraftSense-基于 DHT22 的温湿度传感器模块（MicroPython）

# GraftSense-基于 DHT22 的温湿度传感器模块（MicroPython）

# GraftSense 基于 DHT22 的温湿度传感器模块

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

本模块是 FreakStudio GraftSense 基于 DHT22 的温湿度传感器模块，通过 DHT22 芯片实现高精度环境温湿度测量，采用单总线通信协议，具备测量精度高、响应稳定、接口简便等核心优势，兼容 Grove 接口标准。相比 DHT11，DHT22 在精度和环境适应性上显著提升，适用于电子 DIY 气象监测实验、智能温控与环境感知演示、工业级场景数据采集等对精度要求更高的场景。

## 主要功能

1. 高精度温湿度测量：温度测量精度 ±0.5℃，湿度测量精度 ±2%RH，远超 DHT11 传感器；
2. 单总线通信：通过单根 DIO 引脚实现数据传输，无需额外时钟线，接口简洁；
3. 宽范围环境适配：工作温度范围-40~80℃，工作湿度范围 0~100%RH（无结露），适配工业与户外等严苛场景；
4. 稳定的数据输出：输出 40 位数字信号（含校验和），保障数据完整性；
5. 兼容 Grove 接口：支持快速插拔，适配主流主控板；
6. 状态可视化：集成电源指示灯，直观显示模块工作状态。

## 硬件要求

1. 供电电源：支持 3.3V/5V 双电平供电，需与主控 MCU 电源电平匹配；
2. 引脚连接：

   - VCC：接主控板电源引脚（3.3V/5V）；
   - GND：接主控板接地引脚；
   - DIO：接主控板 GPIO 引脚（单总线通信）；
   - NC：无需连接；
3. 外围电路依赖：模块内置 4.7kΩ 上拉电阻、100nF 滤波电容，需确保焊接正常；
4. 主控兼容性：支持具备 GPIO 引脚的主流 MCU（如 ESP32/ESP8266、树莓派 Pico 等），需适配 MicroPython 环境。

## 文件说明

| 文件名  | 功能说明                                                        |
| ------- | --------------------------------------------------------------- |
| main.py | 核心示例程序，实现 DHT22 温湿度的高精度采集、数据打印与异常处理 |

## 软件设计核心思想

1. 通信协议适配：基于 DHT22 单总线通信协议，利用 MicroPython 内置 `dht` 库封装底层通信逻辑，简化开发；
2. 时序保障：上电后增加延时（3 秒）等待模块稳定，采集间隔遵循 DHT22 要求（≥2 秒），避免数据失真；
3. 鲁棒性设计：通过 `try-except` 捕获通信异常（如总线干扰、模块未响应），防止程序崩溃；
4. 高精度数据提取：通过 `temperature()` 和 `humidity()` 方法直接获取带小数的温湿度值，保留高精度特性。

## 使用说明

1. 硬件接线：将模块的 VCC、GND 分别接主控板对应电源引脚，DIO 引脚接主控板指定 GPIO（示例中为 GPIO6，可按需调整）；
2. 环境准备：在主控板中烧录 MicroPython 固件，确保 `dht` 库可用；
3. 程序部署：将示例程序 `main.py` 上传至主控板；
4. 运行程序：执行 `main.py`，主控板将每隔 2 秒采集并打印温湿度数据；
5. 异常排查：若出现采集失败，检查引脚连接、模块供电及上拉电阻/滤波电容是否正常。

## 示例程序

以下是 `main.py` 中的核心代码，实现 DHT22 温湿度的高精度采集与打印：

```python
from machine import Pin
import time
import dht

# 初始化配置
time.sleep(3)  # 上电延时，等待模块稳定
print('FreakStudio : Using OneWire to read DHT22 sensor')

time.sleep(1)  # 等待DHT22传感器上电完成
# 数据引脚连接至GPIO6（可根据实际硬件调整）
d = dht.DHT22(Pin(6))

# 主循环：实时采集高精度温湿度
while True:
    try:
        d.measure()  # 触发一次温湿度采集
        temp = d.temperature()  # 获取温度值（℃）
        hum = d.humidity()      # 获取湿度值（%RH）
        print("Temperature: %.1f C  Humidity: %.1f %%" % (temp, hum))
    except Exception as e:
        print("Read error:", e)  # 捕获并打印采集异常
    time.sleep(2)  # 间隔2秒采集一次（DHT22推荐间隔）
```

### 示例说明

1. 引脚初始化：使用 GPIO6 作为单总线通信引脚，与模块 DIO 引脚直接连接；
2. 数据采集：循环调用 `measure()` 触发采集，通过 `temperature()` 和 `humidity()` 方法获取高精度温湿度数据；
3. 异常处理：捕获采集过程中的通信异常（如单总线干扰、模块故障），避免程序崩溃，提升系统稳定性。

## 注意事项

1. 测量间隔要求：DHT22 传感器两次测量间隔建议至少 2 秒（示例中通过 `time.sleep(2)` 实现），过短间隔会导致数据不稳定或采集失败；
2. 单总线接线规范：DIO 引脚需直接连接 MCU 的 GPIO 引脚，确保模块内置的 4.7kΩ 上拉电阻和 100nF 滤波电容正常焊接，避免通信干扰导致数据失真；
3. 电源兼容性：模块支持 3.3V/5V 双电源供电，需与主控 MCU 的电源电平严格匹配，避免电平不兼容损坏硬件；
4. 精度与环境适应性：

   - 温度测量精度：±0.5℃（远优于 DHT11 的 ±2℃）；
   - 湿度测量精度：±2%RH（远优于 DHT11 的 ±5%RH）；
   - 工作温度范围：-40~80℃（覆盖更严苛的工业与户外场景）；
   - 工作湿度范围：0~100%RH（无结露）；
5. 异常处理：调用 `measure()` 时需捕获 `Exception`，常见异常包括单总线通信干扰、模块未响应等，及时处理可提升系统可靠性。

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