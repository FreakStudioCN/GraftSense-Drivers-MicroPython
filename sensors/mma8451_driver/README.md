# mma8451_driver - MicroPython MMA8451 三轴加速度传感器驱动

# mma8451_driver - MicroPython MMA8451 三轴加速度传感器驱动

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

本项目是 **MMA8451 三轴加速度传感器** 的 MicroPython 驱动库，为 MicroPython 开发板提供简洁、高效的传感器控制接口，帮助开发者快速接入 MMA8451 并获取三轴加速度数据。

## 主要功能

- 支持 I2C 通信方式初始化 MMA8451 传感器
- 可配置传感器量程（2g/4g/8g），适配不同场景需求
- 提供便捷的三轴加速度数据读取接口
- 封装 I2C 通信辅助函数，简化底层寄存器操作
- 兼容所有 MicroPython 芯片及固件，跨平台移植性强

## 硬件要求

- **传感器**：MMA8451 三轴加速度传感器模块
- **开发板**：支持 MicroPython 的开发板（如 ESP32、PyBoard、RP2040 等）
- **连接方式**：I2C 接口（需连接 SDA、SCL 引脚）
- **供电**：3.3V 直流供电（请确认传感器供电电压要求）

## 文件说明

项目核心文件如下：

- `micropython_mma8451/init.py`：模块入口文件，导出驱动核心类与工具函数
- `micropython_mma8451/i2c_helpers.py`：I2C 通信辅助库，封装通用 I2C 读写寄存器操作
- `micropython_mma8451/mma8451.py`：MMA8451 驱动核心实现，包含传感器初始化、量程配置、数据读取等逻辑
- `package.json`：包管理配置文件，记录库版本、依赖及文件映射信息
- `LICENSE`：MIT 许可协议文件

## 软件设计核心思想

1. **解耦设计**：将 I2C 底层通信与传感器业务逻辑分离，通过 `i2c_helpers.py` 复用通用 I2C 操作，提升代码可维护性
2. **简洁 API**：对外隐藏寄存器级操作细节，提供直观的 Python 接口，降低开发者使用门槛
3. **高兼容性**：配置中 `chips` 和 `fw` 均设为 `all`，支持所有 MicroPython 芯片及固件版本
4. **模块化扩展**：清晰的文件结构便于后续添加新功能或适配其他传感器型号

## 使用说明

1. **文件部署**：将 `micropython_mma8451` 文件夹复制到 MicroPython 开发板的文件系统中
2. **模块导入**：在你的脚本中导入驱动模块：

```python
from micropython_mma8451 import MMA8451
from machine import I2C, Pin
```

1. **初始化 I2C**：根据开发板引脚定义初始化 I2C 总线
2. **传感器初始化**：创建 MMA8451 实例并配置量程、I2C 地址
3. **数据读取**：调用实例方法获取三轴加速度数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : MMA8451加速度传感器示例程序

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from micropython_mma8451 import mma8451

# ======================================== 全局变量 ============================================

# I2C总线编号，RP2040上I2C0对应GPIO4(SDA)/GPIO5(SCL)
I2C_BUS_ID = 0
# I2C时钟线引脚
I2C_SCL_PIN = 5
# I2C数据线引脚
I2C_SDA_PIN = 4
# I2C通信频率，设置为400kHz
I2C_FREQ = 400000
# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x1C,0x1D]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 系统启动延时，确保外设稳定
time.sleep(3)
print("FreakStudio: MMA8451 sensor initialization")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
mma = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            mma = mma8451.MMA8451(i2c=i2c_bus, address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 设置传感器数据输出速率为800Hz
mma.data_rate = mma8451.DATARATE_800HZ

# ========================================  主程序  ============================================

# 无限循环，依次切换数据速率并读取加速度值
while True:
    for data_rate in mma8451.data_rate_values:
        print("Current Data rate setting: ", mma.data_rate)
        # 每个速率下连续读取10次
        for _ in range(10):
            accx, accy, accz = mma.acceleration
            print(f"Acceleration: X={accx:0.1f}m/s^2 y={accy:0.1f}m/s^2 z={accz:0.1f}m/s^2")
            print()
            time.sleep(0.5)
        # 切换到下一个数据速率
        mma.data_rate = data_rate
```

_注：需根据实际开发板引脚修改 I2C 初始化参数，__time__ 模块需提前导入_

## 注意事项

- **I2C 地址**：MMA8451 支持 `0x1C` 和 `0x1D` 两个地址，需根据硬件接线确认并传入初始化参数
- **量程选择**：量程可选 2g/4g/8g，量程越大精度越低，需根据应用场景合理配置
- **数据单位**：读取的加速度数据单位为 `g`（1g ≈ 9.8 m/s²）
- **供电稳定**：确保传感器供电稳定，避免电压波动导致数据异常
- **固件兼容**：本驱动无特定固件依赖，支持所有 MicroPython 固件版本

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源许可协议，完整内容如下：

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
