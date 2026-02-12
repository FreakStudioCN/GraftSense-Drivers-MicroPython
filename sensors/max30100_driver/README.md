# GraftSense-基于 MAX30100 的心率血氧传感器模块(开放版)

# GraftSense-基于 MAX30100 的心率血氧传感器模块(开放版)

# GraftSense MAX30100 Pulse Oximeter and Heart-Rate Sensor Module

目录

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

本项目是 **GraftSense 系列基于 MAX30100 的血氧心率传感器模块**，属于 FreakStudio 开源硬件项目。模块通过 MAX30100 芯片实现红光与红外光检测，支持心率信号采集与血氧饱和度（SpO2）计算，适用于健康监测教学实验、生理信号采集演示、可穿戴创客项目等场景，为生理参数的数字化采集提供了便捷的硬件连接方案。

---

## 主要功能

- **血氧与心率检测**：通过红光与红外光检测，支持心率信号采集与血氧饱和度（SpO2）计算。
- **标准 I2C 通信**：支持标准 I2C 通信速率，默认从机地址为 `0x57`，兼容 3.3V 系统电平，适配主流微控制器。
- **双模式切换**：支持心率模式（MODE_HR）与血氧模式（MODE_SPO2），可根据需求灵活切换。
- **参数可配置**：支持采样率、LED 电流、脉冲宽度等参数配置，适配不同场景下的采集需求。
- **Grove 接口兼容**：遵循 Grove 接口标准，便于快速集成到各类开发平台。

---

## 硬件要求

- **核心芯片**：MAX30100 脉搏血氧仪与心率传感器芯片，内置 DC-DC 5V 转 3.3V 电路、3.3V 转 1.8V 电平转换电路、电源滤波模块与电源指示灯。
- **通信接口**：I2C 接口（SDA、SCL），默认从机地址 `0x57`，兼容 3.3V 系统电平。
- **使用规范**：

  - 需将传感器贴合皮肤（推荐手指腹、耳垂等部位），避免缝隙/毛发遮挡光学窗口；不要用指甲盖覆盖传感器（指甲不透明，会阻断光透射），佩戴时尽量保持贴合处皮肤平整。
  - 避免强光（阳光、强灯光）直射传感器（环境光会干扰光学信号）；测量时保持静止，运动/抖动会导致光强数据波动，使心率/血氧计算失真。
  - 该模块为消费级精度，不能作为医疗诊断依据；保持传感器光学窗口清洁（污渍/指纹会遮挡光线），长期使用后可轻轻擦拭。

---

## 文件说明

- `max30100.py`：MAX30100 传感器驱动文件，封装了传感器初始化、模式设置、数据读取、寄存器操作等核心功能。
- `main.py`：驱动测试与示例程序，演示了传感器初始化、红光/红外数据读取及血氧饱和度计算的完整流程。

---

## 软件设计核心思想

- **分层架构**：将驱动层（硬件通信与寄存器操作）与应用层（数据计算与展示）分离，提升代码可维护性与可扩展性。
- **双模式适配**：支持心率模式（MODE_HR）与血氧模式（MODE_SPO2），通过寄存器配置实现模式切换，适配不同采集需求。
- **数据缓存机制**：通过本地缓冲区存储最新的红光与红外数据，便于后续心率与血氧计算，避免数据丢失。
- **错误处理机制**：内置 I2C 设备扫描与传感器 ID 校验，确保硬件连接正常，避免非法操作导致的模块异常。

---

## 使用说明

1. **硬件连接**：

   - 将模块的 I2C 接口（SDA、SCL）连接至微控制器的对应引脚（示例中 SDA=GP4，SCL=GP5）。
   - 为模块提供 3.3V 或 5V 供电，确保电源稳定。
2. **初始化配置**：

   ```python
   ```

from machine import I2C, Pin
import max30100
import time

# 初始化 I2C（SDA=GP4，SCL=GP5）

i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# 扫描 I2C 设备，确认 MAX30100 连接

devices_list = i2c.scan()
if 0x57 not in devices_list:
raise Exception("No MAX30100 found on I2C bus")

# 初始化传感器并启用血氧模式

sensor = max30100.MAX30100(i2c=i2c)
sensor.enable_spo2()

```

3. **数据读取与计算**：
	```python
while True:
    # 读取传感器数据
    sensor.read_sensor()
    # 获取红光与红外数据
    red = sensor.red
    ir = sensor.ir
    # 计算血氧饱和度（示例公式，可根据需求优化）
    if ir:
        spo2 = 100 - 25 * (red / ir)
        print(f"SpO2: {spo2:.2f}% | Red: {red} | IR: {ir}")
    time.sleep_ms(200)
```

---

## 示例程序

```python
# MicroPython v1.27.0
from machine import I2C, Pin
import max30100
import time

# 上电延时
time.sleep(3)
print("FreakStudio: MAX30100 Pulse Oximeter Test")

# 初始化 I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4))

# 扫描 I2C 设备
devices_list = i2c.scan()
print(f"I2C devices found: {[hex(d) for d in devices_list]}")
if 0x57 not in devices_list:
    raise Exception("MAX30100 not detected!")

# 初始化传感器
sensor = max30100.MAX30100(i2c=i2c)
sensor.enable_spo2()

# 打印传感器信息
print(f"Part ID: {sensor.get_part_id()}, Revision ID: {sensor.get_rev_id()}")

# 主循环读取数据
while True:
    sensor.read_sensor()
    red = sensor.red
    ir = sensor.ir
    if ir:
        spo2 = 100 - 25 * (red / ir)
        print(f"SpO2: {spo2:.2f}% | Red: {red} | IR: {ir}")
    time.sleep_ms(200)
```

---

## 注意事项

1. **使用规范**：

   - 测量时需将传感器紧密贴合皮肤（如手指腹），避免光线泄漏；保持静止，避免强光直射。
   - 模块为消费级精度，**不可用于医疗诊断**，仅适用于教学实验与创客项目。
2. **硬件保护**：

   - 避免在模块工作时频繁插拔电源，防止芯片损坏。
   - 定期清洁传感器光学窗口，避免污渍/指纹遮挡光线影响检测精度。
3. **数据优化**：

   - 示例中的血氧计算公式为简化版本，实际应用中可根据 MAX30100 芯片手册优化算法，提升计算精度。

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
