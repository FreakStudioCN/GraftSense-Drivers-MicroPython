# GraftSense-基于 BA111 的水质 TDS 传感器模块（开放版）

# GraftSense-基于 BA111 的水质 TDS 传感器模块（开放版）

# GraftSense BA111-based TDS Sensor Module

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

本项目是 **GraftSense 系列基于 BA111 的水质 TDS 传感器模块**，属于 FreakStudio 开源硬件项目。模块通过 BA111 芯片实现水中溶解性固体（TDS）浓度检测与温度补偿，支持基线校准与 NTC 参数配置，适用于净水机、智能水杯等需要实时监测水质的场景。

---

## 主要功能

- **TDS 与温度检测**：实时测量水中溶解性固体浓度（ppm）与水温（℃），支持温度补偿以提升检测精度。
- **基线校准**：支持在 25℃±5℃ 纯净水中进行基线校准，确保长期检测基准准确。
- **NTC 参数配置**：可自定义 NTC 常温电阻与 B 值，适配不同温度传感器特性。
- **UART 通信**：通过串口接口实现指令控制与数据回传，支持查询 TDS/温度、校准、参数设置等操作。
- **Grove 接口兼容**：遵循 Grove 接口标准，便于快速集成到各类开发平台。

---

## 硬件要求

- **核心芯片**：BA111 TDS 检测芯片、NTC 温度传感器，内置 DC-DC 5V 转 3.3V 电路与电源滤波模块。
- **探头连接**：

  - 探头接口：XH2.54-4P 接口，黑、红两线对应 TDS 检测电极，白、黄两线对应 NTC 温度传感器。
  - 探头干扰：若同时使用两个 TDS 探头检测同一水体，探头间距需保持在 1 米以上，避免电极间信号干扰。
- **供电**：3.3V 或 5V 直流供电，模块内置电源滤波与指示灯电路。
- **通信接口**：UART 接口（MRX、MTX），MCU 的 RX 对应模块 TX，TX 对应模块 RX，实现双向数据传输。

---

## 文件说明

- `ba111_tds.py`：BA111 TDS 传感器驱动文件，封装了 TDS/温度检测、基线校准、NTC 参数配置等核心功能。
- `main.py`：驱动测试与示例程序，演示了传感器初始化、基线校准、数据读取的完整流程。

---

## 软件设计核心思想

- **帧结构标准化**：采用固定帧格式（命令(1B) + 参数(4B) + CRC(1B)），通过 CRC 校验保障通信可靠性。
- **参数可配置性**：支持自定义 NTC 常温电阻与 B 值，适配不同温度传感器特性，提升检测精度。
- **状态化校准**：通过基线校准消除环境与探头老化影响，确保长期检测基准准确。
- **错误处理机制**：内置错误码映射表，便于快速定位通信、校准、检测等环节的异常。

---

## 使用说明

1. **硬件连接**：

   - 将 TDS 电极探头插入模块的 XH2.54-4P 探头接口，黑、红两线对应 TDS 检测电极，白、黄两线对应 NTC 温度传感器。
   - 将模块通过 Grove 接口连接至 MCU 的 UART 总线（MRX、MTX 引脚），接入 3.3V/5V 供电。
2. **基线校准**：

   - 首次使用或长期放置后，需执行基线校准。校准前将探头置于 25℃±5℃ 的纯净水中，确保检测基准准确。
3. **初始化配置**：

   ```python
   ```

from machine import UART, Pin
from ba111_tds import BA111TDS

# 初始化 UART（波特率 9600）

uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 初始化 BA111 TDS 传感器

sensor = BA111TDS(uart)

# 配置 NTC 参数（可选）

sensor.set_ntc_resistance(10000)
sensor.set_ntc_b_value(3950)

```

4. **数据读取**：
	```python
# 执行 TDS 与温度检测
tds, temp = sensor.detect()
print(f"TDS: {tds}ppm, Temperature: {temp}℃")
```

---

## 示例程序

```python
# MicroPython v1.26.1
from ba111_tds import BA111TDS
import time
from machine import Pin, UART

time.sleep(3)
print("FreakStudio: BA111 TDS Sensor Test")

# 初始化 UART
uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
sensor = BA111TDS(uart)

# 配置 NTC 参数
sensor.set_ntc_resistance(10000)
sensor.set_ntc_b_value(3950)

# 基线校准
input("Place the probe into pure water at 25°C±5°C, then press any key to calibrate...")
if sensor.calibrate():
    print("Calibration successful!")
    # 循环读取数据
    while True:
        result = sensor.detect()
        if result:
            tds, temp = result
            print(f"TDS: {tds:.2f} ppm | Temperature: {temp:.2f} ℃")
        time.sleep(1)
else:
    print("Calibration failed!")
```

---

## 注意事项

1. **基线校准规范**：首次使用或长期放置后必须执行基线校准，校准前需将探头置于 25℃±5℃ 的纯净水中，避免校准基准偏移。
2. **探头干扰抑制**：同时使用两个 TDS 探头检测同一水体时，探头间距需保持在 1 米以上，避免电极间信号干扰。
3. **环境影响修正**：探头浸入水中的深度、容器形状会对检测结果产生线性影响，可根据已知校准点的检测值自行修正系数。
4. **维护建议**：长期使用后需定期检查探头电极表面是否结垢，及时清洁以维持检测精度；插拔探头时确保插头插紧，避免接触不良导致数据异常。
5. **通信参数匹配**：UART 通信需确保波特率（9600）、数据位（8）、停止位（1）等参数与模块配置一致，避免通信失败。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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