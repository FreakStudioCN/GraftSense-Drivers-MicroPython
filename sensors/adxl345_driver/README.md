# ADXL345 Driver for MicroPython

# ADXL345 Driver for MicroPython

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

这是一个适用于 **MicroPython** 的 **ADXL345 三轴数字加速度传感器驱动库**，由 FreakStudio 开发维护。库提供了简洁易用的 API，帮助开发者快速在 MicroPython 环境中初始化 ADXL345、配置测量参数并读取三轴加速度数据，适用于物联网、可穿戴设备、姿态检测等场景。

## 主要功能

- 支持 I2C 通信方式初始化 ADXL345 传感器
- 可配置测量范围（±2g/±4g/±8g/±16g）
- 支持读取三轴（X/Y/Z）原始加速度数据及转换后的重力加速度值
- 提供电源管理功能（测量模式 / 待机模式切换）
- 兼容多种 MicroPython 芯片与固件，无特定硬件 / 固件依赖

## 硬件要求

- **ADXL345 三轴加速度传感器模块**
- 支持 I2C 通信的 MicroPython 开发板（如 ESP32、ESP8266、RP2040、STM32 等）
- 连接线（杜邦线）若干，用于连接传感器与开发板
- 电源：3.3V（注意 ADXL345 不支持 5V 直接供电）

## 典型接线（I2C 模式）

## 文件说明

## 软件设计核心思想

- **模块化封装**：将传感器的初始化、数据读取、参数配置等操作封装为独立方法，降低代码耦合
- **易用性优先**：提供简洁的 API 接口，隐藏底层寄存器操作细节，便于快速上手
- **高兼容性**：设计时无特定芯片 / 固件依赖，支持绝大多数 MicroPython 开发板与通用固件
- **可扩展性**：预留接口，便于后续添加 SPI 通信、中断检测等扩展功能

## 使用说明

1. **下载驱动文件**：将 `code/adxl345.py` 文件上传至 MicroPython 开发板的文件系统中
2. **导入驱动库**：在你的项目代码中导入 `adxl345` 模块
3. **初始化通信总线**：创建 I2C 对象，指定 SDA/SCL 引脚
4. **初始化传感器**：实例化 `ADXL345` 类，传入 I2C 对象与传感器地址（默认 0x53）
5. **配置传感器**：设置测量范围、电源模式等参数
6. **读取数据**：调用相关方法获取三轴加速度数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 下午2:30
# @Author  : fanday
# @File    : main.py
# @Description : ADXL345三轴加速度传感器测试 初始化I2C扫描 读取XYZ轴加速度数据
# ======================================== 导入相关模块 =========================================

# 从machine模块导入Pin类，用于控制GPIO引脚
from machine import Pin

# 从machine模块导入I2C类，用于I2C通信
from machine import I2C

# 导入时间模块，用于延时操作
import time

# 导入ustruct模块，用于解析二进制数据
import ustruct

# 从adxl345模块导入adxl345类，这是ADXL345传感器的驱动类
from adxl345 import adxl345

# ======================================== 全局变量 ============================================

# I2C总线编号（使用0号总线）
I2C_BUS_NUM = 0
# ADXL345的SCL引脚连接到GP5
I2C_SCL_PIN = 5
# ADXL345的SDA引脚连接到GP4
I2C_SDA_PIN = 4
# I2C通信频率设置为400KHz
I2C_FREQ = 400000
# ADXL345支持的I2C地址列表（默认地址0x53，若SDO引脚拉高则为0x1D）
TARGET_SENSOR_ADDRS = [0x53, 0x1D]
# 初始化传感器对象为None，后续扫描成功后再赋值
snsr = None
# 创建ADXL345片选引脚对象，设置为输出模式（I2C模式下片选引脚需设为输出）
cs = Pin(22, Pin.OUT)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，等待系统稳定
time.sleep(3)
# 输出初始化开始提示（纯英文短句）
print("FreakStudio: Starting I2C scanner for ADXL345")
# 初始化I2C总线，用于扫描设备（传感器初始化时仍使用原始参数格式）
i2c_bus = I2C(I2C_BUS_NUM, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 扫描I2C总线上的所有设备地址，返回地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印扫描开始提示
print("START I2C SCANNER")
# 检查是否扫描到任何设备
if len(devices_list) == 0:
    # 未发现设备时打印提示
    print("No i2c device !")
    # 抛出异常并退出程序
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 输出发现的设备数量
    print("i2c devices found:", len(devices_list))
    # 初始化目标地址变量
    target_addr = None
    # 遍历扫描到的所有设备地址
    for device in devices_list:
        # 如果当前地址属于目标传感器地址列表
        if device in TARGET_SENSOR_ADDRS:
            # 记录目标地址
            target_addr = device
            # 以十六进制格式打印目标地址
            print("I2c hexadecimal address:", hex(device))
            try:
                # 按照adxl345类要求传递参数：总线编号、SCL引脚、SDA引脚、片选引脚
                snsr = adxl345(bus=I2C_BUS_NUM, scl=I2C_SCL_PIN, sda=I2C_SDA_PIN, cs=cs)
                # 传感器初始化成功提示
                print("Target sensor initialization successful")
                # 跳出循环
                break
            except Exception as e:
                # 初始化失败时打印异常信息
                print(f"Sensor Initialization failed: {e}")
                # 继续尝试下一个地址
                continue
    # 如果传感器对象仍然为None（未成功初始化）
    if snsr is None:
        # 抛出明确异常，提示检查接线或地址
        raise Exception("No ADXL345 found, please check wiring or address (0x53/0x1D)!")

# ========================================  主程序  ============================================

# 无限循环读取传感器数据
while True:
    # 读取三轴加速度数据，返回值单位是mg
    x, y, z = snsr.readXYZ()
    # 打印X、Y、Z轴数据（单位：mg）
    print("x:", x, "y:", y, "z:", z, "unit:mg")
    # 延时0.5秒
    time.sleep(0.5)

```

## 注意事项

- **接线检查**：确保 VCC 接 3.3V，切勿直接接 5V，否则可能损坏传感器
- **I2C 地址确认**：ADXL345 的 I2C 地址由 ALT ADDRESS 引脚电平决定：接地为 0x53，接高为 0x1D，初始化时需传入正确地址
- **电源管理**：无需数据采集时可调用 `sensor.standby()` 进入待机模式以降低功耗
- **数据精度**：测量范围越大，数据分辨率越低，需根据实际场景选择合适范围
- **固件兼容**：本库无特定固件依赖，支持所有标准 MicroPython 固件

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
