# MMA7660 Driver for MicroPython

# MMA7660 Driver for MicroPython

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

这是 **MMA7660 三轴加速度传感器** 的 MicroPython 驱动库，隶属于 `GraftSense-Drivers-MicroPython` 生态，旨在为 MicroPython 开发者提供简洁、高效的接口，以实现对 MMA7660 传感器的控制与加速度数据采集。

## 主要功能

- 支持 MMA7660 传感器的 I2C 通信初始化
- 读取 X、Y、Z 三轴加速度数据
- 可配置传感器采样率、工作模式（测量 / 待机）
- 支持低功耗模式配置，适配资源受限嵌入式设备
- 跨芯片兼容，支持所有可运行标准 MicroPython 的硬件平台

## 硬件要求

- **传感器**：MMA7660 三轴加速度传感器
- **开发板**：支持 MicroPython 且带有 I2C 接口的开发板（如 ESP32、ESP8266、RP2040、STM32 等）
- **连接方式**：通过 I2C 总线连接（SDA、SCL 引脚需对应开发板的 I2C 引脚）
- **供电**：MMA7660 推荐供电电压为 2.5V - 3.3V，请勿超过 3.3V

## 文件说明

## 软件设计核心思想

- **简洁易用**：封装底层 I2C 寄存器操作，对外提供直观的 Pythonic API，降低开发者使用门槛
- **跨平台兼容**：通过抽象硬件接口，无特定芯片或固件依赖，支持所有标准 MicroPython 环境
- **轻量高效**：代码体积小，运行时资源占用低，适配嵌入式设备的性能限制
- **可扩展性**：模块化设计，便于后续新增中断配置、姿态检测等扩展功能

## 使用说明

1. **部署驱动文件**：将 `code/mma7660.py` 拷贝到 MicroPython 开发板的文件系统中
2. **导入依赖模块**：在你的业务脚本中导入 `machine`（I2C/Pin）、`time` 及 `mma7660` 模块
3. **初始化 I2C 总线**：根据开发板硬件配置，初始化对应的 I2C 实例
4. **初始化传感器**：传入 I2C 实例，创建 MMA7660 传感器对象
5. **配置与采集**：按需配置传感器参数，调用接口读取三轴加速度数据

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午5:30
# @Author  : Developer
# @File    : main.py
# @Description : 基于Raspberry Pi Pico的MMA7660三轴加速度传感器数据读取程序，实现I2C通信、设备扫描、传感器初始化和加速度数据循环读取

# ======================================== 导入相关模块 =========================================

# 导入I2C和Pin模块，用于硬件I2C通信
from machine import I2C, Pin

# 导入sleep模块，用于程序延时
from time import sleep

# 导入MMA7660加速度传感器驱动类
from mma7660 import Accelerometer

# ======================================== 全局变量 ============================================

# 定义I2C通信的SCL引脚编号（对应Raspberry Pi Pico的GP5）
I2C_SCL_PIN = 5
# 定义I2C通信的SDA引脚编号（对应Raspberry Pi Pico的GP4）
I2C_SDA_PIN = 4
# 定义I2C通信频率（400kHz为Pico常用频率）
I2C_FREQ = 400000
# 定义MMA7660加速度传感器的目标I2C地址
TARGET_SENSOR_ADDR = 0x4C

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动后延时3秒，确保硬件稳定
sleep(3)
# 打印程序启动提示信息
print("FreakStudio: MMA7660 accelerometer data reading program started")

# 初始化I2C总线0，配置SCL、SDA引脚和通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C总线上的所有设备，返回设备地址列表并添加类型注解
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描启动提示
print("START I2C SCANNER")

# 检查I2C设备扫描结果，若未扫描到任何设备则退出程序
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的I2C设备数量
    print("i2c devices found:", len(devices_list))

# 初始化传感器变量为None，用于后续接收传感器实例
accel = None
# 遍历扫描到的I2C设备地址列表，查找目标传感器地址
for device in devices_list:
    # 判断当前设备地址是否为MMA7660的目标地址
    if device == TARGET_SENSOR_ADDR:
        # 打印找到的目标传感器十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化MMA7660加速度传感器
            accel = Accelerometer(i2c=i2c_bus)
            # 打印传感器初始化成功提示
            print("Target sensor initialization successful")
            # 找到并初始化成功后退出循环
            break
        except Exception as e:
            # 打印传感器初始化失败的异常信息
            print(f"Sensor Initialization failed: {e}")
            # 继续遍历下一个设备地址
            continue
else:
    # 遍历完所有地址未找到目标传感器，抛出异常
    raise Exception("No MMA7660 Accelerometer found on I2C bus")

# ========================================  主程序  ============================================

# 无限循环读取加速度传感器数据
while True:
    # 读取X/Y/Z轴的加速度值（单位：g）
    x_g, y_g, z_g = accel.getXYZ()
    # 读取X/Y/Z轴的加速度值（单位：m/s²）
    x, y, z = accel.getAcceleration()

    # 打印加速度值（单位：g），保留两位小数
    print(f"Acceleration(g): X={x_g:.2f}, Y={y_g:.2f}, Z={z_g:.2f}")
    # 打印加速度值（单位：m/s²），保留两位小数
    print(f"Acceleration(m/s²): X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
    # 打印分隔线，提升输出可读性
    print("-" * 30)
    # 延时0.5秒后继续读取数据
    sleep(0.5)

```

## 注意事项

- **I2C 地址**：MMA7660 默认 I2C 地址为 `0x4C`，若硬件修改地址需在初始化时传入正确地址
- **供电安全**：严禁超过 3.3V 供电，否则可能导致传感器永久损坏
- **功耗优化**：高采样率会增加功耗，低功耗场景建议降低采样率或切换至待机模式
- **引脚连接**：确保 SDA/SCL 引脚连接正确，部分开发板需额外配置 I2C 上拉电阻
- **固件依赖**：本驱动无特定固件依赖，支持所有标准 MicroPython 固件版本

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
