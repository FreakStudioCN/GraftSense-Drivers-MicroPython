# GraftSense-基于 MLX90614 的非接触式红外测温模块（MicroPython）

# GraftSense-基于 MLX90614 的非接触式红外测温模块（MicroPython）

# 基于 MLX90614 的非接触式红外温度模块 MicroPython 驱动

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

本项目是基于 MLX90614（含 MLX90615）的非接触式红外温度模块的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 I2C 通信接口读取环境温度与物体温度（支持双温区型号），经寄存器数据解析转换为摄氏温度，适用于非接触测温实验、智能设备温度监测、环境温感检测等场景。

---

## 主要功能

- I2C 通信适配：支持 MicroPython I2C 接口，兼容 100kHz 通信速率
- 单/双温区兼容：MLX90614 自动检测双温区配置，MLX90615 仅支持单温区
- 多维度温度读取：支持环境温度、物体温度 1、物体温度 2（双温区专属）读取
- 原始数据访问：可读取寄存器 16 位原始值，支持自定义数据处理流程
- 属性简化调用：通过 `ambient`/`object`/`object2` 属性直接获取温度值
- 批量数据读取：`read()` 方法一次性返回所有温度数据（字典格式）
- 地址范围兼容：支持 MLX90614/90615 的 I2C 地址范围（0x5A-0x5D）
- 参数校验与异常处理：初始化时校验 I2C 实例与地址合法性，提升程序稳定性

---

## 硬件要求

- MLX90614 非接触式红外温度模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040、STM32 等）
- 引脚连接：

  - 模块 VCC → MCU 3.3V/5V 电源引脚
  - 模块 GND → MCU GND 引脚
  - 模块 SDA → MCU I2C SDA 引脚（如 ESP32 的 GPIO4）
  - 模块 SCL → MCU I2C SCL 引脚（如 ESP32 的 GPIO5）
- 模块硬件特性：

  - 内置 DC-DC 5V 转 3.3V 电路，兼容 3.3V/5V 系统供电
  - 配备电源指示灯，直观显示模块供电状态
  - I2C 接口支持 5V 电平耐受，可直接接入 5V I2C 网络
  - 模块 I2C 地址范围：0x5A-0x5D（需通过 I2C 扫描获取实际地址）

---

## 文件说明

| 文件名      | 说明                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------ |
| mlx90614.py | 核心驱动文件，包含 `SensorBase` 基类、`MLX90614`/`MLX90615` 子类，实现 I2C 通信、温度读取与数据解析 |
| main.py     | 测试示例程序，实现 I2C 地址扫描、传感器初始化、实时温度数据读取与多功能测试                      |

---

## 软件设计核心思想

1. 基类封装通用逻辑：`SensorBase` 类封装寄存器读取（`_read16`）、温度转换（`_read_temp`）等通用功能，子类继承后复用代码
2. 型号差异化适配：`MLX90614` 类自动检测双温区配置，`MLX90615` 类固定单温区，实现不同型号的统一接口
3. 属性化数据访问：通过 `@property` 装饰器将温度读取方法封装为属性，简化用户调用（如 `sensor.ambient`）
4. 批量数据读取：`read()` 方法一次性返回所有温度数据字典，提升数据获取效率
5. 严格参数校验：初始化时校验 I2C 实例与地址合法性，避免非法参数导致的运行错误
6. 兼容性设计：支持 MLX90614/90615 的地址范围，适配不同硬件版本的地址差异

---

## 使用说明

1. 硬件连接

- 模块 VCC → MCU 3.3V/5V 引脚
- 模块 GND → MCU GND 引脚
- 模块 SDA → MCU I2C SDA 引脚（如 ESP32 GPIO4）
- 模块 SCL → MCU I2C SCL 引脚（如 ESP32 GPIO5）

1. 驱动初始化

```python
from machine import I2C, Pin
from mlx90614 import MLX90614

# 初始化I2C（以ESP32 I2C0为例）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)

# 扫描I2C地址，获取模块实际地址
devices = i2c.scan()
mlx_addr = next(addr for addr in devices if 0x5A <= addr <= 0x5D)

# 初始化MLX90614传感器
sensor = MLX90614(i2c, mlx_addr)
```

1. 基础操作示例

