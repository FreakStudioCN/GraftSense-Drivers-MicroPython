# GraftSense-基于 NE555 的模拟电容式土壤湿度传感器模块（MicroPython）

# GraftSense-基于 NE555 的模拟电容式土壤湿度传感器模块（MicroPython）

# GraftSense 基于 NE555 的电容式土壤湿度传感器模块 MicroPython 驱动

---

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

---

## 简介

本项目是 **基于 NE555 的模拟电容式土壤湿度传感器模块** 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块。模块以 NE555 芯片为核心，利用 PCB 印刷电容作为湿度敏感元件，通过土壤湿度变化改变等效电容，进而调整 NE555 充放电周期，输出与湿度对应的模拟电压信号，经 MCU 的 ADC 外设采集后，可实现土壤湿度的相对检测，适用于电子 DIY 植物监测、智能灌溉演示、环境感知等场景。

---

## 主要功能

- **原始 ADC 读取**：直接获取传感器输出的模拟电压对应的 16 位 ADC 原始值（0~65535，适配 RP2040 平台）
- **干湿校准**：支持在干燥空气和水中校准参考值，或手动导入校准参数，适配不同环境
- **相对湿度计算**：基于校准值将原始 ADC 值转换为 0~100% 的相对湿度百分比
- **湿度等级判断**：自动划分湿度等级（dry < 30%、moist 30%~70%、wet ≥ 70%），便于快速判断土壤状态
- **校准状态查询**：通过属性快速判断是否完成干湿校准
- **属性访问**：提供 `raw`、`moisture`、`level` 属性，简化数据获取方式

---

## 硬件要求

- **GraftSense NE555-Based Capacitive Soil Moisture Sensor v1.0**（遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如树莓派 Pico RP2040、ESP32 等，需具备 ADC 外设）
- 引脚连接：

  - 模块 AIN → MCU ADC 引脚（如树莓派 Pico 的 GP26，对应 ADC0）
  - VCC → 5V 电源（模块核心 NE555 需 5V 供电）
  - GND → MCU GND（共地确保电压参考一致）
- 模块核心：以 NE555 为核心，PCB 印刷电容作为湿度敏感元件，内置电源滤波电容和信号调理电路，输出模拟电压信号

---

## 文件说明

| 文件名             | 功能描述                                                             |
| ------------------ | -------------------------------------------------------------------- |
| `soil_moisture.py` | 驱动核心文件，定义 `SoilMoistureSensor` 类，提供所有湿度检测与校准 API |
| `main.py`          | 测试与演示文件，包含完整的校准流程和循环读取湿度数据的示例           |

---

## 软件设计核心思想

1. **硬件抽象层**：封装底层 ADC 操作，上层调用无需关心 MCU 的 ADC 配置细节，仅需指定引脚即可初始化
2. **校准适配机制**：自动处理干湿参考值的大小差异（无论干燥值大于还是小于湿润值，均可正确计算湿度百分比）
3. **数据分层输出**：提供原始值、百分比、等级三种数据形式，满足不同场景的使用需求
4. **易用性优化**：通过属性（`raw`/`moisture`/`level`）简化数据获取，无需重复调用方法

---

## 使用说明

### 1. 驱动初始化

```python
from soil_moisture import SoilMoistureSensor

# 初始化传感器：AIN接ADC引脚26（树莓派Pico的ADC0）
sensor = SoilMoistureSensor(pin=26)
```

### 2. 核心操作流程

| 步骤 | 操作     | 说明                                                                                                        |
| ---- | -------- | ----------------------------------------------------------------------------------------------------------- |
| 1    | 干燥校准 | 将传感器置于干燥空气中，调用 `sensor.calibrate_dry()` 保存干燥参考值                                          |
| 2    | 湿润校准 | 将传感器浸入水中，调用 `sensor.calibrate_wet()` 保存湿润参考值                                                |
| 3    | 数据读取 | 调用 `sensor.read_raw()` 获取原始值，`sensor.read_moisture()` 获取湿度百分比，`sensor.get_level()` 获取湿度等级 |
| 4    | 校准导入 | 若已保存校准值，可通过 `sensor.set_calibration(dry, wet)` 手动设置，避免重复校准                              |

---

## 示例程序

### 完整校准与读取流程（来自 `main.py`）

```python
import time
from soil_moisture import SoilMoistureSensor

# 上电延时
time.sleep(3)
print("FreakStudio: SoilMoistureSensor Test Start")
print("Please prepare the sensor for calibration (dry and wet)...")

# 初始化传感器 (ADC引脚26)
sensor = SoilMoistureSensor(pin=26)
print("Sensor initialized on ADC pin 26")

# Step 1: 校准干燥值
input("Place sensor in DRY air/soil and press Enter...")
dry_value = sensor.calibrate_dry()
print("Calibrated dry value:", dry_value)

# Step 2: 校准湿润值
input("Place sensor in WATER (fully wet) and press Enter...")
wet_value = sensor.calibrate_wet()
print("Calibrated wet value:", wet_value)

# Step 3: 设置校准值
sensor.set_calibration(dry_value, wet_value)
print("Calibration set: dry={}, wet={}".format(dry_value, wet_value))

# 循环读取传感器数据
print("\nCalibration completed. Start reading moisture...\n")

try:
    while True:
        raw = sensor.read_raw()
        moisture_percent = sensor.read_moisture()
        level = sensor.get_level()

        print(
            "Raw ADC: {:>5} | Moisture: {:>5.1f}% | Level: {}".format(
                raw, moisture_percent, level
            )
        )
        time.sleep(2)

except KeyboardInterrupt:
    print("\nTest stopped by user.")

print("SoilMoistureSensor Test Completed")
```

---

## 注意事项

1. **校准必要性**：首次使用或更换使用环境（如不同土壤类型、温度）时，必须重新进行干湿校准，否则湿度百分比计算会出现偏差
2. **数据相对性**：`read_moisture()` 返回的是相对湿度百分比，并非土壤绝对含水量，仅用于判断湿度趋势和等级
3. **硬件限制**：模块 AIN 引脚必须连接至 MCU 的 ADC 外设，不可直接连接普通 GPIO 引脚；模块供电需稳定 5V，避免电压波动影响 NE555 工作
4. **传感器保护**：避免传感器长时间浸泡在水中或接触腐蚀性液体，防止 PCB 电容和电路损坏；清洁时用干布擦拭，不可水洗
5. **校准环境**：干燥校准需在无水分的空气或干燥土壤中进行，湿润校准需将传感器完全浸入清水中，确保充分接触

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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