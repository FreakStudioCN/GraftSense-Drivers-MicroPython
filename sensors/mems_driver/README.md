# GraftSense-基于 MEMS 气体传感器的空气质量监测模块(MicroPython)

# GraftSense-基于 MEMS 气体传感器的空气质量监测模块(MicroPython)

# GraftSense MEMS Gas Sensor-based Air Quality Monitoring Module

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

本项目是 **GraftSense 系列基于 MEMS 气体传感器的空气质量监测模块**，属于 FreakStudio 开源硬件项目。模块通过 PCA9546A I2C 扩展芯片挂载 4 路 MEMS 气体传感器（烟雾、一氧化碳、VOC、甲醛），配合 ADS1115 高精度 ADC 实现模拟量采集，支持将传感器电压转换为气体浓度（ppm），广泛适用于电子 DIY 环境监测实验、室内空气质量演示等场景。

---

## 主要功能

- **多传感器集成**：支持 4 路 MEMS 气体传感器（烟雾传感器 JED115、一氧化碳传感器 JED104、VOC 传感器 JED101、甲醛传感器 JED116），覆盖常见有害气体检测。
- **I2C 扩展设计**：通过 PCA9546A 芯片扩展 I2C 总线，避免多传感器地址冲突，支持灵活扩展。
- **高精度 ADC 采集**：基于 ADS1115 16 位 ADC，提供稳定的模拟电压采集，支持多通道切换与采样率配置。
- **多项式校准**：内置多项式校准逻辑，支持自定义或使用内置多项式，将传感器电压线性转换为气体浓度（ppm）。
- **灵活数据读取**：支持单次/多次采样取平均，可直接获取原始电压或浓度值，适配不同应用需求。
- **Grove 接口兼容**：遵循 Grove 接口标准，连接便捷，适配主流 MCU 开发平台。

---

## 硬件要求

- **核心芯片**：PCA9546A（I2C 扩展）、ADS1115（16 位 ADC）、4 路 MEMS 气体传感器（烟雾、CO、VOC、甲醛）。
- **供电**：3.3V 或 5V 直流供电，模块内置 DC-DC 转换电路，适配不同平台供电需求。
- **通信接口**：I2C 总线（SDA、SCL 引脚），遵循 Grove 接口定义，支持 400kHz 高速模式。
- **传感器通道**：4 路模拟输出通道，分别对应 4 种气体传感器，通过 ADS1115 通道切换采集。

---

## 文件说明

- `ads1115.py`：ADS1115 ADC 驱动文件，封装了 ADC 初始化、通道切换、原始值读取、电压转换等核心功能，为 MEMS 传感器提供底层采集支持。
- `mems_air_quality.py`：MEMS 空气质量传感器驱动文件，基于 ADS1115 实现传感器选择、电压读取、多项式校准、浓度计算等功能，提供统一的高层接口。
- `main.py`：驱动测试与示例程序，演示了 I2C 总线初始化、设备扫描、传感器配置、电压与浓度读取的完整流程。

---

## 软件设计核心思想

- **分层架构**：将底层 ADC 采集（ADS1115）与上层传感器逻辑（MEMS 驱动）分离，降低耦合度，提升代码复用性与可维护性。
- **多项式校准抽象**：通过内置/自定义多项式实现电压到浓度的线性转换，适配不同传感器的特性曲线，提升检测精度。
- **通道抽象化**：通过类常量（`CH20`/`SMK`/`VOC`/`CO`）封装传感器通道，简化通道选择逻辑，避免直接使用数字索引导致的错误。
- **采样优化**：支持多次采样取平均，通过延时控制采样间隔，有效降低噪声干扰，提升数据稳定性。
- **参数校验**：对输入参数（如传感器类型、多项式系数长度）进行严格校验，避免无效操作导致的程序异常。

---

## 使用说明

1. **硬件连接**：

   - 将模块通过 Grove 接口连接至 MCU 的 I2C 总线（SDA、SCL 引脚），接入 3.3V/5V 供电。
   - 确保 4 路 MEMS 传感器已正确焊接至模块对应通道。
2. **初始化配置**：

   ```python
   ```

from machine import Pin, I2C
from ads1115 import ADS1115
from mems_air_quality import MEMSAirQuality

# 初始化 I2C 总线（SDA=4, SCL=5, 400kHz）

i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描 I2C 设备获取 ADS1115 地址

devices = i2c.scan()
adc_addr = devices[0] if devices else None

if adc_addr:
# 初始化 ADS1115（增益=1）
adc = ADS1115(i2c, adc_addr, 1)
# 初始化 MEMS 空气质量模块（采样率=7）
mems = MEMSAirQuality(adc, adc_rate=7)

```

3. **传感器校准配置**：
	```python
# 查看 VOC 传感器的多项式系数
mems.get_polynomial(MEMSAirQuality.VOC)
# 设置 VOC 传感器自定义多项式（3 个系数）
mems.set_custom_polynomial(MEMSAirQuality.VOC, [20, 100, 20])
# 恢复 VOC 传感器内置多项式
mems.select_builtin(MEMSAirQuality.VOC)
```

4. **数据读取**：
   ```python
   ```

# 读取 VOC 传感器电压（V）

voltage = mems.read_voltage(MEMSAirQuality.VOC)

# 读取 VOC 传感器浓度（ppm），3 次采样取平均

ppm = mems.read_ppm(MEMSAirQuality.VOC, samples=3, delay_ms=10)

```

---

## 示例程序

```python
# MicroPython v1.23.0
from machine import Pin, I2C
import time
from ads1115 import ADS1115
from mems_air_quality import MEMSAirQuality

# 上电延时
time.sleep(3)
print("FreakStudio: MEMS Air Quality Sensor Test Program")

# 初始化 I2C 总线
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])
adc_addr = devices[0] if devices else None

if not adc_addr:
    print("No ADS1115 found!")
    exit()

# 初始化 ADC 与 MEMS 模块
adc = ADS1115(i2c, adc_addr, 1)
mems = MEMSAirQuality(adc, adc_rate=7)

# 配置 VOC 传感器多项式
mems.select_builtin(MEMSAirQuality.VOC)
print("VOC polynomial:", mems.get_polynomial(MEMSAirQuality.VOC))

# 循环读取数据
while True:
    voltage = mems.read_voltage(MEMSAirQuality.VOC)
    ppm = mems.read_ppm(MEMSAirQuality.VOC, samples=3, delay_ms=10)
    print(f"VOC Voltage: {voltage:.3f}V, Concentration: {ppm:.2f} ppm")
    time.sleep(1)
```

---

## 注意事项

1. **I2C 地址冲突**：使用 PCA9546A 扩展 I2C 时，需确保各传感器地址不冲突，模块已通过硬件设计规避该问题。
2. **采样率选择**：`adc_rate` 取值范围为 0-7，对应不同采样速度，值越大采样速度越快，噪声也会相应增加，需根据场景平衡选择。
3. **多项式校准**：自定义多项式需包含 3 个浮点数系数，若系数格式错误将导致浓度计算异常，建议先使用内置多项式验证。
4. **传感器兼容性**：模块仅适配指定型号 MEMS 传感器（JED115/JED104/JED101/JED116），更换其他传感器需重新校准多项式。
5. **供电稳定性**：模块内置 DC-DC 转换电路，需确保供电电压稳定，避免电压波动导致 ADC 采集精度下降。

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