```python
# 读取环境温度
ambient_temp = sensor.read_ambient()
print(f"环境温度: {ambient_temp:.2f}℃")

# 读取物体温度1
object_temp1 = sensor.read_object()
print(f"物体温度1: {object_temp1:.2f}℃")

# 双温区型号读取物体温度2
if sensor.dual_zone:
    object_temp2 = sensor.read_object2()
    print(f"物体温度2: {object_temp2:.2f}℃")

# 通过属性访问温度
print(f"环境温度（属性）: {sensor.ambient:.2f}℃")
print(f"物体温度（属性）: {sensor.object:.2f}℃")

# 一次性读取所有数据
all_data = sensor.read()
print("所有温度数据:", all_data)
```

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/27 上午11:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : mlx90614双温区温度传感器测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from mlx90614 import MLX90614, MLX90615

# ======================================== 全局变量 =============================================

mlx61xaddr=None

# ======================================== 功能函数 =============================================

def test_sensor_realtime(sensor, name="Sensor", interval=1.0):
    """
    实时显示传感器温度数据，覆盖所有功能测试。
    """
    print("\n=== Realtime testing {} ===".format(name))
    print("Dual zone:", sensor.dual_zone)
    print("Press Ctrl+C to stop")

    try:
        while True:
            # ================= 内部方法测试 =================
            try:
                raw_ambient = sensor._read16(sensor._REGISTER_TA)
                raw_object = sensor._read16(sensor._REGISTER_TOBJ1)
                temp_ambient_internal = sensor._read_temp(sensor._REGISTER_TA)
                temp_object_internal = sensor._read_temp(sensor._REGISTER_TOBJ1)
            except Exception as e:
                print("[Internal] Error:", e)
                raw_ambient = raw_object = temp_ambient_internal = temp_object_internal = None

            # ================= 公共方法测试 =================
            ambient = sensor.read_ambient()
            obj = sensor.read_object()
            obj2 = sensor.read_object2() if sensor.dual_zone else None

            # ================= 属性访问测试 =================
            ambient_prop = sensor.ambient
            obj_prop = sensor.object
            obj2_prop = sensor.object2 if sensor.dual_zone else None

            # ================= 一次性读取功能测试 =================
            try:
                all_data = sensor.read()
            except Exception as e:
                all_data = None

            # ================= 数据输出 =================
            print("\n[{}] Data Snapshot".format(name))
            print("Raw ambient (internal):", raw_ambient)
            print("Raw object (internal):", raw_object)
            if temp_ambient_internal is not None:
                print("Temp ambient via _read_temp: {:.2f} °C".format(temp_ambient_internal))
            if temp_object_internal is not None:
                print("Temp object via _read_temp: {:.2f} °C".format(temp_object_internal))
            print("Ambient: {:.2f} °C".format(ambient))
            print("Object: {:.2f} °C".format(obj))
            if sensor.dual_zone:
                print("Object2: {:.2f} °C".format(obj2))
            print("Property ambient: {:.2f} °C".format(ambient_prop))
            print("Property object: {:.2f} °C".format(obj_prop))
            if sensor.dual_zone:
                print("Property object2: {:.2f} °C".format(obj2_prop))
            print("Read all:", all_data)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nRealtime testing stopped")

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MLX90614 test start ")

i2c = I2C(0, scl=5, sda=4, freq=100000)
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x5A <= device <= 0x5D:
        print("I2c hexadecimal address:", hex(device))
        mlx61xaddr = device

# 初始化传感器
sensor14 = MLX90614(i2c, mlx61xaddr)
print("[MLX90614] Sensor initialized.")
sensor15 = MLX90615(i2c, mlx61xaddr)
print("[MLX90615] Sensor initialized.")

# ======================================== 主程序 ==============================================

print("\n--- Starting MLX90614 Realtime Test ---")
test_sensor_realtime(sensor14, "MLX90614", interval=1.0)

print("\n--- Starting MLX90615 Realtime Test ---")
test_sensor_realtime(sensor15, "MLX90615", interval=1.0)
```

---

## 注意事项

1. I2C 引脚限制：必须连接到 MCU 支持 I2C 功能的 SDA/SCL 引脚，不可接入普通数字 GPIO
2. 地址确认：模块 I2C 地址在 0x5A-0x5D 范围内，建议先通过 I2C 扫描获取实际地址
3. 双温区限制：仅部分 MLX90614 型号支持双温区，MLX90615 无此功能，调用 `read_object2()` 会抛出异常
4. 测量条件：红外测温受距离、角度影响，建议测量距离 ≤5cm，探头正对被测物体表面
5. 异常处理：I2C 通信可能出现异常，建议在数据读取逻辑中添加 `try-except` 捕获异常
6. 电源兼容：模块支持 3.3V/5V 供电，无需额外电平转换，直接接入对应电压的 MCU 电源

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