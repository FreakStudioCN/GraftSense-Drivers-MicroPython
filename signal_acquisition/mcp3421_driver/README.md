# mcp3421_driver

# mcp3421_driver

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

`mcp3421_driver` 是一个用于控制 **MCP3421 模数转换器（ADC）** 的 MicroPython 库，适用于各类支持 MicroPython 的开发板。该库提供了简洁的 API，方便开发者快速读取 MCP3421 的高精度模拟数据，可应用于传感器信号采集、工业数据采集等场景。

---

## 主要功能

- 支持 MCP3421 芯片的 I2C 通信控制
- 可配置采样分辨率（12/14/16/18 位）
- 支持单次转换和连续转换模式
- 提供便捷的电压读取接口
- 无特定芯片或固件依赖，兼容性强

---

## 硬件要求

- 支持 MicroPython 的开发板（如 ESP32、Raspberry Pi Pico 等）
- MCP3421 模数转换芯片
- 连接线路：I2C 总线（SDA、SCL）、电源（3.3V/5V）、地线

---

## 文件说明

## 软件设计核心思想

- **简洁易用**：封装底层 I2C 通信细节，提供直观的 API 调用方式
- **兼容性优先**：不依赖特定固件或芯片，适配主流 MicroPython 开发环境
- **模块化设计**：驱动逻辑与硬件操作解耦，便于维护和扩展
- **轻量高效**：代码精简，资源占用少，适合嵌入式环境

---

## 使用说明

1. 将 `code/mcp3421.py` 文件上传至开发板的文件系统
2. 在 MicroPython 代码中导入 `mcp3421` 模块
3. 初始化 I2C 总线，并创建 MCP3421 实例
4. 调用相关方法读取 ADC 数据

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:30
# @Author  : octaprog7
# @File    : main.py
# @Description : Raspberry Pi Pico使用MCP3421模数转换芯片进行电压测量，支持单次和自动连续测量模式

# ======================================== 导入相关模块 =========================================
import sys
import time
from machine import I2C, Pin
from mcp3421 import I2cAdapter
from mcp3421 import Mcp342X

# ======================================== 全局变量 ============================================
# SCL引脚编号
I2C_SCL_PIN = 5  
# SDA引脚编号
I2C_SDA_PIN = 4  
I2C_FREQ = 400_000  # I2C通信频率
TARGET_SENSOR_ADDR = 0x68  # MCP3421默认I2C地址（可根据硬件配置调整）
# 设置增益参数（0表示默认增益）
my_gain = 0
# 设置数据速率参数
my_data_rate = 1

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: MCP3421 ADC voltage measurement")

# 初始化I2C总线
i2c_bus = I2C(1, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print(f"I2C_FREQ={I2C_FREQ}")
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")
print(devices_list)
# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 创建I2C适配器实例
            adapter = I2cAdapter(i2c_bus)
            # 创建MCP342X ADC实例（初始化目标传感器）
            sensor = Mcp342X(adapter)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No Mcp3421 sensor found on I2C bus")

adc = sensor

# 打印单次测量模式提示
print("---Single measurement mode---")

# 启动单次测量模式，配置数据速率、增益、通道和差分模式
adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)

# ========================================  主程序  ============================================

# 打印传感器原始配置提示
print("---Basic raw sensor settings---")
# 获取传感器通用原始属性
gp = adc.get_general_raw_props()
# 打印通用原始属性
print(gp)
# 打印分隔线
print(16 * "--")
# 获取转换周期时间
td = adc.get_conversion_cycle_time()
# 打印转换周期时间（微秒）
print(f"Conversion time [us]: {td}")
# 打印当前分辨率（位数）
print(f"Bits per reading: {adc.current_resolution}")
# 打印PGA增益值
print(f"PGA: {adc.gain}")
# 打印分隔线
print(16 * "--")
# 循环进行33次单次测量
for _ in range(33):
    # 等待转换周期完成
    time.sleep_us(td)
    # 获取转换后的电压值（非原始值）
    val = adc.get_value(raw=False)
    # 打印测量得到的电压值
    print(f"Voltage: {val} Volts")
    # 再次启动单次测量，保持相同配置
    adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)

# 打印分隔线
print(16 * "--")
# 打印自动测量模式提示
print("Automatic ADC measurement mode")
# 打印分隔线
print(16 * "--")
# 启动自动连续测量模式，配置参数与单次模式一致
adc.start_measurement(single_shot=False, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)
# 获取转换周期时间
td = adc.get_conversion_cycle_time()
# 等待首次转换完成
time.sleep_us(td)
# 打印转换周期时间（微秒）
print(f"Conversion time [us]: {td}")
# 打印当前分辨率（位数）
print(f"Bits per reading: {adc.current_resolution}")
# 初始化循环计数器和最大值
_cnt, _max = 0, 333333
# 迭代获取自动测量的电压值
for voltage in adc:
    # 打印自动测量得到的电压值
    print(f"Voltage: {voltage} Volts")
    # 判断计数器是否超过最大值，超过则退出程序
    if _cnt > _max:
        sys.exit(0)
    # 等待转换周期完成
    time.sleep_us(td)
    # 计数器加1
    _cnt += 1

```

## 注意事项

- 请确保 I2C 总线引脚与开发板硬件定义一致
- MCP3421 的 I2C 地址可通过硬件引脚配置，需与代码中地址匹配
- 高分辨率模式下转换时间会延长，注意时序控制
- 电源噪声会影响采样精度，建议使用稳定电源并添加滤波电路

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议，完整协议内容如下：

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
