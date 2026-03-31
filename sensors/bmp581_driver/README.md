# BMP581 Driver for MicroPython

# BMP581 Driver for MicroPython

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

BMP581 Driver 是 **GraftSense-Drivers-MicroPython** 项目下的传感器驱动库，专为 MicroPython 环境设计，用于控制 BMP581 高精度数字气压传感器，可实现气压、温度数据的采集与处理，为环境监测、海拔计算等应用提供可靠的传感器数据支持。

## 主要功能

- 支持 BMP581 传感器的初始化与通信配置（I2C/SPI 接口）
- 提供气压、温度数据的读取与物理量转换功能
- 内置数据校验（CRC）机制，保障数据传输完整性
- 模块化设计，兼容多种 MicroPython 芯片与固件版本
- 统一的传感器接口规范，便于与其他传感器驱动集成

## 硬件要求

- **传感器模块**：BMP581 数字气压传感器
- **开发板**：支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- **通信接口**：I2C 或 SPI 接口（根据硬件连接方式选择）
- **供电**：3.3V 直流电源（需符合 BMP581 传感器额定电压要求）
- **连接线**：杜邦线若干，用于连接传感器与开发板的电源、通信引脚

## 文件说明

## 软件设计核心思想

1. **模块化解耦**：将传感器驱动、总线通信、数据处理、校验等功能拆分为独立模块，降低耦合度，提升代码可复用性与可维护性。
2. **接口统一化**：基于 `base_sensor.py` 定义抽象接口，所有传感器驱动遵循同一规范，便于在上层应用中无缝切换不同传感器。
3. **硬件无关性**：通过 `bus_service.py` 封装底层通信，使传感器驱动不依赖特定硬件平台，支持多种 MicroPython 芯片（`chips: all`）与固件（`fw: all`）。
4. **轻量高效**：适配 MicroPython 资源受限的环境，代码精简高效，避免不必要的性能开销。

## 使用说明

### 部署驱动文件

将以下文件上传至开发板的文件系统（可通过 `mpremote`、`ampy` 等工具完成）：

- `bmp581mod.py`
- `sensor_pack/` 目录下所有文件（`init.py`、`base_sensor.py`、`bus_service.py`、`converter.py`、`crc_mod.py`、`geosensmod.py`）

### 导入模块

在 MicroPython 脚本中导入驱动模块：

```python
from bmp581mod import BMP581
from sensor_pack.bus_service import I2CService  # 若使用 I2C 接口
# from sensor_pack.bus_service import SPIService  # 若使用 SPI 接口
```

### 初始化传感器

根据硬件连接方式初始化通信总线与传感器实例：

```python
# 示例：I2C 接口初始化
i2c = I2CService(0, scl=Pin(17), sda=Pin(16), freq=400000)  # 替换为实际引脚与频率
sensor = BMP581(i2c, address=0x47)  # 替换为实际 I2C 地址
```

## 示例程序

以下是完整的 MicroPython 示例代码，实现 BMP581 传感器的初始化与数据循环读取：

```python
from machine import Pin
from bmp581mod import BMP581
from sensor_pack.bus_service import I2CService
import time

# 初始化 I2C 总线（根据实际硬件修改引脚）
i2c = I2CService(0, scl=Pin(17), sda=Pin(16), freq=400000)

# 初始化 BMP581 传感器（I2C 地址默认 0x47，可根据硬件修改）
sensor = BMP581(i2c, address=0x47)

# 循环读取并打印数据
while True:
    sensor.start_measurement()
    temp = sensor.get_temperature()
    pressure = sensor.get_pressure()
    print(f"温度: {temp:.2f} ℃, 气压: {pressure:.2f} Pa")
    time.sleep(1)  # 1 秒读取一次
```

## 注意事项

1. **硬件连接**：确保传感器与开发板的通信引脚（SCL/SDA 或 SCK/MOSI/MISO/CS）连接正确，避免短路或接反。
2. **供电安全**：BMP581 传感器额定供电电压为 1.71V–3.6V，请勿超过 3.6V，否则可能损坏硬件。
3. **通信配置**：I2C/SPI 总线的频率、引脚号需与实际硬件一致，否则会导致通信失败。
4. **数据读取**：测量启动后需等待传感器完成转换（具体时间参考 BMP581 数据手册），避免读取未完成的无效数据。
5. **协议遵守**：本项目采用 MIT 协议，使用、修改与分发代码时需保留原版权声明与许可条款。

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
